from __future__ import annotations

import numpy as np
from scipy.fft import fft, ifft

from src.models.signal import Signal


def cross_correlation(
    signal1: Signal, signal2: Signal, max_lag: int | None = None, normalize: bool = True
) -> Signal:
    validate_same_sampling_rate(signal1, signal2)

    data1 = signal1.time_data
    data2 = signal2.time_data
    n1, n2 = len(data1), len(data2)
    n = max(n1, n2)

    if max_lag is None:
        max_lag = n - 1
    max_lag = min(max_lag, n - 1)

    if normalize:
        mean1, std1 = np.mean(data1), np.std(data1)
        mean2, std2 = np.mean(data2), np.std(data2)
        if std1 > 0:
            data1 = (data1 - mean1) / std1
        if std2 > 0:
            data2 = (data2 - mean2) / std2

    n_fft = 1
    while n_fft < 2 * n - 1:
        n_fft *= 2

    fft1 = fft(data1, n_fft)
    fft2 = fft(data2, n_fft)

    cross_psd = np.conj(fft1) * fft2
    crosscorr = np.real(ifft(cross_psd))

    if normalize and n1 > 0 and n2 > 0:
        norm = np.sqrt(np.sum(data1**2) * np.sum(data2**2))
        if norm > 0:
            crosscorr = crosscorr / norm

    result = np.zeros(2 * max_lag + 1)
    center = n_fft // 2
    result[: max_lag + 1] = crosscorr[center : center + max_lag + 1]
    result[max_lag + 1 :] = crosscorr[center - max_lag : center]

    return Signal(
        time_data=result,
        sampling_rate=signal1.sampling_rate,
    )


def cross_correlation_fft(signal1: Signal, signal2: Signal, n_fft: int | None = None) -> Signal:
    validate_same_sampling_rate(signal1, signal2)

    data1 = signal1.time_data
    data2 = signal2.time_data
    n = max(len(data1), len(data2))

    n_fft = n_fft or n
    while n_fft < 2 * n - 1:
        n_fft *= 2

    fft1 = fft(data1, n_fft)
    fft2 = fft(data2, n_fft)

    cross_psd = np.conj(fft1) * fft2
    crosscorr = np.real(ifft(cross_psd))

    return Signal(
        time_data=crosscorr[:n],
        sampling_rate=signal1.sampling_rate,
    )


def time_delay_estimation(signal1: Signal, signal2: Signal, max_lag: int | None = None) -> int:
    cc_result = cross_correlation(signal1, signal2, max_lag)
    crosscorr = cc_result.time_data

    peak_idx = np.argmax(np.abs(crosscorr))
    center = len(crosscorr) // 2
    delay = peak_idx - center

    return int(delay)


def generalized_cross_correlation(
    signal1: Signal, signal2: Signal, weight: str = "phat", max_lag: int | None = None
) -> Signal:
    validate_same_sampling_rate(signal1, signal2)

    data1 = signal1.time_data
    data2 = signal2.time_data
    n = max(len(data1), len(data2))

    n_fft = 1
    while n_fft < 2 * n - 1:
        n_fft *= 2

    fft1 = fft(data1, n_fft)
    fft2 = fft(data2, n_fft)

    if weight == "phat":
        cross_psd = np.conj(fft1) * fft2
        magnitude = np.abs(cross_psd)
        cross_psd = np.where(magnitude > 1e-10, cross_psd / magnitude, 0)
    elif weight == "scot":
        cross_psd = np.conj(fft1) * fft2
        magnitude = np.abs(fft1) * np.abs(fft2)
        cross_psd = np.where(magnitude > 1e-10, cross_psd / magnitude, 0)
    elif weight == "roth":
        cross_psd = np.conj(fft1) * fft2
        magnitude = np.abs(fft1) ** 2 * np.abs(fft2) ** 2
        cross_psd = np.where(magnitude > 1e-10, cross_psd / magnitude, 0)
    else:
        cross_psd = np.conj(fft1) * fft2

    crosscorr = np.real(ifft(cross_psd))

    if max_lag is None:
        max_lag = n - 1
    max_lag = min(max_lag, n - 1)

    result = np.zeros(2 * max_lag + 1)
    center = n_fft // 2
    result[: max_lag + 1] = crosscorr[center : center + max_lag + 1]
    result[max_lag + 1 :] = crosscorr[center - max_lag : center]

    return Signal(
        time_data=result,
        sampling_rate=signal1.sampling_rate,
    )


def validate_same_sampling_rate(signal1: Signal, signal2: Signal) -> None:
    if signal1.sampling_rate != signal2.sampling_rate:
        raise ValueError(
            f"Sampling rate mismatch: {signal1.sampling_rate} vs {signal2.sampling_rate}"
        )
