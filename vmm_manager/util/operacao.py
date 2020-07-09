"""
Módulo com funções úteis de operação
"""

import sys
import os
import platform
import json
from vmm_manager.util.msgs import imprimir_ok, imprimir_erro
from vmm_manager.util.msgs import formatar_msg_erro, finalizar_com_erro
from vmm_manager.util.msgs import get_str_data_formatada, imprimir_acao_corrente
from vmm_manager.infra.comando import Comando


def __confirmar_acao_usuario(servidor_acesso=None, agrupamento=None, nuvem=None,
                             ocultar_progresso=False):
    resposta = None
    while resposta not in ['s', 'n']:
        resposta = input('Deseja executar? (s/n): ')
        if resposta == 'n':
            if servidor_acesso and agrupamento and nuvem:
                liberar_lock(servidor_acesso, agrupamento,
                             nuvem, ocultar_progresso)
            print('Ação cancelada pelo usuário.')
            sys.exit(0)


def confirmar_acao_usuario_sem_lock():
    __confirmar_acao_usuario()


def confirmar_acao_usuario_com_lock(servidor_acesso, agrupamento, nuvem):
    __confirmar_acao_usuario(servidor_acesso, agrupamento, nuvem)


def validar_retorno_operacao_sem_lock(status, msg, ocultar_progresso):
    if status:
        imprimir_ok(ocultar_progresso)
    else:
        imprimir_erro(ocultar_progresso)
        finalizar_com_erro(msg)


def validar_retorno_operacao_com_lock(status, msg, servidor_acesso,
                                      agrupamento, nuvem, ocultar_progresso):
    if status:
        imprimir_ok(ocultar_progresso)
    else:
        imprimir_erro(ocultar_progresso)
        liberar_lock(servidor_acesso, agrupamento, nuvem, ocultar_progresso)
        finalizar_com_erro(msg)


def adquirir_lock(servidor_acesso, agrupamento, nuvem, ocultar_progresso):
    imprimir_acao_corrente('Adquirindo lock', ocultar_progresso)

    cmd = Comando('adquirir_lock',
                  lockfile=servidor_acesso.get_caminho_lockfile(
                      agrupamento,
                      nuvem),
                  pid=os.getpid(),
                  host=platform.node(),
                  agrupamento=agrupamento,
                  nuvem=nuvem,
                  data=get_str_data_formatada('%d/%m/%Y às %H:%M:%S.%f'))

    status, retorno_cmd = cmd.executar(servidor_acesso)
    if status:
        dados_lock = json.loads(retorno_cmd)
        if not dados_lock.get('Sucesso'):
            status = False
            retorno_cmd = f"O processo {dados_lock.get('PIDProcesso')}, " \
                f"iniciado em { dados_lock.get('DataLock')} " \
                f"no servidor {dados_lock.get('HostLock')}, " \
                f"já está manipulando o agrupamento {dados_lock.get('Agrupamento')} " \
                f"na nuvem {dados_lock.get('Nuvem')}."

    validar_retorno_operacao_sem_lock(status, retorno_cmd, ocultar_progresso)


def liberar_lock(servidor_acesso, agrupamento, nuvem, ocultar_progresso):
    imprimir_acao_corrente('Liberando lock', ocultar_progresso)

    cmd = Comando('liberar_lock',
                  lockfile=servidor_acesso.get_caminho_lockfile(
                      agrupamento,
                      nuvem))

    status, _ = cmd.executar(servidor_acesso)
    if status:
        imprimir_ok(ocultar_progresso)
    else:
        imprimir_erro(ocultar_progresso)
        print(formatar_msg_erro(
            'Erro ao liberar o lock: você terá que excluir o arquivo manualmente.'))
