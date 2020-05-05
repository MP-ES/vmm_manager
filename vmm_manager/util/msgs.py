"""
Módulo com funções que tratam da impressão de informações
"""
import sys
from datetime import datetime
from pytz import timezone


def formatar_msg_aviso(msg):
    return '\033[93m{}\033[0m'.format(msg)


def formatar_msg_erro(msg):
    return '\033[91m{}\033[0m'.format(msg)


def finalizar_com_erro(msg_erro):
    print(formatar_msg_erro('\nErro ao executar operação:\n{}'.format(msg_erro)))
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
