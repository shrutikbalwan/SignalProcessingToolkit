from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import signal as sp_signal

from src.models.signal import Signal


@dataclass
class AliasingReport:
    original_frequency: float
    sampling_rate: float
    nyquist: float
    aliased: bool
    aliased_frequency: float | None = None
    aliased_magnitude: float | None = None


class SamplingService:
    def sample(self, signal: Signal, new_rate: float) -> Signal:
        return signal.resample(new_rate)

    def reconstruct(self, signal: Signal, original_rate: float) -> Signal:
        ratio = original_rate / signal.sampling_rate
        new_length = int(signal.length * ratio)
        reconstructed = sp_signal.resample(signal.time_data, new_length)
        return Signal(
            time_data=reconstructed,
            sampling_rate=original_rate,
        )

    def downsample(self, signal: Signal, factor: int) -> Signal:
        if factor < 1:
            raise ValueError(f"Downsample factor must be >= 1, got {factor}")
        return Signal(
            time_data=signal.time_data[::factor],
            sampling_rate=signal.sampling_rate / factor,
        )

    def upsample(self, signal: Signal, factor: int) -> Signal:
        if factor < 1:
            raise ValueError(f"Upsample factor must be >= 1, got {factor}")
        upsampled = np.zeros(len(signal.time_data) * factor)
        upsampled[::factor] = signal.time_data
        return Signal(
            time_data=upsampled,
            sampling_rate=signal.sampling_rate * factor,
        )

    def detect_aliasing(self, signal: Signal, target_rate: float) -> AliasingReport:
        nyquist = target_rate / 2.0
        freq = signal.frequency
        aliased = freq > nyquist
        aliased_freq = None
        if aliased:
            aliased_freq = abs(freq % target_rate)
            if aliased_freq > nyquist:
                aliased_freq = target_rate - aliased_freq
        return AliasingReport(
            original_frequency=freq,
            sampling_rate=target_rate,
            nyquist=nyquist,
            aliased=aliased,
            aliased_frequency=aliased_freq,
        )

    def demo_aliasing(self, signal: Signal, target_rate: float) -> dict:
        report = self.detect_aliasing(signal, target_rate)
        aliased_signal = self.downsample(signal, max(1, int(signal.sampling_rate / target_rate)))
        return {"report": report, "aliased_signal": aliased_signal}
