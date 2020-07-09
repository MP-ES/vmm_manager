"""
Módulo com funções que tratam da impressão de informações
"""
import sys
from datetime import datetime
from pytz import timezone


def formatar_msg_aviso(msg):
    return f'\033[93m{msg}\033[0m'


def formatar_msg_erro(msg):
    return f'\033[91m{msg}\033[0m'


def finalizar_com_erro(msg_erro):
    print(formatar_msg_erro(f'\nErro ao executar operação:\n{msg_erro}'))
    sys.exit(1)


def imprimir_ok(ocultar_progresso):
    if not ocultar_progresso:
        print('[OK]')


def imprimir_erro(ocultar_progresso):
    if not ocultar_progresso:
        print('[ERRO]')


def imprimir_acao_corrente(acao, ocultar_progresso):
    if not ocultar_progresso:
        print('{:<60}'.format(acao + '...'), end='', flush=True)


def get_str_data_formatada(formato):
    fuso = timezone('America/Sao_Paulo')
    return datetime.now().astimezone(fuso).strftime(formato)
