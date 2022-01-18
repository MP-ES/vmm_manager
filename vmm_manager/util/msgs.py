"""
Módulo com funções que tratam da impressão de informações
"""
import sys
from datetime import datetime
from pytz import timezone

# Parâmetros globais de escrita
_EXIBIR_CORES = True


def set_parametros_globais_escrita(exibir_cores):
    global _EXIBIR_CORES  # pylint: disable=global-statement
    _EXIBIR_CORES = exibir_cores


def formatar_msg_aviso(msg):
    msg_inicial = 'AVISO'
    if _EXIBIR_CORES:
        return f'\033[93m{msg_inicial}: {msg}\033[0m'
    return f'{msg_inicial}: {msg}'


def formatar_msg_erro(msg):
    if _EXIBIR_CORES:
        return f'\033[91m{msg}\033[0m'
    return msg


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
        print(f'{acao:<57}...', end='', flush=True)


def get_str_data_formatada(formato):
    fuso = timezone('America/Sao_Paulo')
    return datetime.now().astimezone(fuso).strftime(formato)
