"""
Operation helper functions.
"""

import json
import os
import platform
import sys

from vmm_manager.infra.command import Command
from vmm_manager.util.msgs import (finalizar_com_erro, formatar_msg_aviso,
                                   formatar_msg_erro, get_str_data_formatada,
                                   imprimir_acao_corrente, imprimir_erro,
                                   imprimir_ok)


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
                remove_operation_lock(servidor_acesso, group,
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
        remove_operation_lock(servidor_acesso, group, cloud, ocultar_progresso)
        finalizar_com_erro(msg)


def add_operation_lock(servidor_acesso, group, cloud, ocultar_progresso):
    imprimir_acao_corrente('Adding lock', ocultar_progresso)

    cmd = Command('add_operation_lock',
                  lockfile=servidor_acesso.get_caminho_lockfile(
                      group,
                      cloud),
                  pid=os.getpid(),
                  host=platform.node(),
                  group=group,
                  cloud=cloud,
                  data=get_str_data_formatada('%m-%d-%Y at %I:%M:%S.%f %p'))

    status, retorno_cmd = cmd.executar(servidor_acesso)
    if status:
        dados_lock = json.loads(retorno_cmd)
        if not dados_lock.get('Success'):
            status = False
            retorno_cmd = f"The process {dados_lock.get('PID')}, " \
                f"started in {dados_lock.get('DataLock')} " \
                f"on the server {dados_lock.get('HostLock')}, " \
                f"is already working on the {dados_lock.get('Group')} group " \
                f"in the {dados_lock.get('Cloud')} cloud."

    validar_retorno_operacao_sem_lock(status, retorno_cmd, ocultar_progresso)


def remove_operation_lock(servidor_acesso, group, cloud, ocultar_progresso):
    imprimir_acao_corrente('Removing lock', ocultar_progresso)

    cmd = Command('remove_operation_lock',
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
