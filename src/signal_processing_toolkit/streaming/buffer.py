from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass
from enum import StrEnum
from threading import Condition


class OverflowPolicy(StrEnum):
    """Behavior when a bounded buffer has no free slot."""

    BLOCK = "block"
    DROP_OLDEST = "drop_oldest"
    DROP_NEWEST = "drop_newest"
    RAISE = "raise"


class BufferClosedError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class BufferSnapshot:
    capacity: int
    depth: int
    maximum_depth: int
    accepted: int
    consumed: int
    dropped: int


class BoundedRingBuffer[T]:
    """Lock-safe FIFO with bounded memory and an explicit overflow policy."""

    def __init__(self, capacity: int, policy: OverflowPolicy = OverflowPolicy.DROP_OLDEST) -> None:
        if isinstance(capacity, bool) or capacity < 1:
            raise ValueError("capacity must be a positive integer")
        self.capacity = int(capacity)
        self.policy = OverflowPolicy(policy)
        self._items: deque[T] = deque()
        self._condition = Condition()
        self._closed = False
        self._maximum_depth = 0
        self._accepted = 0
        self._consumed = 0
        self._dropped = 0

    def put(self, item: T, timeout: float | None = None) -> bool:
        """Add an item, returning false only when DROP_NEWEST rejects it."""
        deadline = None if timeout is None else time.monotonic() + max(timeout, 0.0)
        with self._condition:
            if self._closed:
                raise BufferClosedError("buffer is closed")
            while len(self._items) >= self.capacity:
                if self.policy is OverflowPolicy.DROP_OLDEST:
                    self._items.popleft()
                    self._dropped += 1
                    break
                if self.policy is OverflowPolicy.DROP_NEWEST:
                    self._dropped += 1
                    return False
                if self.policy is OverflowPolicy.RAISE:
                    raise BufferError("bounded ring buffer is full")
                remaining = None if deadline is None else deadline - time.monotonic()
                if remaining is not None and remaining <= 0:
                    return False
                self._condition.wait(remaining)
                if self._closed:
                    raise BufferClosedError("buffer is closed")
            self._items.append(item)
            self._accepted += 1
            self._maximum_depth = max(self._maximum_depth, len(self._items))
            self._condition.notify_all()
            return True

    def get(self, timeout: float | None = None) -> T | None:
        deadline = None if timeout is None else time.monotonic() + max(timeout, 0.0)
        with self._condition:
            while not self._items:
                if self._closed:
                    return None
                remaining = None if deadline is None else deadline - time.monotonic()
                if remaining is not None and remaining <= 0:
                    return None
                self._condition.wait(remaining)
            item = self._items.popleft()
            self._consumed += 1
            self._condition.notify_all()
            return item

    def clear(self, *, reset_metrics: bool = False) -> None:
        with self._condition:
            self._items.clear()
            if reset_metrics:
                self._maximum_depth = self._accepted = self._consumed = self._dropped = 0
            self._condition.notify_all()

    def close(self) -> None:
        with self._condition:
            self._closed = True
            self._condition.notify_all()

    def reopen(self) -> None:
        with self._condition:
            self._closed = False
            self._condition.notify_all()

    @property
    def snapshot(self) -> BufferSnapshot:
        with self._condition:
            return BufferSnapshot(
                self.capacity,
                len(self._items),
                self._maximum_depth,
                self._accepted,
                self._consumed,
                self._dropped,
            )
