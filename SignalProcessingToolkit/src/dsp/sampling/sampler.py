from __future__ import annotations

import numpy as np

from src.models.signal import Signal


def sample_continuous_signal(
    signal_func,
    sampling_rate: float,
    duration: float,
    t_start: float = 0.0,
) -> Signal:
    n_samples = int(sampling_rate * duration)
    t = np.linspace(t_start, t_start + duration, n_samples, endpoint=False)
    samples = signal_func(t)
    return Signal(
        time_data=samples,
        sampling_rate=sampling_rate,
    )


def resample_signal(signal: Signal, new_sampling_rate: float) -> Signal:
    if signal.sampling_rate == new_sampling_rate:
        return signal.copy()

    from scipy import signal as sp_signal

    ratio = new_sampling_rate / signal.sampling_rate
    new_length = int(signal.length * ratio)
    resampled = sp_signal.resample(signal.time_data, new_length)

    return Signal(
        time_data=resampled,
        sampling_rate=new_sampling_rate,
    )


def decimate_signal(signal: Signal, factor: int) -> Signal:
    if factor <= 1:
        return signal.copy()

    from scipy import signal as sp_signal

    decimated = sp_signal.decimate(signal.time_data, factor)
    new_rate = signal.sampling_rate / factor

    return Signal(
        time_data=decimated,
        sampling_rate=new_rate,
    )


def interpolate_signal(signal: Signal, factor: int) -> Signal:
    if factor <= 1:
        return signal.copy()

    from scipy import signal as sp_signal

    interpolated = sp_signal.resample_poly(signal.time_data, factor, 1)
    new_rate = signal.sampling_rate * factor

    return Signal(
        time_data=interpolated,
        sampling_rate=new_rate,
    )


def rational_resample(signal: Signal, up: int, down: int) -> Signal:
    from scipy import signal as sp_signal

    resampled = sp_signal.resample_poly(signal.time_data, up, down)
    new_rate = signal.sampling_rate * up / down

    return Signal(
        time_data=resampled,
        sampling_rate=new_rate,
    )
