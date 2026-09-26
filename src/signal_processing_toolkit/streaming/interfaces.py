from __future__ import annotations

from collections.abc import Mapping
from threading import Event
from typing import Any, Protocol, runtime_checkable

from signal_processing_toolkit.streaming.model import StreamChunk


@runtime_checkable
class ProcessingNode(Protocol):
    """Typed transformation contract for stateless or stateful nodes."""

    def configure(self, settings: Mapping[str, Any] | None = None) -> None: ...

    def process(self, chunk: StreamChunk) -> StreamChunk | None: ...

    def reset(self) -> None: ...


@runtime_checkable
class StreamSource(Protocol):
    @property
    def exhausted(self) -> bool: ...

    def configure(self, settings: Mapping[str, Any] | None = None) -> None: ...

    def read(self, cancel: Event) -> StreamChunk | None: ...

    def reset(self) -> None: ...

    def close(self) -> None: ...


@runtime_checkable
class StreamSink(Protocol):
    def consume(self, chunk: StreamChunk) -> None: ...

    def reset(self) -> None: ...

    def close(self) -> None: ...


class StatelessNode:
    """Convenience base implementing no-op lifecycle methods."""

    def configure(self, settings: Mapping[str, Any] | None = None) -> None:
        del settings

    def reset(self) -> None:
        return

    def flush(self) -> StreamChunk | None:
        return None
