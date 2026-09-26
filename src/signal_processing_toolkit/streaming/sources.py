from __future__ import annotations

import time
from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping
from threading import Event
from typing import Any

import numpy as np

from signal_processing_toolkit.streaming.model import ChannelMetadata, StreamChunk


class SyntheticSource:
    """Paced, phase-continuous synthetic source for tests and live monitoring."""

    def __init__(
        self,
        *,
        sampling_rate: float = 44_100.0,
        chunk_size: int = 1024,
        frequency: float = 440.0,
        amplitude: float = 1.0,
        waveform: str = "sine",
        real_time: bool = True,
        seed: int = 0,
    ) -> None:
        self.sampling_rate = float(sampling_rate)
        self.chunk_size = int(chunk_size)
        self.frequency = float(frequency)
        self.amplitude = float(amplitude)
        self.waveform = waveform
        self.real_time = real_time
        self._rng = np.random.default_rng(seed)
        self._sequence = 0
        self._sample_index = 0
        self._next_deadline: float | None = None
        self.configure()

    @property
    def exhausted(self) -> bool:
        return False

    def configure(self, settings: Mapping[str, Any] | None = None) -> None:
        if settings:
            for name in ("sampling_rate", "chunk_size", "frequency", "amplitude", "waveform"):
                if name in settings:
                    setattr(self, name, settings[name])
        if not np.isfinite(self.sampling_rate) or self.sampling_rate <= 0:
            raise ValueError("sampling_rate must be finite and positive")
        if self.chunk_size < 1:
            raise ValueError("chunk_size must be positive")
        if self.waveform not in {"sine", "square", "sawtooth", "noise"}:
            raise ValueError("waveform must be sine, square, sawtooth, or noise")

    def read(self, cancel: Event) -> StreamChunk | None:
        duration = self.chunk_size / self.sampling_rate
        if self.real_time:
            now = time.monotonic()
            deadline = now if self._next_deadline is None else self._next_deadline
            if cancel.wait(max(0.0, deadline - now)):
                return None
            self._next_deadline = max(deadline, time.monotonic()) + duration
        start = self._sample_index / self.sampling_rate
        phase = (
            2.0
            * np.pi
            * self.frequency
            * (self._sample_index + np.arange(self.chunk_size))
            / self.sampling_rate
        )
        samples: np.ndarray
        if self.waveform == "sine":
            samples = self.amplitude * np.sin(phase)
        elif self.waveform == "square":
            samples = self.amplitude * np.where(np.sin(phase) >= 0, 1.0, -1.0)
        elif self.waveform == "sawtooth":
            cycles = phase / (2.0 * np.pi)
            samples = self.amplitude * (2.0 * (cycles - np.floor(cycles + 0.5)))
        else:
            samples = self.amplitude * self._rng.standard_normal(self.chunk_size)
        chunk = StreamChunk(
            samples,
            self.sampling_rate,
            (ChannelMetadata("synthetic", "FS"),),
            self._sequence,
            start,
            time.time(),
            {"source": "synthetic", "waveform": self.waveform},
        )
        self._sequence += 1
        self._sample_index += self.chunk_size
        return chunk

    def reset(self) -> None:
        self._sequence = 0
        self._sample_index = 0
        self._next_deadline = None

    def close(self) -> None:
        self._next_deadline = None


class AudioSource(ABC):
    """Dependency-free audio source abstraction.

    An adapter in the optional audio extra may feed device callback blocks into
    this contract; importing the streaming engine never imports sounddevice.
    """

    @property
    @abstractmethod
    def exhausted(self) -> bool: ...

    @abstractmethod
    def configure(self, settings: Mapping[str, Any] | None = None) -> None: ...

    @abstractmethod
    def read(self, cancel: Event) -> StreamChunk | None: ...

    @abstractmethod
    def reset(self) -> None: ...

    @abstractmethod
    def close(self) -> None: ...


class ReplaySource:
    """Deterministically replay recorded chunks in their original order."""

    def __init__(self, chunks: Iterable[StreamChunk], *, paced: bool = False) -> None:
        self._chunks = tuple(chunks)
        self.paced = paced
        self._index = 0
        self._first_device_time = self._chunks[0].device_timestamp if self._chunks else 0.0
        self._started: float | None = None

    @property
    def exhausted(self) -> bool:
        return self._index >= len(self._chunks)

    def configure(self, settings: Mapping[str, Any] | None = None) -> None:
        if settings and "paced" in settings:
            self.paced = bool(settings["paced"])

    def read(self, cancel: Event) -> StreamChunk | None:
        if self.exhausted:
            return None
        chunk = self._chunks[self._index]
        if self.paced:
            if self._started is None:
                self._started = time.monotonic()
            target = self._started + chunk.device_timestamp - self._first_device_time
            if cancel.wait(max(0.0, target - time.monotonic())):
                return None
        self._index += 1
        return chunk

    def reset(self) -> None:
        self._index = 0
        self._started = None

    def close(self) -> None:
        return
