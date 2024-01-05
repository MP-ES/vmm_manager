"""
Manages resources in the System Center Virtual Machine Manager (SCVMM),
in a declarative way, based on a YAML configuration file.
"""

import argparse
import os
import re
import string

import configargparse
from ruamel.yaml import YAML, scanner

from vmm_manager.entity.inventory import Inventory
from vmm_manager.entity.plan import Plan
from vmm_manager.infra.access_server import AccessServer
from vmm_manager.infra.command import Command
from vmm_manager.parser.parser_local import ParserLocal
from vmm_manager.parser.parser_remote import ParserRemote
from vmm_manager.util.config import (FIELD_GROUP, FIELD_ID, FIELD_IMAGE,
                                     FIELD_NETWORK_DEFAULT, FIELD_REGION)
from vmm_manager.util.msgs import (finalizar_com_erro, formatar_msg_aviso,
                                   imprimir_acao_corrente,
                                   set_parametros_globais_escrita)
from vmm_manager.util.operation import (add_operation_lock,
                                        confirmar_acao_usuario_com_lock,
                                        remove_operation_lock,
                                        validar_retorno_operacao_com_lock,
                                        validar_retorno_operacao_sem_lock)


def parametro_arquivo_yaml(nome_arquivo):
    try:
        with open(nome_arquivo, 'r', encoding='utf8') as stream:
            yaml = YAML()
            yaml.load(stream)

            return nome_arquivo
    except (FileNotFoundError, IsADirectoryError) as exc:
        raise argparse.ArgumentTypeError(exc)
    except scanner.ScannerError as exc:
        raise argparse.ArgumentTypeError(
            f'Invalid YAML: {exc}')


def parametro_alfanumerico_limitado(value):
    regex_alfa_num = re.compile(r'^[a-z]{1}[a-z0-9_]{2,39}$', re.IGNORECASE)

    if value and not regex_alfa_num.match(value):
        raise argparse.ArgumentTypeError(
            f"Invalid parameter: '{value}'")

    return value


def get_parser():
    parser = configargparse.ArgumentParser(
        description='''
        Python script that manages resources in the System Center Virtual Machine Manager (SCVMM), \
        in a declarative way, based on a YAML configuration file.
        ''', default_config_files=['vmm_manager.ini'])

    parser.add('-a', '--access-point',
               help='''
                Address (FQDN or IP) of the Windows server, \
                with the VirtualMachineManager PowerShell module installed, \
                which will run the PowerShell scripts. \
                E.g.: windows_host.domain.com
               ''',
               env_var='VMM_ACCESS_POINT', required=True, type=str)
    parser.add('-u', '--username',
               help='Username with access to the access point and the SCVMM',
               env_var='VMM_USERNAME', required=True, type=str)
    parser.add('-p', '--password',
               help='User password',
               env_var='VMM_PASSWORD', required=True, type=str)
    parser.add('-s', '--server',
               help='SCVMM server. E.g.: scvmm_server.domain.com',
               env_var='VMM_SERVER', required=True, type=str)
    parser.add('--hide-progress',
               help='Hide progress messages',
               env_var='VMM_HIDE_PROGRESS', required=False, action='store_true')
    parser.add('--no-color',
               help='Do not use colors in the output',
               env_var='VMM_NO_COLOR', required=False, action='store_true')

    subprasers = parser.add_subparsers(dest='command')
    plan = subprasers.add_parser(
        'plan', help='Create an execution plan \
            based on the difference between the local and remote inventory')
    plan.add_argument('--inventory',
                      help='YAML file with resource specifications',
                      dest='inventory_file', env_var='VMM_INVENTORY',
                      required=True, type=parametro_arquivo_yaml)

    apply = subprasers.add_parser(
        'apply',
        help='Apply the execution plan to the SCVMM')
    apply.add_argument('--execution-plan',
                       help='YAML file with the execution plan',
                       dest='execution_plan_file', env_var='VMM_EXECUTION_PLAN',
                       required=False, type=parametro_arquivo_yaml)
    apply.add_argument('--inventory',
                       help='YAML file with resource specifications',
                       dest='inventory_file', env_var='VMM_INVENTORY',
                       required=False, type=parametro_arquivo_yaml)
    apply.add_argument('--skip-confirmation',
                       help='Skip confirmation',
                       env_var='VMM_SKIP_CONFIRMATION', required=False, action='store_true')
    apply.add_argument('--interval-between-resources',
                       help='Interval (in seconds) to wait between operations on different resources. '
                            'It has precedence over the value defined in the inventory file. '
                            'It is useful when you are working with clusters, and you want to '
                            'wait for the node stabilization before starting the operations on the next node.',
                       env_var='VMM_INTERVAL_BETWEEN_RESOURCES', required=False, type=int, default=-1)

    destroy = subprasers.add_parser(
        'destroy', help='Remove all machines from the specified group in the specified cloud')
    destroy.add_argument(
        '--group', help='Group name', required=True)
    destroy.add_argument(
        '--cloud', help='Cloud name', required=True)
    destroy.add_argument('--skip-confirmation',
                         help='Skip confirmation',
                         env_var='VMM_SKIP_CONFIRMATION', required=False, action='store_true')

    subprasers.add_parser(
        'opts', help='List available options in the SCVMM for each field')

    show = subprasers.add_parser(
        'show', help='Show a JSON data with information about the resources')
    show.add_argument('--inventory',
                      help='YAML file with resource specifications',
                      dest='inventory_file', env_var='VMM_INVENTORY',
                      required=True, type=parametro_arquivo_yaml)
    show.add_argument('--vm-name',
                      help='Virtual machine name', default='',
                      required=False, type=parametro_alfanumerico_limitado)
    show.add_argument('--all-data',
                      help='Show all the resource data',
                      env_var='VMM_ALL_DATA', required=False, action='store_true')

    return parser


def obter_inventario_remoto(
    servidor_acesso,
    group,
    cloud,
    ocultar_progresso,
    filtro_nome_vm=None,
    filtro_dados_completos=True
):
    imprimir_acao_corrente('Loading remote inventory', ocultar_progresso)

    parser_remoto = ParserRemote(group, cloud)
    status, inventario_remoto = parser_remoto.get_inventario(
        servidor_acesso, filtro_nome_vm, filtro_dados_completos)
    validar_retorno_operacao_com_lock(status, inventario_remoto,
                                      servidor_acesso, group,
                                      cloud, ocultar_progresso)

    return inventario_remoto


def obter_inventario_local(
    servidor_acesso,
    inventory_file,
    ocultar_progresso,
    filtro_nome_vm=None,
    filtro_dados_completos=True
):
    imprimir_acao_corrente('Loading local inventory', ocultar_progresso)

    parser_local = ParserLocal(inventory_file)
    status, inventario_local = parser_local.get_inventario(
        servidor_acesso, filtro_nome_vm, filtro_dados_completos)
    validar_retorno_operacao_sem_lock(
        status, inventario_local, ocultar_progresso)

    return inventario_local


def obter_plano_execucao(servidor_acesso, inventario_local: Inventory, ocultar_progresso):
    inventario_remoto = obter_inventario_remoto(
        servidor_acesso, inventario_local.group,
        inventario_local.cloud, ocultar_progresso)

    imprimir_acao_corrente('Calculation execution plan', ocultar_progresso)
    status, plano_execucao = inventario_local.calcular_plano_execucao(
        inventario_remoto)
    validar_retorno_operacao_com_lock(status, plano_execucao, servidor_acesso,
                                      inventario_local.group,
                                      inventario_local.cloud, ocultar_progresso)
    return plano_execucao


def validar_conexao(servidor_acesso, ocultar_progresso):
    imprimir_acao_corrente('Checking VMM connection', ocultar_progresso)
    cmd = Command('connection_test', vmm_server=servidor_acesso.vmm_server)
    status, msg = cmd.executar(servidor_acesso)

    if status and 'True' not in msg:
        status = False
    validar_retorno_operacao_sem_lock(status, msg, ocultar_progresso)


def vmm_setup(servidor_acesso, ocultar_progresso):
    imprimir_acao_corrente('Setting up the VMM', ocultar_progresso)
    cmd = Command('vmm_setup', vmm_server=servidor_acesso.vmm_server,
                  campos_customizados=[FIELD_GROUP, FIELD_ID,
                                       FIELD_IMAGE, FIELD_REGION,
                                       FIELD_NETWORK_DEFAULT])
    status, msg = cmd.executar(servidor_acesso)

    validar_retorno_operacao_sem_lock(status, msg, ocultar_progresso)


def list_options(servidor_acesso, ocultar_progresso):
    imprimir_acao_corrente('Listing options', ocultar_progresso)
    cmd = Command('list_options', vmm_server=servidor_acesso.vmm_server)
    status, opcoes = cmd.executar(servidor_acesso)

    validar_retorno_operacao_sem_lock(status, opcoes, ocultar_progresso)
    regioes = re.search(r'regions: ([0-9]{1,})', opcoes).group(1)
    str_regioes = '\n'.join(string.ascii_uppercase[0:int(regioes)])
    opcoes = opcoes.replace(f'regions: {regioes}', str_regioes)
    print('\n' + opcoes)


def imprimir_json_inventario(
    servidor_acesso,
    inventory_file,
    vm_name,
    all_data,
    ocultar_progresso
):
    vmm_setup(servidor_acesso, ocultar_progresso)
    inventario_local = obter_inventario_local(
        servidor_acesso, inventory_file, ocultar_progresso,
        filtro_nome_vm=vm_name, filtro_dados_completos=all_data)

    add_operation_lock(servidor_acesso, inventario_local.group,
                       inventario_local.cloud, ocultar_progresso)

    inventario_remoto = obter_inventario_remoto(
        servidor_acesso, inventario_local.group,
        inventario_local.cloud, ocultar_progresso,
        filtro_nome_vm=vm_name, filtro_dados_completos=all_data)

    remove_operation_lock(servidor_acesso, inventario_local.group,
                          inventario_local.cloud, ocultar_progresso)

    imprimir_acao_corrente('Generating JSON', ocultar_progresso)
    status, json_inventario = Inventory.get_json(
        inventario_local, inventario_remoto, all_data)
    validar_retorno_operacao_sem_lock(
        status, json_inventario, ocultar_progresso)
    print(json_inventario)


def planejar_sincronizacao(servidor_acesso, inventory_file, ocultar_progresso):
    vmm_setup(servidor_acesso, ocultar_progresso)
    inventario_local = obter_inventario_local(
        servidor_acesso, inventory_file, ocultar_progresso)

    add_operation_lock(servidor_acesso,
                       inventario_local.group,
                       inventario_local.cloud, ocultar_progresso)

    conteudo_arquivo = None
    plano_execucao = obter_plano_execucao(
        servidor_acesso, inventario_local, ocultar_progresso)

    if not plano_execucao.is_vazio():
        imprimir_acao_corrente(
            f'Saving file {Plan.ARQUIVO_PLANO_EXECUCAO}',
            ocultar_progresso)
        status, conteudo_arquivo = plano_execucao.gerar_arquivo()
        validar_retorno_operacao_sem_lock(
            status, conteudo_arquivo, ocultar_progresso)

    remove_operation_lock(servidor_acesso, inventario_local.group,
                          inventario_local.cloud, ocultar_progresso)

    if conteudo_arquivo:
        print(f'\nChanges to apply:\n{conteudo_arquivo}')
    else:
        Plan.excluir_arquivo()
        print(
            '\nNo differences between the local and remote inventory: nothing to do.')


def executar_sincronizacao(
    servidor_acesso,
    execution_plan_file,
    skip_confirmation,
    inventory_file,
    ocultar_progresso,
    interval_between_resources
):
    vmm_setup(servidor_acesso, ocultar_progresso)

    # Obtendo plano de execução
    #
    # Caso de ter informado o plano de execução
    adquiriu_lock = False
    if execution_plan_file or os.path.isfile(Plan.ARQUIVO_PLANO_EXECUCAO):
        imprimir_acao_corrente(
            'Loading execution plan', ocultar_progresso)
        status, plano_execucao = Plan.carregar_plano_execucao(
            execution_plan_file or Plan.ARQUIVO_PLANO_EXECUCAO)
        validar_retorno_operacao_sem_lock(
            status, plano_execucao, ocultar_progresso)
    # Caso de ter informado o arquivo de inventário
    elif inventory_file:
        print(formatar_msg_aviso(
            'The execution plan will be generated based on the local inventory.'),
            flush=True)
        inventario_local = obter_inventario_local(
            servidor_acesso, inventory_file, ocultar_progresso)

        add_operation_lock(servidor_acesso, inventario_local.group,
                           inventario_local.cloud, ocultar_progresso)
        adquiriu_lock = True

        plano_execucao = obter_plano_execucao(
            servidor_acesso,
            inventario_local,
            ocultar_progresso
        )
    # Se não informou nem o plano nem o inventário, então informar erro
    else:
        finalizar_com_erro(
            'You must pass the execution plan or the inventory file.')

    if not adquiriu_lock:
        add_operation_lock(servidor_acesso, plano_execucao.group,
                           plano_execucao.cloud, ocultar_progresso)

    if plano_execucao.is_vazio():
        remove_operation_lock(servidor_acesso, plano_execucao.group,
                              plano_execucao.cloud, ocultar_progresso)
        print(
            '\nThe execution plan is empty: nothing to do.')
    else:
        # Exibindo confirmação
        if not skip_confirmation:
            print('\nThe following actions will be performed:')
            plano_execucao.imprimir_acoes()
            confirmar_acao_usuario_com_lock(
                servidor_acesso, plano_execucao.group,
                plano_execucao.cloud, ocultar_progresso)

        plano_execucao.executar(servidor_acesso, ocultar_progresso, interval_between_resources)

        remove_operation_lock(servidor_acesso, plano_execucao.group,
                              plano_execucao.cloud, ocultar_progresso)
        plano_execucao.imprimir_resultado_execucao()


def remover_agrupamento_da_nuvem(
    servidor_acesso,
    group,
    cloud,
    skip_confirmation,
    ocultar_progresso
):
    vmm_setup(servidor_acesso, ocultar_progresso)

    add_operation_lock(servidor_acesso, group, cloud, ocultar_progresso)

    inventario_remoto = obter_inventario_remoto(
        servidor_acesso, group, cloud, ocultar_progresso)

    if not inventario_remoto.is_vazio():
        # Exibindo confirmação
        if not skip_confirmation:
            print('\nThe following resources will be removed:')
            for maquina_virtual in inventario_remoto.vms.values():
                print(
                    f'VMM ID: {maquina_virtual.vmm_id}\t'
                    f'Name: {maquina_virtual.name}\t'
                    f'Status: {maquina_virtual.status}')
            confirmar_acao_usuario_com_lock(
                servidor_acesso, group, cloud, ocultar_progresso)

        plano_execucao = inventario_remoto.gerar_plano_exclusao()
        plano_execucao.executar(servidor_acesso, ocultar_progresso)

        remove_operation_lock(servidor_acesso, group, cloud, ocultar_progresso)
        plano_execucao.imprimir_resultado_execucao()
    else:
        remove_operation_lock(servidor_acesso, group, cloud, ocultar_progresso)
        print(
            f'\nThere are no resources in the cloud {cloud} for the group {group}.')


def main():
    parser = get_parser()
    args = parser.parse_args()

    set_parametros_globais_escrita(args.no_color)

    if not args.command:
        finalizar_com_erro('No command. Use -h for help.')

    servidor_acesso = AccessServer(
        args.access_point, args.username, args.password, args.server)
    validar_conexao(servidor_acesso, args.hide_progress)

    if args.command == 'plan':
        planejar_sincronizacao(
            servidor_acesso, args.inventory_file, args.hide_progress)
    elif args.command == 'apply':
        executar_sincronizacao(
            servidor_acesso, args.execution_plan_file,
            args.skip_confirmation, args.inventory_file,
            args.hide_progress, args.interval_between_resources)
    elif args.command == 'destroy':
        remover_agrupamento_da_nuvem(
            servidor_acesso, args.group, args.cloud,
            args.skip_confirmation, args.hide_progress)
    elif args.command == 'opts':
        list_options(servidor_acesso, args.hide_progress)
    elif args.command == 'show':
        imprimir_json_inventario(
            servidor_acesso, args.inventory_file,
            args.vm_name.upper(), args.all_data,
            args.hide_progress)
