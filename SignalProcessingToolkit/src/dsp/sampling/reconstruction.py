from __future__ import annotations

import numpy as np

from src.models.signal import Signal


def zero_order_hold(signal: Signal, oversample_factor: int = 10) -> Signal:
    n_original = signal.length
    n_new = n_original * oversample_factor

    new_data = np.repeat(signal.time_data, oversample_factor)
    new_data = new_data[:n_new]

    return Signal(
        time_data=new_data,
        sampling_rate=signal.sampling_rate * oversample_factor,
    )


def linear_interpolation(signal: Signal, oversample_factor: int = 10) -> Signal:
    n_original = signal.length
    n_new = n_original * oversample_factor

    x_original = np.arange(n_original)
    x_new = np.linspace(0, n_original - 1, n_new)

    new_data = np.interp(x_new, x_original, signal.time_data)

    return Signal(
        time_data=new_data,
        sampling_rate=signal.sampling_rate * oversample_factor,
    )


def sinc_interpolation(
    signal: Signal, oversample_factor: int = 10, window_size: int = 10
) -> Signal:
    from scipy import signal as sp_signal

    n_original = signal.length
    n_new = n_original * oversample_factor

    new_data = sp_signal.resample(signal.time_data, n_new)

    return Signal(
        time_data=new_data,
        sampling_rate=signal.sampling_rate * oversample_factor,
    )


def spline_interpolation(signal: Signal, oversample_factor: int = 10, order: int = 3) -> Signal:
    from scipy import interpolate

    n_original = signal.length
    n_new = n_original * oversample_factor

    x_original = np.arange(n_original)
    x_new = np.linspace(0, n_original - 1, n_new)

    spline = interpolate.UnivariateSpline(x_original, signal.time_data, k=order, s=0)
    new_data = spline(x_new)

    return Signal(
        time_data=new_data,
        sampling_rate=signal.sampling_rate * oversample_factor,
    )


def ideal_reconstruction(signal: Signal, oversample_factor: int = 10) -> Signal:

    return sinc_interpolation(signal, oversample_factor)


RECONSTRUCTION_METHODS = {
    "zoh": zero_order_hold,
    "linear": linear_interpolation,
    "sinc": sinc_interpolation,
    "spline": spline_interpolation,
    "ideal": ideal_reconstruction,
}


def reconstruct_signal(
    signal: Signal, method: str = "sinc", oversample_factor: int = 10, **kwargs
) -> Signal:
    func = RECONSTRUCTION_METHODS.get(method.lower())
    if func is None:
        raise ValueError(f"Unknown reconstruction method: {method}")
    return func(signal, oversample_factor, **kwargs)
