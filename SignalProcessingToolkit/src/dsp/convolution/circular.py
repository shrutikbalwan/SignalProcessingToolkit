from __future__ import annotations

import numpy as np
from scipy.fft import fft, ifft

from src.models.signal import Signal


def circular_convolve(signal1: Signal, signal2: Signal) -> Signal:
    validate_same_sampling_rate(signal1, signal2)

    n = max(signal1.length, signal2.length)

    padded1 = np.pad(signal1.time_data, (0, n - signal1.length))
    padded2 = np.pad(signal2.time_data, (0, n - signal2.length))

    fft1 = fft(padded1, n)
    fft2 = fft(padded2, n)

    result_fft = fft1 * fft2
    result_data = np.real(ifft(result_fft))

    return Signal(
        time_data=result_data,
        sampling_rate=signal1.sampling_rate,
    )


def circular_convolve_fft(signal1: Signal, signal2: Signal, n_fft: int | None = None) -> Signal:
    validate_same_sampling_rate(signal1, signal2)

    n = n_fft or max(signal1.length, signal2.length)

    fft1 = fft(signal1.time_data, n)
    fft2 = fft(signal2.time_data, n)

    result_fft = fft1 * fft2
    result_data = np.real(ifft(result_fft))

    return Signal(
        time_data=result_data,
        sampling_rate=signal1.sampling_rate,
    )


def circular_correlate(signal1: Signal, signal2: Signal) -> Signal:
    validate_same_sampling_rate(signal1, signal2)

    n = max(signal1.length, signal2.length)

    padded1 = np.pad(signal1.time_data, (0, n - signal1.length))
    padded2 = np.pad(signal2.time_data, (0, n - signal2.length))

    fft1 = fft(padded1, n)
    fft2 = fft(padded2, n)

    result_fft = np.conj(fft1) * fft2
    result_data = np.real(ifft(result_fft))

    return Signal(
        time_data=result_data,
        sampling_rate=signal1.sampling_rate,
    )


def validate_same_sampling_rate(signal1: Signal, signal2: Signal) -> None:
    if signal1.sampling_rate != signal2.sampling_rate:
        raise ValueError(
            f"Sampling rate mismatch: {signal1.sampling_rate} vs {signal2.sampling_rate}"
        )
