import logging

from src.config import settings
from src.core.logging_config import setup_logging

_initialized = False


def init_logger() -> None:
    global _initialized
    if not _initialized:
        setup_logging(settings.logs_dir, settings.debug)
        _initialized = True


def get_logger(name: str | None = None) -> logging.Logger:
    init_logger()
    if name is None:
        import inspect

        current = inspect.currentframe()
        if current is None:
            name = "spt"
        else:
            frame = current.f_back
            name = frame.f_globals.get("__name__", "spt") if frame else "spt"
    return logging.getLogger(name)


class LoggerMixin:
    @property
    def logger(self) -> logging.Logger:
        if not hasattr(self, "_logger"):
            self._logger = get_logger(self.__class__.__module__ + "." + self.__class__.__name__)
        return self._logger
