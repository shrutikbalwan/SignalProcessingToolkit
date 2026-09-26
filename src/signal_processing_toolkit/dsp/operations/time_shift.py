from __future__ import annotations

import numpy as np

from signal_processing_toolkit.dsp.operations.base import BaseOperation
from signal_processing_toolkit.models.signal import Signal


def _padded_shift(data: np.ndarray, shift_samples: int) -> np.ndarray:
    """Translate samples on axis 0, filling newly exposed positions with zero."""
    result = np.zeros_like(data)
    n_samples = data.shape[0]
    if shift_samples >= n_samples or shift_samples <= -n_samples:
        return result
    if shift_samples > 0:
        result[shift_samples:] = data[: n_samples - shift_samples]
    elif shift_samples < 0:
        result[: n_samples + shift_samples] = data[-shift_samples:]
    else:
        result[...] = data
    return result


class TimeShiftOperation(BaseOperation):
    """Non-circular time shift with zero padding and fixed output length."""

    def apply(self, signal: Signal, shift_samples: int = 0, **kwargs: object) -> Signal:
        return signal.updated(
            time_data=_padded_shift(signal.time_data, shift_samples),
            operation="time_shift",
            parameters={"shift_samples": shift_samples},
        )


class CircularShiftOperation(BaseOperation):
    """Circularly rotate samples on the time axis."""

    def apply(self, signal: Signal, shift_samples: int = 0, **kwargs: object) -> Signal:
        return signal.updated(
            time_data=np.roll(signal.time_data, shift_samples, axis=Signal.SAMPLE_AXIS),
            operation="circular_shift",
            parameters={"shift_samples": shift_samples},
        )


class TimeShiftSecondsOperation(BaseOperation):
    def apply(self, signal: Signal, shift_seconds: float = 0.0, **kwargs: object) -> Signal:
        shift_samples = int(round(shift_seconds * signal.sampling_rate))
        return TimeShiftOperation().apply(signal, shift_samples=shift_samples)
