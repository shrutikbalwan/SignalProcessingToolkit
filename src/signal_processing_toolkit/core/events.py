from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)

EventHandler = Callable[..., None]


class EventBus:
    def __init__(self) -> None:
        self._subscribers: dict[str, list[EventHandler]] = defaultdict(list)

    def subscribe(self, event: str, handler: EventHandler) -> None:
        if handler not in self._subscribers[event]:
            self._subscribers[event].append(handler)
            logger.debug("Subscribed %s to '%s'", handler.__name__, event)

    def unsubscribe(self, event: str, handler: EventHandler) -> None:
        self._subscribers[event] = [h for h in self._subscribers[event] if h is not handler]
        logger.debug("Unsubscribed %s from '%s'", handler.__name__, event)

    def publish(self, event: str, **kwargs: Any) -> None:
        logger.debug("Publishing event '%s' with %s", event, kwargs)
        for handler in self._subscribers.get(event, []):
            try:
                handler(**kwargs)
            except Exception:
                logger.exception("Handler %s failed for event '%s'", handler.__name__, event)

    def clear(self) -> None:
        self._subscribers.clear()
