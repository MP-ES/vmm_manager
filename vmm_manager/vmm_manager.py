"""
Script que gerencia um inventário de máquinas no SCVMM, com base
em um arquivo YAML.
"""
import re
import string
import os
import argparse
from distutils.util import strtobool
import configargparse
from ruamel.yaml import YAML, scanner
from vmm_manager.infra.servidor_acesso import ServidorAcesso
from vmm_manager.infra.comando import Comando
from vmm_manager.parser.parser_local import ParserLocal
from vmm_manager.parser.parser_remoto import ParserRemoto
from vmm_manager.entidade.plano_execucao import PlanoExecucao
from vmm_manager.util.config import CAMPO_AGRUPAMENTO, CAMPO_ID, CAMPO_IMAGEM, CAMPO_REGIAO
from vmm_manager.util.msgs import finalizar_com_erro, imprimir_acao_corrente
from vmm_manager.util.operacao import validar_retorno_operacao_com_lock
from vmm_manager.util.operacao import validar_retorno_operacao_sem_lock
from vmm_manager.util.operacao import adquirir_lock, liberar_lock, confirmar_acao_usuario_com_lock


def parametro_arquivo_yaml(nome_arquivo):
    try:
        with open(nome_arquivo, 'r') as stream:
            yaml = YAML()
            yaml.load(stream)
            return nome_arquivo
    except FileNotFoundError as exc:
        raise argparse.ArgumentTypeError(exc)
    except scanner.ScannerError as exc:
        raise argparse.ArgumentTypeError(
            'YAML inválido: {}'.format(exc))


def parametro_booleano(valor):
    try:
        return strtobool(valor)
    except ValueError:
        raise argparse.ArgumentTypeError(
            "'{}' não é um valor booleano".format(valor))


def get_parser():
    parser = configargparse.ArgumentParser(
        description='Gerenciador de inventário SCVMM', default_config_files=['vmm_manager.ini'])
    parser.add('-a', '--servidor-acesso',
               help='Servidor que executará os scripts PowerShell. Ex: localhost',
               env_var='VMM_SERVIDOR_ACESSO', required=True, type=str)
    parser.add('-u', '--usuario',
               help='Usuário com permissões no servidor de acesso e no VMM',
               env_var='VMM_USUARIO', required=True, type=str)
    parser.add('-p', '--senha',
               help='Senha do usuário',
               env_var='VMM_SENHA', required=True, type=str)
    parser.add('-s', '--servidor',
               help='Servidor VMM. Ex: localhost',
               env_var='VMM_SERVIDOR', required=True, type=str)

    subprasers = parser.add_subparsers(dest='comando')
    plan = subprasers.add_parser(
        'plan', help='Cria um plano de execução, \
            com ações necessárias à sincronização do inventário')
    plan.add_argument('--inventario',
                      help='Arquivo YAML com a especificação das máquinas',
                      dest='arquivo_inventario', env_var='VMM_INVENTARIO',
                      required=True, type=parametro_arquivo_yaml)

    apply = subprasers.add_parser(
        'apply', help='Aplica as alterações necessárias no VMM')
    apply.add_argument('--plano-execucao',
                       help='Arquivo YAML com o plano de execução',
                       dest='arquivo_plano_execucao', env_var='VMM_PLANO_EXECUCAO',
                       required=False, type=parametro_arquivo_yaml)
    apply.add_argument('--pular-confirmacao',
                       help='Se for True, o plano de execução é aplicado sem confirmação',
                       dest='pular_confirmacao', env_var='VMM_PULAR_CONFIRMACAO',
                       required=False, type=parametro_booleano)
    apply.add_argument('--inventario',
                       help='Arquivo YAML com a especificação das máquinas',
                       dest='arquivo_inventario', env_var='VMM_INVENTARIO',
                       required=False, type=parametro_arquivo_yaml)

    destroy = subprasers.add_parser(
        'destroy', help='Remove todas as máquinas do agrupamento informado')
    destroy.add_argument(
        '--agrupamento', help='Agrupamento a ser excluído', required=True)
    destroy.add_argument(
        '--nuvem', help='Nuvem a ser analisada', required=True)
    destroy.add_argument('--pular-confirmacao',
                         help='Se for True, o agrupamento é excluído sem confirmação',
                         dest='pular_confirmacao', env_var='VMM_PULAR_CONFIRMACAO',
                         required=False, type=parametro_booleano)

    subprasers.add_parser(
        'opts', help='Lista as opções disponíveis no VMM para cada parâmetro da VM')

    return parser


def obter_inventario_remoto(servidor_acesso, agrupamento, nuvem):
    imprimir_acao_corrente('Obtendo inventário remoto')

    parser_remoto = ParserRemoto(agrupamento, nuvem)
    status, inventario_remoto = parser_remoto.get_inventario(servidor_acesso)
    validar_retorno_operacao_com_lock(status, inventario_remoto,
                                      servidor_acesso, agrupamento, nuvem)

    return inventario_remoto


def obter_inventario_local(servidor_acesso, arquivo_inventario):
    imprimir_acao_corrente('Obtendo inventário local')

    parser_local = ParserLocal(arquivo_inventario)
    status, inventario_local = parser_local.get_inventario(servidor_acesso)
    validar_retorno_operacao_sem_lock(status, inventario_local)

    return inventario_local


def obter_plano_execucao(servidor_acesso, inventario_local):
    inventario_remoto = obter_inventario_remoto(
        servidor_acesso, inventario_local.agrupamento, inventario_local.nuvem)

    imprimir_acao_corrente('Calculando plano de execução')
    status, plano_execucao = inventario_local.calcular_plano_execucao(
        inventario_remoto)
    validar_retorno_operacao_com_lock(status, plano_execucao, servidor_acesso,
                                      inventario_local.agrupamento, inventario_local.nuvem)
    return plano_execucao


def validar_conexao(servidor_acesso):
    imprimir_acao_corrente('Validando conexão com o VMM')
    cmd = Comando('testar_conexao', servidor_vmm=servidor_acesso.servidor_vmm)
    status, msg = cmd.executar(servidor_acesso)

    if status and not 'True' in msg:
        status = False
    validar_retorno_operacao_sem_lock(status, msg)


def configurar_vmm(servidor_acesso):
    imprimir_acao_corrente('Configurando VMM')
    cmd = Comando('configurar_vmm', servidor_vmm=servidor_acesso.servidor_vmm,
                  campos_customizados=[CAMPO_AGRUPAMENTO, CAMPO_ID,
                                       CAMPO_IMAGEM, CAMPO_REGIAO])
    status, msg = cmd.executar(servidor_acesso)

    validar_retorno_operacao_sem_lock(status, msg)


def listar_opcoes(servidor_acesso):
    imprimir_acao_corrente('Listando opções')
    cmd = Comando('listar_opcoes', servidor_vmm=servidor_acesso.servidor_vmm)
    status, opcoes = cmd.executar(servidor_acesso)

    validar_retorno_operacao_sem_lock(status, opcoes)
    regioes = re.search(r'regioes: ([0-9]{1,})', opcoes).group(1)
    str_regioes = '\n'.join(string.ascii_uppercase[0:int(regioes)])
    opcoes = opcoes.replace('regioes: {}'.format(regioes), str_regioes)
    print('\n' + opcoes)


def planejar_sincronizacao(servidor_acesso, arquivo_inventario):
    configurar_vmm(servidor_acesso)
    inventario_local = obter_inventario_local(
        servidor_acesso, arquivo_inventario)

    adquirir_lock(servidor_acesso,
                  inventario_local.agrupamento,
                  inventario_local.nuvem)

    conteudo_arquivo = None
    plano_execucao = obter_plano_execucao(servidor_acesso, inventario_local)

    if not plano_execucao.is_vazio():
        imprimir_acao_corrente('Gerando arquivo {}'.format(
            PlanoExecucao.ARQUIVO_PLANO_EXECUCAO))
        status, conteudo_arquivo = plano_execucao.gerar_arquivo()
        validar_retorno_operacao_sem_lock(status, conteudo_arquivo)

    liberar_lock(servidor_acesso, inventario_local.agrupamento,
                 inventario_local.nuvem)

    if conteudo_arquivo:
        print('\nAlterações a serem realizadas:\n{}'.format(conteudo_arquivo))
    else:
        PlanoExecucao.excluir_arquivo()
        print(
            '\nNenhuma diferença encontrada entre o inventário local e o remoto.')


def executar_sincronizacao(servidor_acesso, arquivo_plano_execucao,
                           pular_confirmacao, arquivo_inventario):
    configurar_vmm(servidor_acesso)

    # Obtendo plano de execução
    #
    # Caso de ter informado o plano de execução
    adquiriu_lock = False
    if arquivo_plano_execucao or os.path.isfile(PlanoExecucao.ARQUIVO_PLANO_EXECUCAO):
        imprimir_acao_corrente('Carregando plano de execução')
        status, plano_execucao = PlanoExecucao.carregar_plano_execucao(
            arquivo_plano_execucao or PlanoExecucao.ARQUIVO_PLANO_EXECUCAO)
        validar_retorno_operacao_sem_lock(status, plano_execucao)
    # Caso de ter informado o arquivo de inventário
    elif arquivo_inventario:
        print('AVISO: plano de execução será calculado à partir do inventário.',
              flush=True)
        inventario_local = obter_inventario_local(
            servidor_acesso, arquivo_inventario)

        adquirir_lock(servidor_acesso, inventario_local.agrupamento,
                      inventario_local.nuvem)
        adquiriu_lock = True

        plano_execucao = obter_plano_execucao(
            servidor_acesso, inventario_local)
    # Se não informou nem o plano nem o inventário, então informar erro
    else:
        finalizar_com_erro(
            'É necessário informar o plano de execução ou o arquivo de inventário.')

    if not adquiriu_lock:
        adquirir_lock(servidor_acesso, plano_execucao.agrupamento,
                      plano_execucao.nuvem)

    if plano_execucao.is_vazio():
        liberar_lock(servidor_acesso, plano_execucao.agrupamento,
                     plano_execucao.nuvem)
        print(
            '\nPlano de execução vazio: nada a alterar.')
    else:
        # Exibindo confirmação
        if not pular_confirmacao:
            print('\nAs seguintes operações serão executadas:')
            plano_execucao.imprimir_acoes()
            confirmar_acao_usuario_com_lock(
                servidor_acesso, plano_execucao.agrupamento, plano_execucao.nuvem)

        plano_execucao.executar(servidor_acesso)

        liberar_lock(servidor_acesso, plano_execucao.agrupamento,
                     plano_execucao.nuvem)
        plano_execucao.imprimir_resultado_execucao()


def remover_agrupamento_da_nuvem(servidor_acesso, agrupamento, nuvem, pular_confirmacao):
    configurar_vmm(servidor_acesso)

    adquirir_lock(servidor_acesso, agrupamento, nuvem)

    inventario_remoto = obter_inventario_remoto(
        servidor_acesso, agrupamento, nuvem)

    if not inventario_remoto.is_vazio():
        # Exibindo confirmação
        if not pular_confirmacao:
            print('\nAs seguintes máquinas serão excluídas:')
            for maquina_virtual in inventario_remoto.vms.values():
                print('ID_VMM: {}\tNome: {}\tStatus: {}'.format(
                    maquina_virtual.id_vmm,
                    maquina_virtual.nome,
                    maquina_virtual.status))
            confirmar_acao_usuario_com_lock(
                servidor_acesso, agrupamento, nuvem)

        plano_execucao = inventario_remoto.gerar_plano_exclusao()
        plano_execucao.executar(servidor_acesso)

        liberar_lock(servidor_acesso, agrupamento, nuvem)
        plano_execucao.imprimir_resultado_execucao()
    else:
        liberar_lock(servidor_acesso, agrupamento, nuvem)
        print('\nNão há máquinas do agrupamento {} na nuvem {}: nada a fazer.'
              .format(agrupamento, nuvem))


def main():
    parser = get_parser()
    args = parser.parse_args()
    if not args.comando:
        finalizar_com_erro('Comando não informado. Use a opção -h para ajuda.')

    servidor_acesso = ServidorAcesso(
        args.servidor_acesso, args.usuario, args.senha, args.servidor)
    validar_conexao(servidor_acesso)

    if args.comando == 'plan':
        planejar_sincronizacao(servidor_acesso, args.arquivo_inventario)
    elif args.comando == 'apply':
        executar_sincronizacao(
            servidor_acesso, args.arquivo_plano_execucao,
            args.pular_confirmacao, args.arquivo_inventario)
    elif args.comando == 'destroy':
        remover_agrupamento_da_nuvem(
            servidor_acesso, args.agrupamento, args.nuvem, args.pular_confirmacao)
    elif args.comando == 'opts':
        listar_opcoes(servidor_acesso)
