"""
Módulo com definições e funções úteis
"""

import sys
import os
import platform
import json
from datetime import datetime
from pytz import timezone
from app.comando import Comando

# Campos customizado no VMM
CAMPO_AGRUPAMENTO = ('VMM_MANAGER_AGRUPAMENTO',
                     'Agrupamento da máquina (script vmm_manager).')

CAMPO_ID = ('VMM_MANAGER_ID',
            'Nome da VM informada no inventário (script vmm_manager).')

CAMPO_IMAGEM = ('VMM_MANAGER_IMAGEM',
                'Imagem utilizada para criar a VM (script vmm_manager).')

CAMPO_REGIAO = ('VMM_MANAGER_REGIAO',
                'Região na qual a VM foi criada (script vmm_manager).')


def formatar_msg_aviso(msg):
    return '\033[93m{}\033[0m'.format(msg)


def formatar_msg_erro(msg):
    return '\033[91m{}\033[0m'.format(msg)


def finalizar_com_erro(msg_erro):
    print(formatar_msg_erro('\nErro ao executar operação:\n{}'.format(msg_erro)))
    sys.exit(1)


def imprimir_ok():
    print('[OK]')


def imprimir_erro():
    print('[ERRO]')


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


def imprimir_acao_corrente(acao):
    print('{:<60}'.format(acao + '...'), end='', flush=True)


def get_str_data_formatada(formato):
    fuso = timezone('America/Sao_Paulo')
    return datetime.now().astimezone(fuso).strftime(formato)


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
