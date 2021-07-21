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
from vmm_manager.util.config import(CAMPO_AGRUPAMENTO, CAMPO_ID, CAMPO_IMAGEM,
                                    CAMPO_REGIAO, CAMPO_REDE_PRINCIPAL)
from vmm_manager.util.msgs import (finalizar_com_erro, formatar_msg_aviso,
                                   imprimir_acao_corrente, set_parametros_globais_escrita)
from vmm_manager.util.operacao import validar_retorno_operacao_com_lock
from vmm_manager.util.operacao import validar_retorno_operacao_sem_lock
from vmm_manager.util.operacao import adquirir_lock, liberar_lock, confirmar_acao_usuario_com_lock
from vmm_manager.entidade.inventario import Inventario


def parametro_arquivo_yaml(nome_arquivo):
    try:
        with open(nome_arquivo, 'r') as stream:
            yaml = YAML()
            yaml.load(stream)
            return nome_arquivo
    except (FileNotFoundError, IsADirectoryError) as exc:
        raise argparse.ArgumentTypeError(exc)
    except scanner.ScannerError as exc:
        raise argparse.ArgumentTypeError(
            f'YAML inválido: {exc}')


def parametro_booleano(valor):
    try:
        return strtobool(valor)
    except ValueError as error:
        raise argparse.ArgumentTypeError(
            f"'{valor}' não é um valor booleano") from error


def parametro_alfanumerico_limitado(valor):
    regex_alfa_num = re.compile(r'^[a-z]{1}[a-z0-9_]{2,39}$', re.IGNORECASE)
    if valor and not regex_alfa_num.match(valor):
        raise argparse.ArgumentTypeError(
            f"Parâmetro inválido: '{valor}'")
    return valor


def get_parser():
    parser = configargparse.ArgumentParser(
        description='''
        Script python que gerencia recursos no System Center Virtual Machine Manager (SCVMM), \
            de forma declarativa, com base em um arquivo de configuração YAML.
        ''', default_config_files=['vmm_manager.ini'])
    parser.add('-a', '--servidor-acesso',
               help='''
               Endereço (FQDN ou IP) do servidor Windows, com o módulo PSH do SCVMM instalado, \
                   que executará os scripts PowerShell. \
                   Ex: windows_host.domain.com
               ''',
               env_var='VMM_SERVIDOR_ACESSO', required=True, type=str)
    parser.add('-u', '--usuario',
               help='Usuário com permissões no servidor de acesso e no SCVMM',
               env_var='VMM_USUARIO', required=True, type=str)
    parser.add('-p', '--senha',
               help='Senha do usuário',
               env_var='VMM_SENHA', required=True, type=str)
    parser.add('-s', '--servidor',
               help='Servidor SCVMM. Ex: scvmm_server.domain.com',
               env_var='VMM_SERVIDOR', required=True, type=str)
    parser.add('-o', '--ocultar-progresso',
               help='Não imprime informações de progresso do comando',
               action='store_true')
    parser.add('--exibir-cores',
               help='Se for False, não exibe cores na saída do terminal',
               dest='exibir_cores', env_var='VMM_EXIBIR_CORES', default=True,
               required=False, type=parametro_booleano)

    subprasers = parser.add_subparsers(dest='comando')
    plan = subprasers.add_parser(
        'plan', help='Cria um plano de execução, \
            com ações necessárias à sincronização do inventário')
    plan.add_argument('--inventario',
                      help='Arquivo YAML com a especificação das máquinas',
                      dest='arquivo_inventario', env_var='VMM_INVENTARIO',
                      required=True, type=parametro_arquivo_yaml)

    apply = subprasers.add_parser(
        'apply', help='Aplica as alterações necessárias no SCVMM')
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
        'opts', help='Lista as opções disponíveis no SCVMM para cada parâmetro da VM')

    show = subprasers.add_parser(
        'show', help='Imprime json com os dados e situação dos ativos do inventário')
    show.add_argument('--inventario',
                      help='Arquivo YAML com a especificação das máquinas',
                      dest='arquivo_inventario', env_var='VMM_INVENTARIO',
                      required=True, type=parametro_arquivo_yaml)
    show.add_argument('--vm',
                      help='Nome da máquina virtual', default='',
                      dest='nome_vm', required=False,
                      type=parametro_alfanumerico_limitado)
    show.add_argument('--dados-completos',
                      help='Se for True, exibe todos os dados da VM',
                      dest='dados_completos', env_var='VMM_DADOS_COMPLETOS',
                      required=False, type=parametro_booleano)

    return parser


def obter_inventario_remoto(servidor_acesso, agrupamento, nuvem, ocultar_progresso,
                            filtro_nome_vm=None, filtro_dados_completos=True):
    imprimir_acao_corrente('Obtendo inventário remoto', ocultar_progresso)

    parser_remoto = ParserRemoto(agrupamento, nuvem)
    status, inventario_remoto = parser_remoto.get_inventario(
        servidor_acesso, filtro_nome_vm, filtro_dados_completos)
    validar_retorno_operacao_com_lock(status, inventario_remoto,
                                      servidor_acesso, agrupamento,
                                      nuvem, ocultar_progresso)

    return inventario_remoto


def obter_inventario_local(servidor_acesso, arquivo_inventario, ocultar_progresso,
                           filtro_nome_vm=None, filtro_dados_completos=True):
    imprimir_acao_corrente('Obtendo inventário local', ocultar_progresso)

    parser_local = ParserLocal(arquivo_inventario)
    status, inventario_local = parser_local.get_inventario(
        servidor_acesso, filtro_nome_vm, filtro_dados_completos)
    validar_retorno_operacao_sem_lock(
        status, inventario_local, ocultar_progresso)

    return inventario_local


def obter_plano_execucao(servidor_acesso, inventario_local, ocultar_progresso):
    inventario_remoto = obter_inventario_remoto(
        servidor_acesso, inventario_local.agrupamento,
        inventario_local.nuvem, ocultar_progresso)

    imprimir_acao_corrente('Calculando plano de execução', ocultar_progresso)
    status, plano_execucao = inventario_local.calcular_plano_execucao(
        inventario_remoto)
    validar_retorno_operacao_com_lock(status, plano_execucao, servidor_acesso,
                                      inventario_local.agrupamento,
                                      inventario_local.nuvem, ocultar_progresso)
    return plano_execucao


def validar_conexao(servidor_acesso, ocultar_progresso):
    imprimir_acao_corrente('Validando conexão com o VMM', ocultar_progresso)
    cmd = Comando('testar_conexao', servidor_vmm=servidor_acesso.servidor_vmm)
    status, msg = cmd.executar(servidor_acesso)

    if status and not 'True' in msg:
        status = False
    validar_retorno_operacao_sem_lock(status, msg, ocultar_progresso)


def configurar_vmm(servidor_acesso, ocultar_progresso):
    imprimir_acao_corrente('Configurando VMM', ocultar_progresso)
    cmd = Comando('configurar_vmm', servidor_vmm=servidor_acesso.servidor_vmm,
                  campos_customizados=[CAMPO_AGRUPAMENTO, CAMPO_ID,
                                       CAMPO_IMAGEM, CAMPO_REGIAO,
                                       CAMPO_REDE_PRINCIPAL])
    status, msg = cmd.executar(servidor_acesso)

    validar_retorno_operacao_sem_lock(status, msg, ocultar_progresso)


def listar_opcoes(servidor_acesso, ocultar_progresso):
    imprimir_acao_corrente('Listando opções', ocultar_progresso)
    cmd = Comando('listar_opcoes', servidor_vmm=servidor_acesso.servidor_vmm)
    status, opcoes = cmd.executar(servidor_acesso)

    validar_retorno_operacao_sem_lock(status, opcoes, ocultar_progresso)
    regioes = re.search(r'regioes: ([0-9]{1,})', opcoes).group(1)
    str_regioes = '\n'.join(string.ascii_uppercase[0:int(regioes)])
    opcoes = opcoes.replace(f'regioes: {regioes}', str_regioes)
    print('\n' + opcoes)


def imprimir_json_inventario(servidor_acesso, arquivo_inventario,
                             nome_vm, dados_completos, ocultar_progresso):
    configurar_vmm(servidor_acesso, ocultar_progresso)
    inventario_local = obter_inventario_local(
        servidor_acesso, arquivo_inventario, ocultar_progresso,
        filtro_nome_vm=nome_vm, filtro_dados_completos=dados_completos)

    adquirir_lock(servidor_acesso, inventario_local.agrupamento,
                  inventario_local.nuvem, ocultar_progresso)

    inventario_remoto = obter_inventario_remoto(
        servidor_acesso, inventario_local.agrupamento,
        inventario_local.nuvem, ocultar_progresso,
        filtro_nome_vm=nome_vm, filtro_dados_completos=dados_completos)

    liberar_lock(servidor_acesso, inventario_local.agrupamento,
                 inventario_local.nuvem, ocultar_progresso)

    imprimir_acao_corrente('Gerando JSON', ocultar_progresso)
    status, json_inventario = Inventario.get_json(
        inventario_local, inventario_remoto, dados_completos)
    validar_retorno_operacao_sem_lock(
        status, json_inventario, ocultar_progresso)
    print(json_inventario)


def planejar_sincronizacao(servidor_acesso, arquivo_inventario, ocultar_progresso):
    configurar_vmm(servidor_acesso, ocultar_progresso)
    inventario_local = obter_inventario_local(
        servidor_acesso, arquivo_inventario, ocultar_progresso)

    adquirir_lock(servidor_acesso,
                  inventario_local.agrupamento,
                  inventario_local.nuvem, ocultar_progresso)

    conteudo_arquivo = None
    plano_execucao = obter_plano_execucao(
        servidor_acesso, inventario_local, ocultar_progresso)

    if not plano_execucao.is_vazio():
        imprimir_acao_corrente(
            f'Gerando arquivo {PlanoExecucao.ARQUIVO_PLANO_EXECUCAO}',
            ocultar_progresso)
        status, conteudo_arquivo = plano_execucao.gerar_arquivo()
        validar_retorno_operacao_sem_lock(
            status, conteudo_arquivo, ocultar_progresso)

    liberar_lock(servidor_acesso, inventario_local.agrupamento,
                 inventario_local.nuvem, ocultar_progresso)

    if conteudo_arquivo:
        print(f'\nAlterações a serem realizadas:\n{conteudo_arquivo}')
    else:
        PlanoExecucao.excluir_arquivo()
        print(
            '\nNenhuma diferença encontrada entre o inventário local e o remoto.')


def executar_sincronizacao(servidor_acesso, arquivo_plano_execucao,
                           pular_confirmacao, arquivo_inventario,
                           ocultar_progresso):
    configurar_vmm(servidor_acesso, ocultar_progresso)

    # Obtendo plano de execução
    #
    # Caso de ter informado o plano de execução
    adquiriu_lock = False
    if arquivo_plano_execucao or os.path.isfile(PlanoExecucao.ARQUIVO_PLANO_EXECUCAO):
        imprimir_acao_corrente(
            'Carregando plano de execução', ocultar_progresso)
        status, plano_execucao = PlanoExecucao.carregar_plano_execucao(
            arquivo_plano_execucao or PlanoExecucao.ARQUIVO_PLANO_EXECUCAO)
        validar_retorno_operacao_sem_lock(
            status, plano_execucao, ocultar_progresso)
    # Caso de ter informado o arquivo de inventário
    elif arquivo_inventario:
        print(formatar_msg_aviso(
            'plano de execução será calculado à partir do inventário.'),
            flush=True)
        inventario_local = obter_inventario_local(
            servidor_acesso, arquivo_inventario, ocultar_progresso)

        adquirir_lock(servidor_acesso, inventario_local.agrupamento,
                      inventario_local.nuvem, ocultar_progresso)
        adquiriu_lock = True

        plano_execucao = obter_plano_execucao(
            servidor_acesso, inventario_local, ocultar_progresso)
    # Se não informou nem o plano nem o inventário, então informar erro
    else:
        finalizar_com_erro(
            'É necessário informar o plano de execução ou o arquivo de inventário.')

    if not adquiriu_lock:
        adquirir_lock(servidor_acesso, plano_execucao.agrupamento,
                      plano_execucao.nuvem, ocultar_progresso)

    if plano_execucao.is_vazio():
        liberar_lock(servidor_acesso, plano_execucao.agrupamento,
                     plano_execucao.nuvem, ocultar_progresso)
        print(
            '\nPlano de execução vazio: nada a alterar.')
    else:
        # Exibindo confirmação
        if not pular_confirmacao:
            print('\nAs seguintes operações serão executadas:')
            plano_execucao.imprimir_acoes()
            confirmar_acao_usuario_com_lock(
                servidor_acesso, plano_execucao.agrupamento, plano_execucao.nuvem)

        plano_execucao.executar(servidor_acesso, ocultar_progresso)

        liberar_lock(servidor_acesso, plano_execucao.agrupamento,
                     plano_execucao.nuvem, ocultar_progresso)
        plano_execucao.imprimir_resultado_execucao()


def remover_agrupamento_da_nuvem(servidor_acesso, agrupamento, nuvem,
                                 pular_confirmacao, ocultar_progresso):
    configurar_vmm(servidor_acesso, ocultar_progresso)

    adquirir_lock(servidor_acesso, agrupamento, nuvem, ocultar_progresso)

    inventario_remoto = obter_inventario_remoto(
        servidor_acesso, agrupamento, nuvem, ocultar_progresso)

    if not inventario_remoto.is_vazio():
        # Exibindo confirmação
        if not pular_confirmacao:
            print('\nAs seguintes máquinas serão excluídas:')
            for maquina_virtual in inventario_remoto.vms.values():
                print(
                    f'ID_VMM: {maquina_virtual.id_vmm}\t'
                    f'Nome: {maquina_virtual.nome}\t'
                    f'Status: { maquina_virtual.status}')
            confirmar_acao_usuario_com_lock(
                servidor_acesso, agrupamento, nuvem)

        plano_execucao = inventario_remoto.gerar_plano_exclusao()
        plano_execucao.executar(servidor_acesso, ocultar_progresso)

        liberar_lock(servidor_acesso, agrupamento, nuvem, ocultar_progresso)
        plano_execucao.imprimir_resultado_execucao()
    else:
        liberar_lock(servidor_acesso, agrupamento, nuvem, ocultar_progresso)
        print(
            f'\nNão há máquinas do agrupamento {agrupamento} na nuvem {nuvem}: nada a fazer.')


def main():
    parser = get_parser()
    args = parser.parse_args()

    set_parametros_globais_escrita(args.exibir_cores)

    if not args.comando:
        finalizar_com_erro('Comando não informado. Use a opção -h para ajuda.')

    servidor_acesso = ServidorAcesso(
        args.servidor_acesso, args.usuario, args.senha, args.servidor)
    validar_conexao(servidor_acesso, args.ocultar_progresso)

    if args.comando == 'plan':
        planejar_sincronizacao(
            servidor_acesso, args.arquivo_inventario, args.ocultar_progresso)
    elif args.comando == 'apply':
        executar_sincronizacao(
            servidor_acesso, args.arquivo_plano_execucao,
            args.pular_confirmacao, args.arquivo_inventario,
            args.ocultar_progresso)
    elif args.comando == 'destroy':
        remover_agrupamento_da_nuvem(
            servidor_acesso, args.agrupamento, args.nuvem,
            args.pular_confirmacao, args.ocultar_progresso)
    elif args.comando == 'opts':
        listar_opcoes(servidor_acesso, args.ocultar_progresso)
    elif args.comando == 'show':
        imprimir_json_inventario(
            servidor_acesso, args.arquivo_inventario,
            args.nome_vm.upper(), args.dados_completos,
            args.ocultar_progresso)
