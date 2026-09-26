from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from signal_processing_toolkit.models.signal import Signal, SignalMetadata


@dataclass
class AudioSignal:
    signal: Signal
    channels: int = 1
    bit_depth: int = 16
    audio_format: str = "wav"

    def __post_init__(self) -> None:
        if self.channels < 1:
            raise ValueError(f"Invalid channel count: {self.channels}")
        if self.channels != self.signal.n_channels:
            raise ValueError(
                f"Audio channel count {self.channels} does not match signal data "
                f"({self.signal.n_channels})"
            )

    @property
    def samples(self) -> np.ndarray:
        return self.signal.time_data

    @property
    def sampling_rate(self) -> float:
        return self.signal.sampling_rate

    @property
    def duration(self) -> float:
        return self.signal.duration

    @property
    def metadata(self) -> SignalMetadata:
        return self.signal.metadata

    @classmethod
    def from_signal(
        cls, signal: Signal, channels: int | None = None, bit_depth: int = 16
    ) -> AudioSignal:
        return cls(
            signal=signal,
            channels=signal.n_channels if channels is None else channels,
            bit_depth=bit_depth,
        )

    def to_mono(self) -> AudioSignal:
        if self.channels == 1:
            return self
        mono_data = np.mean(self.samples, axis=Signal.CHANNEL_AXIS)
        return AudioSignal(
            signal=self.signal.updated(
                time_data=mono_data,
                channel_names=("mono",),
                units=(self.signal.units[0],),
                operation="mixdown_to_mono",
            ),
            channels=1,
            bit_depth=self.bit_depth,
        )

    def copy(self) -> AudioSignal:
        return AudioSignal(
            signal=self.signal.copy(),
            channels=self.channels,
            bit_depth=self.bit_depth,
            audio_format=self.audio_format,
        )
