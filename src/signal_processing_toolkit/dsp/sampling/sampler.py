from __future__ import annotations

from collections.abc import Callable
from fractions import Fraction

import numpy as np
from scipy import signal as sp_signal

from signal_processing_toolkit.models.signal import Signal


def _positive_integer(value: int, name: str) -> int:
    if isinstance(value, bool) or int(value) != value or value < 1:
        raise ValueError(f"{name} must be a positive integer, got {value!r}")
    return int(value)


def sample_continuous_signal(
    signal_func: Callable[[np.ndarray], np.ndarray],
    sampling_rate: float,
    duration: float,
    t_start: float = 0.0,
) -> Signal:
    if not np.isfinite(duration) or duration < 0:
        raise ValueError("duration must be finite and non-negative")
    n_samples = int(round(sampling_rate * duration))
    times = t_start + np.arange(n_samples) / sampling_rate
    return Signal(
        time_data=np.asarray(signal_func(times)), sampling_rate=sampling_rate, start_time=t_start
    )


def rational_resample(signal: Signal, up: int, down: int) -> Signal:
    """Polyphase resampling with anti-alias/reconstruction FIR filtering.

    The output contains ``ceil(n_samples * up / down)`` samples, matching
    :func:`scipy.signal.resample_poly`.
    """
    up = _positive_integer(up, "up")
    down = _positive_integer(down, "down")
    divisor = np.gcd(up, down)
    up //= int(divisor)
    down //= int(divisor)
    expected = (signal.n_samples * up + down - 1) // down
    if signal.n_samples == 0:
        shape = (0,) if signal.time_data.ndim == 1 else (0, signal.n_channels)
        data = np.empty(shape, dtype=signal.time_data.dtype)
    else:
        data = sp_signal.resample_poly(signal.time_data, up, down, axis=Signal.SAMPLE_AXIS)
    if data.shape[0] != expected:
        raise RuntimeError(f"Unexpected resample length {data.shape[0]}; expected {expected}")
    return signal.updated(
        time_data=data,
        sampling_rate=signal.sampling_rate * up / down,
        operation="resample_poly",
        parameters={"up": up, "down": down},
    )


def resample_signal(
    signal: Signal, new_sampling_rate: float, *, max_denominator: int = 100_000
) -> Signal:
    if not np.isfinite(new_sampling_rate) or new_sampling_rate <= 0:
        raise ValueError("new_sampling_rate must be finite and positive")
    if np.isclose(signal.sampling_rate, new_sampling_rate, rtol=0.0, atol=1e-12):
        return signal.copy()
    ratio = Fraction(float(new_sampling_rate / signal.sampling_rate)).limit_denominator(
        max_denominator
    )
    achieved = signal.sampling_rate * ratio.numerator / ratio.denominator
    if not np.isclose(achieved, new_sampling_rate, rtol=1e-10, atol=1e-12):
        raise ValueError(
            f"Rate ratio cannot be represented within tolerance using denominator "
            f"{max_denominator}: requested {new_sampling_rate} Hz, achieved {achieved} Hz"
        )
    result = rational_resample(signal, ratio.numerator, ratio.denominator)
    result.sampling_rate = float(new_sampling_rate)
    return result


def decimate_signal(signal: Signal, factor: int) -> Signal:
    factor = _positive_integer(factor, "factor")
    return signal.copy() if factor == 1 else rational_resample(signal, 1, factor)


def interpolate_signal(signal: Signal, factor: int) -> Signal:
    factor = _positive_integer(factor, "factor")
    return signal.copy() if factor == 1 else rational_resample(signal, factor, 1)
