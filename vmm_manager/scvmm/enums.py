"""
Enums do VMM
"""
from enum import Enum


class VMStatusEnum(Enum):
    EM_EXECUCAO = 0
    DESLIGADA = 1


class SCJobStatusEnum(Enum):
    EM_EXECUCAO = 1
    FALHA = 3
    CANCELADO = 4
    SUCESSO = 5
    SUCESSO_COM_AVISO = 6
