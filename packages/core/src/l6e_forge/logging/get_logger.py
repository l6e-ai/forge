from l6e_forge.logging.base import ILogger
from l6e_forge.logging.print_logger import PrintLogger

default_logger: ILogger = PrintLogger()


def get_logger() -> ILogger:
    return default_logger


def set_logger(logger: ILogger) -> None:
    default_logger = logger
