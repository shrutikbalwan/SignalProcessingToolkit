"""Threaded adapter for any streaming source implementing ``StreamSource``."""

from __future__ import annotations

from collections import deque
from collections.abc import Callable
from threading import Event, Lock, Thread
from typing import Any

from signal_processing_toolkit.streaming.model import StreamChunk


class AcquisitionService:
    """Read a source off the UI thread and expose bounded polling to Qt."""

    def __init__(self, source: Any, max_queue: int = 32) -> None:
        self.source = source
        self.max_queue = max_queue
        self._queue: deque[StreamChunk] = deque(maxlen=max_queue)
        self._lock = Lock()
        self._cancel = Event()
        self._thread: Thread | None = None
        self.dropped_chunks = 0
        self.running = False
        self.error: BaseException | None = None
        self._events: list[Callable[[str], None]] = []

    def subscribe_events(self, callback: Callable[[str], None]) -> None:
        if callback not in self._events:
            self._events.append(callback)

    def start(self) -> None:
        if self.running:
            return
        self._cancel.clear()
        self.error = None
        self.running = True
        self._thread = Thread(target=self._run, name="spt-dashboard-source", daemon=True)
        self._thread.start()

    def _run(self) -> None:
        try:
            while not self._cancel.is_set():
                chunk = self.source.read(self._cancel)
                if chunk is None:
                    if getattr(self.source, "exhausted", False):
                        break
                    continue
                with self._lock:
                    if len(self._queue) >= self.max_queue:
                        self._queue.popleft()
                        self.dropped_chunks += 1
                    self._queue.append(chunk)
        except BaseException as error:  # surfaced by poll, never swallowed
            self.error = error
            for callback in tuple(self._events):
                callback(str(error))
        finally:
            self.running = False

    def poll(self, limit: int = 4) -> list[StreamChunk]:
        with self._lock:
            chunks = [self._queue.popleft() for _ in range(min(limit, len(self._queue)))]
        return chunks

    @property
    def queue_depth(self) -> int:
        with self._lock:
            return len(self._queue)

    def stop(self) -> None:
        self._cancel.set()
        close = getattr(self.source, "close", None)
        if callable(close):
            close()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
        self.running = False

    def reset(self) -> None:
        self.stop()
        reset = getattr(self.source, "reset", None)
        if callable(reset):
            reset()
        with self._lock:
            self._queue.clear()
        self.dropped_chunks = 0
        self.error = None
