from __future__ import annotations

from abc import ABC

from src.core.events import EventBus


class BaseController(ABC):  # noqa: B024
    def __init__(self, event_bus: EventBus) -> None:
        self.event_bus = event_bus
        self._connect_events()

    def _connect_events(self) -> None:  # noqa: B027
        pass

    def cleanup(self) -> None:  # noqa: B027
        pass
