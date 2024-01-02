"""
Output messages and formatting.
"""

import sys
from datetime import datetime

from pytz import timezone

# Global variables
_SHOW_COLORS = True


def set_parametros_globais_escrita(no_color):
    global _SHOW_COLORS  # pylint: disable=global-statement
    _SHOW_COLORS = not no_color


def formatar_msg_aviso(msg):
    msg_inicial = 'WARNING'
    if _SHOW_COLORS:
        return f'\033[93m{msg_inicial}: {msg}\033[0m'
    return f'{msg_inicial}: {msg}'


def formatar_msg_erro(msg):
    if _SHOW_COLORS:
        return f'\033[91m{msg}\033[0m'
    return msg


def finalizar_com_erro(msg_erro):
    print(formatar_msg_erro(f'\nOperation error:\n{msg_erro}'))
    sys.exit(1)


def imprimir_ok(ocultar_progresso):
    if not ocultar_progresso:
        if _SHOW_COLORS:
            print('\033[92m[OK]\033[0m')
        else:
            print('[OK]')


def imprimir_erro(ocultar_progresso):
    if not ocultar_progresso:
        if _SHOW_COLORS:
            print('\033[91m[ERR]\033[0m')
        else:
            print('[ERR]')


def imprimir_acao_corrente(acao, ocultar_progresso, max_len=60):
    if not ocultar_progresso:
        print(f'{acao:<{max_len-3}}...', end='', flush=True)


def get_str_data_formatada(formato):
    fuso = timezone('America/Sao_Paulo')
    return datetime.now().astimezone(fuso).strftime(formato)
