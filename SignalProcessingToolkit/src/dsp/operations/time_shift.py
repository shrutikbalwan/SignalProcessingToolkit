from __future__ import annotations

import numpy as np

from src.dsp.operations.base import BaseOperation
from src.models.signal import Signal


class TimeShiftOperation(BaseOperation):
    def apply(self, signal: Signal, shift_samples: int = 0, **kwargs) -> Signal:
        if shift_samples == 0:
            return signal.copy()

        shifted_data = np.roll(signal.time_data, shift_samples)

        if shift_samples > 0:
            shifted_data[:shift_samples] = 0
        else:
            shifted_data[shift_samples:] = 0

        return Signal(
            time_data=shifted_data,
            sampling_rate=signal.sampling_rate,
            metadata=signal.metadata,
        )


class TimeShiftSecondsOperation(BaseOperation):
    def apply(self, signal: Signal, shift_seconds: float = 0.0, **kwargs) -> Signal:
        shift_samples = int(shift_seconds * signal.sampling_rate)
        return TimeShiftOperation().apply(signal, shift_samples=shift_samples)
