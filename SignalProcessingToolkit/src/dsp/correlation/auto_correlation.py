from __future__ import annotations

import numpy as np
from scipy.fft import fft, ifft

from src.models.signal import Signal


def auto_correlation(signal: Signal, max_lag: int | None = None, normalize: bool = True) -> Signal:
    data = signal.time_data
    n = len(data)

    if max_lag is None:
        max_lag = n - 1
    max_lag = min(max_lag, n - 1)

    if normalize:
        mean = np.mean(data)
        std = np.std(data)
        if std > 0:
            data = (data - mean) / std

    n_fft = 1
    while n_fft < 2 * n - 1:
        n_fft *= 2

    data_fft = fft(data, n_fft)
    psd = data_fft * np.conj(data_fft)
    autocorr = np.real(ifft(psd))[:n]

    if normalize and n > 0:
        autocorr = autocorr / autocorr[0]

    np.arange(max_lag + 1)
    result_data = autocorr[: max_lag + 1]

    return Signal(
        time_data=result_data,
        sampling_rate=signal.sampling_rate,
        metadata=signal.metadata,
    )


def biased_auto_correlation(signal: Signal, max_lag: int | None = None) -> Signal:
    data = signal.time_data
    n = len(data)

    if max_lag is None:
        max_lag = n - 1
    max_lag = min(max_lag, n - 1)

    result = np.zeros(max_lag + 1)
    for k in range(max_lag + 1):
        result[k] = np.sum(data[: n - k] * data[k:]) / n

    return Signal(
        time_data=result,
        sampling_rate=signal.sampling_rate,
        metadata=signal.metadata,
    )


def unbiased_auto_correlation(signal: Signal, max_lag: int | None = None) -> Signal:
    data = signal.time_data
    n = len(data)

    if max_lag is None:
        max_lag = n - 1
    max_lag = min(max_lag, n - 1)

    result = np.zeros(max_lag + 1)
    for k in range(max_lag + 1):
        result[k] = np.sum(data[: n - k] * data[k:]) / (n - k)

    return Signal(
        time_data=result,
        sampling_rate=signal.sampling_rate,
        metadata=signal.metadata,
    )


def find_period(signal: Signal, min_period: int = 2, max_period: int | None = None) -> int:
    autocorr_result = auto_correlation(signal)
    autocorr = autocorr_result.time_data

    if max_period is None:
        max_period = len(autocorr) // 2

    search_range = autocorr[min_period:max_period]
    if len(search_range) == 0:
        return 0

    peak_idx = np.argmax(search_range) + min_period
    return int(peak_idx)
