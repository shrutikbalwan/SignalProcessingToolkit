"""Optional callback-based audio acquisition adapter.

The module defines dependency-injection protocols without importing sounddevice.
``SoundDeviceBackend`` imports it only when a device operation is requested.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Any, Protocol, cast

import numpy as np

from signal_processing_toolkit.streaming.buffer import (
    BoundedRingBuffer,
    BufferClosedError,
    OverflowPolicy,
)
from signal_processing_toolkit.streaming.model import ChannelMetadata, StreamChunk
from signal_processing_toolkit.streaming.sources import AudioSource


@dataclass(frozen=True, slots=True)
class AudioDevice:
    index: int
    name: str
    maximum_input_channels: int
    maximum_output_channels: int
    default_sampling_rate: float

    @property
    def supports_input(self) -> bool:
        return self.maximum_input_channels > 0

    @property
    def supports_output(self) -> bool:
        return self.maximum_output_channels > 0


@dataclass(frozen=True, slots=True)
class AudioStreamConfig:
    sampling_rate: float = 44_100.0
    channels: int = 1
    dtype: str = "float32"
    block_size: int = 1024
    device: int | str | None = None
    queue_capacity: int = 8
    channel_names: tuple[str, ...] | None = None
    units: str = "FS"

    def __post_init__(self) -> None:
        if not np.isfinite(self.sampling_rate) or self.sampling_rate <= 0:
            raise ValueError("sampling_rate must be finite and positive")
        if isinstance(self.channels, bool) or self.channels < 1:
            raise ValueError("channels must be a positive integer")
        if isinstance(self.block_size, bool) or self.block_size < 1:
            raise ValueError("block_size must be a positive integer")
        if isinstance(self.queue_capacity, bool) or self.queue_capacity < 1:
            raise ValueError("queue_capacity must be a positive integer")
        dtype = np.dtype(self.dtype)
        if dtype.kind not in "fiu" or dtype == np.dtype(bool):
            raise ValueError("audio dtype must be a real integer or floating dtype")
        if self.channel_names is not None and len(self.channel_names) != self.channels:
            raise ValueError("channel_names must contain one name per channel")


@dataclass(frozen=True, slots=True)
class AudioSourceMetrics:
    callback_blocks: int
    input_overflows: int
    output_underflows: int
    dropped_blocks: int


class AudioInputStream(Protocol):
    def start(self) -> None: ...

    def stop(self) -> None: ...

    def close(self) -> None: ...


AudioCallback = Callable[[np.ndarray, int, Any, Any], None]


class AudioBackend(Protocol):
    def query_devices(self) -> Sequence[Mapping[str, Any]]: ...

    def create_input_stream(
        self,
        *,
        callback: AudioCallback,
        sampling_rate: float,
        channels: int,
        dtype: str,
        block_size: int,
        device: int | str | None,
    ) -> AudioInputStream: ...


class SoundDeviceBackend:
    """Lazy adapter for the optional sounddevice dependency."""

    @staticmethod
    def _module():
        try:
            import sounddevice
        except ModuleNotFoundError as error:
            raise RuntimeError(
                "Audio acquisition requires the 'audio' extra: "
                'pip install "signal-processing-toolkit[audio]"'
            ) from error
        return sounddevice

    def query_devices(self) -> Sequence[Mapping[str, Any]]:
        return cast(Sequence[Mapping[str, Any]], self._module().query_devices())

    def create_input_stream(
        self,
        *,
        callback: AudioCallback,
        sampling_rate: float,
        channels: int,
        dtype: str,
        block_size: int,
        device: int | str | None,
    ) -> AudioInputStream:
        return cast(
            AudioInputStream,
            self._module().InputStream(
                samplerate=sampling_rate,
                channels=channels,
                dtype=dtype,
                blocksize=block_size,
                device=device,
                callback=callback,
            ),
        )


def enumerate_audio_devices(backend: AudioBackend | None = None) -> tuple[AudioDevice, ...]:
    selected = backend or SoundDeviceBackend()
    return tuple(
        AudioDevice(
            index=index,
            name=str(item["name"]),
            maximum_input_channels=int(item.get("max_input_channels", 0)),
            maximum_output_channels=int(item.get("max_output_channels", 0)),
            default_sampling_rate=float(item.get("default_samplerate", 0.0)),
        )
        for index, item in enumerate(selected.query_devices())
    )


class SoundDeviceAudioSource(AudioSource):
    """Non-blocking callback audio source with a bounded handoff queue."""

    def __init__(
        self,
        config: AudioStreamConfig | None = None,
        *,
        backend: AudioBackend | None = None,
    ) -> None:
        self.config = config or AudioStreamConfig()
        self.backend = backend or SoundDeviceBackend()
        self._buffer: BoundedRingBuffer[StreamChunk] = BoundedRingBuffer(
            self.config.queue_capacity, OverflowPolicy.DROP_OLDEST
        )
        self._stream: AudioInputStream | None = None
        self._sequence = 0
        self._callback_blocks = 0
        self._input_overflows = 0
        self._output_underflows = 0
        self._lock = threading.Lock()
        self._closed = False

    @property
    def exhausted(self) -> bool:
        return self._closed

    def configure(self, settings: Mapping[str, Any] | None = None) -> None:
        if settings:
            self.config = replace(self.config, **dict(settings))
        self._replace_buffer()

    def _replace_buffer(self) -> None:
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        self._buffer.close()
        self._buffer = BoundedRingBuffer(self.config.queue_capacity, OverflowPolicy.DROP_OLDEST)
        self._closed = False

    @staticmethod
    def _status_flag(status: Any, name: str) -> bool:
        return bool(getattr(status, name, False)) if status is not None else False

    @staticmethod
    def _device_time(time_info: Any) -> float:
        if isinstance(time_info, Mapping):
            value = time_info.get("inputBufferAdcTime", time.time())
        else:
            value = getattr(time_info, "inputBufferAdcTime", time.time())
        return float(value)

    def _callback(self, input_data: np.ndarray, frames: int, time_info: Any, status: Any) -> None:
        values = np.array(input_data, copy=True)
        if values.ndim == 1:
            values = values[:, np.newaxis]
        if frames != values.shape[0] or values.shape[1] != self.config.channels:
            return
        with self._lock:
            sequence = self._sequence
            self._sequence += 1
            self._callback_blocks += 1
            overflow = self._status_flag(status, "input_overflow")
            underflow = self._status_flag(status, "output_underflow")
            self._input_overflows += int(overflow)
            self._output_underflows += int(underflow)
        names = self.config.channel_names or tuple(
            f"audio_{index + 1}" for index in range(self.config.channels)
        )
        chunk = StreamChunk(
            values,
            self.config.sampling_rate,
            tuple(ChannelMetadata(name, self.config.units) for name in names),
            sequence,
            self._device_time(time_info),
            time.time(),
            {
                "source": "audio",
                "input_overflow": overflow,
                "output_underflow": underflow,
                "dtype": self.config.dtype,
            },
        )
        try:
            self._buffer.put(chunk)
        except BufferClosedError:
            if not self._closed:
                raise

    def _ensure_started(self) -> None:
        if self._stream is not None:
            return
        self._stream = self.backend.create_input_stream(
            callback=self._callback,
            sampling_rate=self.config.sampling_rate,
            channels=self.config.channels,
            dtype=self.config.dtype,
            block_size=self.config.block_size,
            device=self.config.device,
        )
        self._stream.start()

    def read(self, cancel: threading.Event) -> StreamChunk | None:
        if self._closed:
            return None
        self._ensure_started()
        while not cancel.is_set() and not self._closed:
            chunk = self._buffer.get(timeout=0.05)
            if chunk is not None:
                return chunk
        return None

    def reset(self) -> None:
        self._replace_buffer()
        with self._lock:
            self._sequence = 0
            self._callback_blocks = 0
            self._input_overflows = 0
            self._output_underflows = 0

    def close(self) -> None:
        self._closed = True
        self._buffer.close()
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

    @property
    def metrics(self) -> AudioSourceMetrics:
        with self._lock:
            return AudioSourceMetrics(
                self._callback_blocks,
                self._input_overflows,
                self._output_underflows,
                self._buffer.snapshot.dropped,
            )
