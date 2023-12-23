"""
Operation helper functions.
"""

import sys
import os
import platform
import json
from vmm_manager.util.msgs import formatar_msg_aviso, imprimir_ok, imprimir_erro
from vmm_manager.util.msgs import formatar_msg_erro, finalizar_com_erro
from vmm_manager.util.msgs import get_str_data_formatada, imprimir_acao_corrente
from vmm_manager.infra.comando import Comando


def __confirmar_acao_usuario(
    servidor_acesso=None,
    group=None,
    cloud=None,
    ocultar_progresso=False
):
    resposta = None
    while resposta not in ['s', 'n', 'y']:
        resposta = input('Continue? [y/n] ').lower()

        if resposta == 'n':
            if servidor_acesso and group and cloud:
                liberar_lock(servidor_acesso, group,
                             cloud, ocultar_progresso)

            if not ocultar_progresso:
                print(formatar_msg_aviso('Canceled by user.'))

            sys.exit(0)


def confirmar_acao_usuario_sem_lock():
    __confirmar_acao_usuario()


def confirmar_acao_usuario_com_lock(servidor_acesso, group, cloud, ocultar_progresso):
    __confirmar_acao_usuario(
        servidor_acesso, group, cloud, ocultar_progresso)


def validar_retorno_operacao_sem_lock(status, msg, ocultar_progresso):
    if status:
        imprimir_ok(ocultar_progresso)
    else:
        imprimir_erro(ocultar_progresso)
        finalizar_com_erro(msg)


def validar_retorno_operacao_com_lock(
    status,
    msg,
    servidor_acesso,
    group,
    cloud,
    ocultar_progresso
):
    if status:
        imprimir_ok(ocultar_progresso)
    else:
        imprimir_erro(ocultar_progresso)
        liberar_lock(servidor_acesso, group, cloud, ocultar_progresso)
        finalizar_com_erro(msg)


def adquirir_lock(servidor_acesso, group, cloud, ocultar_progresso):
    imprimir_acao_corrente('Adding lock', ocultar_progresso)

    cmd = Comando('adquirir_lock',
                  lockfile=servidor_acesso.get_caminho_lockfile(
                      group,
                      cloud),
                  pid=os.getpid(),
                  host=platform.node(),
                  group=group,
                  cloud=cloud,
                  data=get_str_data_formatada('%d/%m/%Y às %H:%M:%S.%f'))

    status, retorno_cmd = cmd.executar(servidor_acesso)
    if status:
        dados_lock = json.loads(retorno_cmd)
        if not dados_lock.get('Sucesso'):
            status = False
            retorno_cmd = f"The process {dados_lock.get('PIDProcesso')}, " \
                f"started in { dados_lock.get('DataLock')} " \
                f"on the server {dados_lock.get('HostLock')}, " \
                f"is already working on the {dados_lock.get('Agrupamento')} group " \
                f"in the {dados_lock.get('Nuvem')} cloud."

    validar_retorno_operacao_sem_lock(status, retorno_cmd, ocultar_progresso)


def liberar_lock(servidor_acesso, group, cloud, ocultar_progresso):
    imprimir_acao_corrente('Removing lock', ocultar_progresso)

    cmd = Comando('liberar_lock',
                  lockfile=servidor_acesso.get_caminho_lockfile(
                      group,
                      cloud))

    status, _ = cmd.executar(servidor_acesso)
    if status:
        imprimir_ok(ocultar_progresso)
    else:
        imprimir_erro(ocultar_progresso)
        print(formatar_msg_erro(
            'The lock file could not be removed. Please remove it manually.'))
