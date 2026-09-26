from __future__ import annotations

import numpy as np

from signal_processing_toolkit.models.signal import Signal


def zero_order_hold(signal: Signal, oversample_factor: int = 10) -> Signal:
    n_original = signal.length
    n_new = n_original * oversample_factor

    new_data = np.repeat(signal.time_data, oversample_factor, axis=Signal.SAMPLE_AXIS)
    new_data = new_data[:n_new]

    return signal.updated(
        time_data=new_data,
        sampling_rate=signal.sampling_rate * oversample_factor,
        operation="zero_order_hold",
        parameters={"oversample_factor": oversample_factor},
    )


def linear_interpolation(signal: Signal, oversample_factor: int = 10) -> Signal:
    n_original = signal.length
    n_new = n_original * oversample_factor

    x_original = np.arange(n_original)
    x_new = np.linspace(0, n_original - 1, n_new)

    if signal.is_mono:
        new_data = np.interp(x_new, x_original, signal.time_data)
    else:
        new_data = np.stack(
            [
                np.interp(x_new, x_original, signal.time_data[:, channel])
                for channel in range(signal.n_channels)
            ],
            axis=Signal.CHANNEL_AXIS,
        )

    return signal.updated(
        time_data=new_data,
        sampling_rate=signal.sampling_rate * oversample_factor,
        operation="linear_interpolation",
        parameters={"oversample_factor": oversample_factor},
    )


def sinc_interpolation(
    signal: Signal, oversample_factor: int = 10, window_size: int = 10
) -> Signal:
    return signal.resample(signal.sampling_rate * oversample_factor)


def spline_interpolation(signal: Signal, oversample_factor: int = 10, order: int = 3) -> Signal:
    from scipy import interpolate

    n_original = signal.length
    n_new = n_original * oversample_factor

    x_original = np.arange(n_original)
    x_new = np.linspace(0, n_original - 1, n_new)

    if signal.is_mono:
        spline = interpolate.UnivariateSpline(x_original, signal.time_data, k=order, s=0)
        new_data = spline(x_new)
    else:
        new_data = np.stack(
            [
                interpolate.UnivariateSpline(
                    x_original, signal.time_data[:, channel], k=order, s=0
                )(x_new)
                for channel in range(signal.n_channels)
            ],
            axis=Signal.CHANNEL_AXIS,
        )

    return signal.updated(
        time_data=new_data,
        sampling_rate=signal.sampling_rate * oversample_factor,
        operation="spline_interpolation",
        parameters={"oversample_factor": oversample_factor, "order": order},
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
