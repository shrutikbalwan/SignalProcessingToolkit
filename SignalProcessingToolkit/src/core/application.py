from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class ApplicationLifecycle:
    def __init__(self) -> None:
        self._initialized = False

    def initialize(self) -> None:
        logger.debug("Application lifecycle initializing")
        self._initialized = True

    def shutdown(self) -> None:
        logger.debug("Application lifecycle shutting down")
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        return self._initialized
