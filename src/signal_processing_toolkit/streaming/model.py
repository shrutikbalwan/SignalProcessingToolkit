from __future__ import annotations

import time
from collections.abc import Mapping
from dataclasses import dataclass, field
from numbers import Integral
from types import MappingProxyType
from typing import Any

import numpy as np


@dataclass(frozen=True, slots=True)
class ChannelMetadata:
    """Identity and physical unit for one sample channel."""

    name: str
    unit: str = ""

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Channel names cannot be empty")


@dataclass(frozen=True, slots=True)
class SessionEvent:
    """Timestamped acquisition or connection event stored with a session."""

    kind: str
    host_timestamp: float = field(default_factory=time.time)
    device_timestamp: float | None = None
    details: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.kind.strip():
            raise ValueError("event kind cannot be empty")
        if not np.isfinite(self.host_timestamp):
            raise ValueError("event host timestamp must be finite")
        if self.device_timestamp is not None and not np.isfinite(self.device_timestamp):
            raise ValueError("event device timestamp must be finite when provided")
        object.__setattr__(self, "details", MappingProxyType(dict(self.details)))


@dataclass(frozen=True, slots=True)
class StreamChunk:
    """One immutable-by-convention, sample-major block in a stream.

    Samples have shape ``(samples,)`` for mono data or ``(samples, channels)``.
    Sources must not mutate an array after publishing it. Processing nodes create
    a new chunk with :meth:`with_samples`, preserving sequence and timestamps.
    Timestamps are seconds on the source device and host Unix clocks respectively.
    """

    samples: np.ndarray
    sampling_rate: float
    channels: tuple[ChannelMetadata, ...]
    sequence: int
    device_timestamp: float
    host_timestamp: float = field(default_factory=time.time)
    attributes: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        data = np.asarray(self.samples)
        if data.ndim not in (1, 2):
            raise ValueError("Stream samples must be sample-major one- or two-dimensional data")
        if data.ndim == 2 and data.shape[1] == 0:
            raise ValueError("A multichannel stream must have at least one channel")
        if not (
            np.issubdtype(data.dtype, np.integer)
            or np.issubdtype(data.dtype, np.floating)
            or np.issubdtype(data.dtype, np.complexfloating)
        ) or np.issubdtype(data.dtype, np.bool_):
            raise TypeError("Stream samples must have a real or complex numeric dtype")
        if not np.all(np.isfinite(data)):
            raise ValueError("Stream samples must contain only finite values")
        if not np.isfinite(self.sampling_rate) or self.sampling_rate <= 0:
            raise ValueError("sampling_rate must be finite and positive")
        if (
            isinstance(self.sequence, bool)
            or not isinstance(self.sequence, Integral)
            or self.sequence < 0
        ):
            raise ValueError("sequence must be a non-negative integer")
        if not np.isfinite(self.device_timestamp) or not np.isfinite(self.host_timestamp):
            raise ValueError("device and host timestamps must be finite")
        channel_count = 1 if data.ndim == 1 else data.shape[1]
        if len(self.channels) != channel_count:
            raise ValueError(
                f"Expected metadata for {channel_count} channel(s), received {len(self.channels)}"
            )
        object.__setattr__(self, "samples", data)
        object.__setattr__(self, "attributes", MappingProxyType(dict(self.attributes)))

    @property
    def sample_count(self) -> int:
        return int(self.samples.shape[0])

    @property
    def channel_count(self) -> int:
        return 1 if self.samples.ndim == 1 else int(self.samples.shape[1])

    @property
    def duration(self) -> float:
        return self.sample_count / self.sampling_rate

    def with_samples(
        self,
        samples: np.ndarray,
        *,
        sampling_rate: float | None = None,
        channels: tuple[ChannelMetadata, ...] | None = None,
        attributes: Mapping[str, Any] | None = None,
    ) -> StreamChunk:
        combined = dict(self.attributes)
        if attributes:
            combined.update(attributes)
        return StreamChunk(
            samples=samples,
            sampling_rate=self.sampling_rate if sampling_rate is None else sampling_rate,
            channels=self.channels if channels is None else channels,
            sequence=self.sequence,
            device_timestamp=self.device_timestamp,
            host_timestamp=self.host_timestamp,
            attributes=combined,
        )
