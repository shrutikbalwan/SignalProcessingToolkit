from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime

import numpy as np

from src.models.enums import WindowType


@dataclass
class SignalMetadata:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    name: str = "Untitled Signal"
    created_at: datetime = field(default_factory=datetime.now)
    modified_at: datetime = field(default_factory=datetime.now)
    description: str = ""
    tags: list[str] = field(default_factory=list)
    source: str = ""


@dataclass
class Signal:
    time_data: np.ndarray
    sampling_rate: float
    frequency: float = 0.0
    amplitude: float = 1.0
    phase: float = 0.0
    metadata: SignalMetadata = field(default_factory=SignalMetadata)

    def __post_init__(self) -> None:
        if self.sampling_rate <= 0:
            raise ValueError(f"Invalid sampling rate: {self.sampling_rate}")
        if self.time_data.size == 0:
            raise ValueError("Signal data cannot be empty")

    @property
    def duration(self) -> float:
        return self.time_data.size / self.sampling_rate

    @property
    def nyquist_frequency(self) -> float:
        return self.sampling_rate / 2.0

    @property
    def time_vector(self) -> np.ndarray:
        return np.arange(self.time_data.size) / self.sampling_rate

    @property
    def rms(self) -> float:
        return float(np.sqrt(np.mean(self.time_data**2)))

    @property
    def peak_to_peak(self) -> float:
        return float(np.max(self.time_data) - np.min(self.time_data))

    @property
    def snr(self) -> float:
        signal_power = np.mean(self.time_data**2)
        if signal_power == 0:
            return -float("inf")
        return float(10 * np.log10(signal_power))

    @property
    def shape(self) -> tuple[int, ...]:
        return self.time_data.shape

    @property
    def length(self) -> int:
        return self.time_data.size

    def copy(self) -> Signal:
        return Signal(
            time_data=self.time_data.copy(),
            sampling_rate=self.sampling_rate,
            frequency=self.frequency,
            amplitude=self.amplitude,
            phase=self.phase,
            metadata=SignalMetadata(
                name=f"{self.metadata.name} (copy)",
                description=self.metadata.description,
                tags=self.metadata.tags.copy(),
                source=self.metadata.source,
            ),
        )

    def resample(self, new_rate: float) -> Signal:
        from scipy import signal as sp_signal

        ratio = new_rate / self.sampling_rate
        new_length = int(self.length * ratio)
        resampled = sp_signal.resample(self.time_data, new_length)
        return Signal(
            time_data=resampled,
            sampling_rate=new_rate,
            frequency=self.frequency * ratio,
            amplitude=self.amplitude,
            phase=self.phase,
        )

    def apply_window(self, window_type: WindowType, **kwargs: float) -> Signal:
        from src.dsp.windows.base import create_window

        window = create_window(window_type, self.length, **kwargs)
        return Signal(
            time_data=self.time_data * window,
            sampling_rate=self.sampling_rate,
            frequency=self.frequency,
            amplitude=self.amplitude,
            phase=self.phase,
        )
