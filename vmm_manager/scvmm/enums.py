"""
VMM Manager enums.
"""

from enum import Enum


class VMStatusEnum(Enum):
    RUNNING = 0
    POWER_OFF = 1
    UPDATED_WITH_ERROR = 107


class SCJobStatusEnum(Enum):
    RUNNING = 1
    FAILED = 3
    CANCELED = 4
    SUCCESS = 5
    SUCCESS_WITH_WARNING = 6


class SCDiskBusType(Enum):
    SCSI = 'SCSI'
    IDE = 'IDE'


class SCDiskSizeType(Enum):
    FIXED = 'FixedSize'
    DYNAMIC = 'DynamicallyExpanding'
