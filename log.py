import logging
from enum import Enum
from typeguard import typechecked
from data import uData


@typechecked
class loglevel(Enum):
    CRITICAL = logging.CRITICAL
    ERROR = logging.ERROR
    WARNING = logging.WARNING
    INFO = logging.INFO
    DEBUG = logging.DEBUG
    NOTSET = logging.NOTSET


logging.basicConfig(level=loglevel[uData.setting['loglevel'].upper()].value,
                    datefmt='%m-%d %H:%M',
                    format='%(asctime)s %(levelname)s: %(message)s')
