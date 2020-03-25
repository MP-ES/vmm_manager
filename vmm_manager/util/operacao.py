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


def __confirmar_acao_usuario(servidor_acesso=None, agrupamento=None, nuvem=None):
    resposta = None
    while resposta not in ['s', 'n']:
        resposta = input('Deseja executar? (s/n): ')
        if resposta == 'n':
            if servidor_acesso and agrupamento and nuvem:
                liberar_lock(servidor_acesso, agrupamento, nuvem)
            print('Ação cancelada pelo usuário.')
            sys.exit(0)


def confirmar_acao_usuario_sem_lock():
    __confirmar_acao_usuario()


def confirmar_acao_usuario_com_lock(servidor_acesso, agrupamento, nuvem):
    __confirmar_acao_usuario(servidor_acesso, agrupamento, nuvem)


def validar_retorno_operacao_sem_lock(status, msg):
    if status:
        imprimir_ok()
    else:
        imprimir_erro()
        finalizar_com_erro(msg)


def validar_retorno_operacao_com_lock(status, msg, servidor_acesso, agrupamento, nuvem):
    if status:
        imprimir_ok()
    else:
        imprimir_erro()
        liberar_lock(servidor_acesso, agrupamento, nuvem)
        finalizar_com_erro(msg)


def adquirir_lock(servidor_acesso, agrupamento, nuvem):
    imprimir_acao_corrente('Adquirindo lock')

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
            retorno_cmd = ('O processo {}, '
                           'iniciado em {} '
                           'no servidor {}, '
                           'já está manipulando o agrupamento {} '
                           'na nuvem {}.').format(dados_lock.get('PIDProcesso'),
                                                  dados_lock.get('DataLock'),
                                                  dados_lock.get('HostLock'),
                                                  dados_lock.get(
                                                      'Agrupamento'),
                                                  dados_lock.get('Nuvem')
                                                  )
    validar_retorno_operacao_sem_lock(status, retorno_cmd)


def liberar_lock(servidor_acesso, agrupamento, nuvem):
    imprimir_acao_corrente('Liberando lock')

    cmd = Comando('liberar_lock',
                  lockfile=servidor_acesso.get_caminho_lockfile(
                      agrupamento,
                      nuvem))

    status, _ = cmd.executar(servidor_acesso)
    if status:
        imprimir_ok()
    else:
        imprimir_erro()
        print(formatar_msg_erro(
            'Erro ao liberar o lock: você terá que excluir o arquivo manualmente.'))
