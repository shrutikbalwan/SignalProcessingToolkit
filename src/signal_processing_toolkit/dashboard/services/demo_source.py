"""Deterministic synthetic source for demos and automated tests."""

from __future__ import annotations

import math
from collections.abc import Callable


class DemoSource:
    def __init__(self, sampling_rate: float = 1_000.0, frequency: float = 100.0) -> None:
        self.sampling_rate = sampling_rate
        self.frequency = frequency
        self.running = False
        self.sequence = 0
        self._phase = 0.0
        self._callbacks: list[Callable[[list[float], int], None]] = []

    def subscribe(self, callback: Callable[[list[float], int], None]) -> None:
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def unsubscribe(self, callback: Callable[[list[float], int], None]) -> None:
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def start(self) -> None:
        self.running = True

    def stop(self) -> None:
        self.running = False

    def reset(self) -> None:
        self.stop()
        self.sequence = 0
        self._phase = 0.0

    def next_chunk(self, size: int = 128) -> list[float]:
        if not self.running:
            return []
        step = 2 * math.pi * self.frequency / self.sampling_rate
        chunk = [math.sin(self._phase + i * step) for i in range(size)]
        self._phase = (self._phase + size * step) % (2 * math.pi)
        self.sequence += 1
        for callback in tuple(self._callbacks):
            callback(chunk, self.sequence)
        return chunk
