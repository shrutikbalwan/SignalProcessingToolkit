from __future__ import annotations

import json
from collections import deque
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock
from typing import Any

import numpy as np

from signal_processing_toolkit.streaming.model import ChannelMetadata, SessionEvent, StreamChunk


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, str | bool | int | float):
        return value
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, tuple | list):
        return [_json_safe(item) for item in value]
    if isinstance(value, np.generic):
        return value.item()
    return repr(value)


@dataclass(frozen=True, slots=True)
class RecordedSession:
    chunks: tuple[StreamChunk, ...]
    connection_events: tuple[SessionEvent, ...] = ()
    pipeline_configuration: Mapping[str, Any] = field(default_factory=dict)
    stream_name: str = "processed"

    def __post_init__(self) -> None:
        if not self.stream_name.strip():
            raise ValueError("stream_name cannot be empty")
        object.__setattr__(self, "pipeline_configuration", dict(self.pipeline_configuration))

    def save(self, path: str | Path) -> None:
        """Store samples and timing without pickle-dependent object arrays."""
        destination = Path(path)
        manifest: list[dict[str, Any]] = []
        arrays: dict[str, np.ndarray] = {}
        for index, chunk in enumerate(self.chunks):
            key = f"samples_{index}"
            arrays[key] = chunk.samples
            manifest.append(
                {
                    "key": key,
                    "sampling_rate": chunk.sampling_rate,
                    "channels": [
                        {"name": channel.name, "unit": channel.unit} for channel in chunk.channels
                    ],
                    "sequence": chunk.sequence,
                    "device_timestamp": chunk.device_timestamp,
                    "host_timestamp": chunk.host_timestamp,
                    "attributes": _json_safe(chunk.attributes),
                }
            )
        session_metadata = {
            "version": 2,
            "stream_name": self.stream_name,
            "pipeline_configuration": _json_safe(self.pipeline_configuration),
            "connection_events": [
                {
                    "kind": event.kind,
                    "host_timestamp": event.host_timestamp,
                    "device_timestamp": event.device_timestamp,
                    "details": _json_safe(event.details),
                }
                for event in self.connection_events
            ],
            "chunks": manifest,
        }
        arrays["manifest"] = np.asarray(json.dumps(session_metadata))
        with destination.open("wb") as stream:
            saver: Any = np.savez_compressed
            saver(stream, **arrays)

    @classmethod
    def load(cls, path: str | Path) -> RecordedSession:
        with np.load(Path(path), allow_pickle=False) as archive:
            stored = json.loads(str(archive["manifest"]))
            if isinstance(stored, list):
                manifest = stored
                metadata: dict[str, Any] = {}
            else:
                metadata = stored
                manifest = metadata.get("chunks", [])
            chunks = tuple(
                StreamChunk(
                    np.array(archive[item["key"]], copy=True),
                    item["sampling_rate"],
                    tuple(ChannelMetadata(**channel) for channel in item["channels"]),
                    item["sequence"],
                    item["device_timestamp"],
                    item["host_timestamp"],
                    {"source": "recording", **item.get("attributes", {})},
                )
                for item in manifest
            )
        events = tuple(
            SessionEvent(
                item["kind"],
                item["host_timestamp"],
                item.get("device_timestamp"),
                item.get("details", {}),
            )
            for item in metadata.get("connection_events", [])
        )
        return cls(
            chunks,
            events,
            metadata.get("pipeline_configuration", {}),
            metadata.get("stream_name", "processed"),
        )

    def replay_source(self, *, paced: bool = False):
        """Create a source that replays these chunks through any pipeline."""
        from signal_processing_toolkit.streaming.sources import ReplaySource

        return ReplaySource(self.chunks, paced=paced)


class RecorderSink:
    def __init__(
        self,
        *,
        maximum_chunks: int | None = None,
        stream_name: str = "processed",
    ) -> None:
        if maximum_chunks is not None and maximum_chunks < 1:
            raise ValueError("maximum_chunks must be positive when provided")
        self.maximum_chunks = maximum_chunks
        if not stream_name.strip():
            raise ValueError("stream_name cannot be empty")
        self.stream_name = stream_name
        self._chunks: deque[StreamChunk] = deque(maxlen=maximum_chunks)
        self._events: list[SessionEvent] = []
        self._pipeline_configuration: dict[str, Any] = {}
        self._lock = Lock()

    def consume(self, chunk: StreamChunk) -> None:
        recorded = chunk.with_samples(np.array(chunk.samples, copy=True))
        with self._lock:
            self._chunks.append(recorded)

    @property
    def session(self) -> RecordedSession:
        with self._lock:
            return RecordedSession(
                tuple(self._chunks),
                tuple(self._events),
                dict(self._pipeline_configuration),
                self.stream_name,
            )

    def record_events(self, events: Iterable[SessionEvent]) -> None:
        with self._lock:
            self._events.extend(events)

    def set_pipeline_configuration(self, configuration: Mapping[str, Any]) -> None:
        with self._lock:
            self._pipeline_configuration = dict(configuration)

    def reset(self) -> None:
        with self._lock:
            self._chunks.clear()
            self._events.clear()

    def close(self) -> None:
        return


class PlotSink:
    """Bounded rolling samples for incremental GUI curve updates."""

    def __init__(
        self,
        maximum_samples: int = 8192,
        callback: Callable[[StreamChunk], None] | None = None,
    ) -> None:
        if maximum_samples < 1:
            raise ValueError("maximum_samples must be positive")
        self.maximum_samples = int(maximum_samples)
        self.callback = callback
        self._chunks: deque[StreamChunk] = deque()
        self._sample_count = 0
        self._lock = Lock()

    def consume(self, chunk: StreamChunk) -> None:
        with self._lock:
            self._chunks.append(chunk)
            self._sample_count += chunk.sample_count
            while (
                self._chunks
                and self._sample_count - self._chunks[0].sample_count >= self.maximum_samples
            ):
                self._sample_count -= self._chunks.popleft().sample_count
        if self.callback is not None:
            self.callback(chunk)

    def snapshot(self) -> tuple[np.ndarray, float]:
        with self._lock:
            chunks = tuple(self._chunks)
        if not chunks:
            return np.empty(0), 1.0
        values = np.concatenate([chunk.samples for chunk in chunks], axis=0)
        return values[-self.maximum_samples :], chunks[-1].sampling_rate

    def reset(self) -> None:
        with self._lock:
            self._chunks.clear()
            self._sample_count = 0

    def close(self) -> None:
        self.reset()


class CallbackSink:
    def __init__(self, callback: Callable[[StreamChunk], None]) -> None:
        self.callback = callback

    def consume(self, chunk: StreamChunk) -> None:
        self.callback(chunk)

    def reset(self) -> None:
        return

    def close(self) -> None:
        return
