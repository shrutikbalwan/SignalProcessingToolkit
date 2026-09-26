from __future__ import annotations

import numpy as np

from signal_processing_toolkit.models.signal import Signal
from signal_processing_toolkit.services.correlation_service import CorrelationService


def cross_correlation(
    signal1: Signal, signal2: Signal, max_lag: int | None = None, normalize: bool = True
) -> Signal:
    result = CorrelationService().cross_correlation(signal1, signal2, max_lag, normalize=normalize)
    return signal1.updated(
        time_data=result.values,
        start_time=float(result.lag_seconds[0]),
        operation="cross_correlation",
        parameters={"normalized": normalize, "second_signal_id": signal2.metadata.id},
    )


def cross_correlation_fft(signal1: Signal, signal2: Signal, n_fft: int | None = None) -> Signal:
    del n_fft
    return cross_correlation(signal1, signal2, normalize=False)


def time_delay_estimation(signal1: Signal, signal2: Signal, max_lag: int | None = None) -> int:
    result = CorrelationService().cross_correlation(signal1, signal2, max_lag)
    return int(result.peak_lag)


def generalized_cross_correlation(
    signal1: Signal, signal2: Signal, weight: str = "phat", max_lag: int | None = None
) -> Signal:
    if weight not in {"none", "phat"}:
        raise ValueError("Supported generalized correlation weights are 'none' and 'phat'")
    if weight == "none":
        return cross_correlation(signal1, signal2, max_lag, normalize=False)
    signal1.validate_compatibility(
        signal2, require_same_length=False, require_same_start=False, require_same_units=False
    )
    size = signal1.n_samples + signal2.n_samples - 1
    n_fft = 1 << (size - 1).bit_length()
    first = np.fft.fft(signal1.time_data, n_fft, axis=Signal.SAMPLE_AXIS)
    second = np.fft.fft(signal2.time_data, n_fft, axis=Signal.SAMPLE_AXIS)
    cross_spectrum = first * np.conj(second)
    cross_spectrum /= np.maximum(np.abs(cross_spectrum), np.finfo(float).tiny)
    values = np.fft.ifft(cross_spectrum, axis=Signal.SAMPLE_AXIS)
    negative = values[-(signal2.n_samples - 1) :] if signal2.n_samples > 1 else values[:0]
    values = np.concatenate((negative, values[: signal1.n_samples]), axis=Signal.SAMPLE_AXIS)
    if not signal1.is_complex and not signal2.is_complex:
        values = values.real
    lags = np.arange(-(signal2.n_samples - 1), signal1.n_samples)
    if max_lag is not None:
        keep = np.abs(lags) <= max_lag
        lags, values = lags[keep], values[keep]
    return signal1.updated(
        time_data=values,
        start_time=signal1.start_time - signal2.start_time + lags[0] / signal1.sampling_rate,
        operation="generalized_cross_correlation",
        parameters={"weight": weight},
    )


def validate_same_sampling_rate(signal1: Signal, signal2: Signal) -> None:
    signal1.validate_compatibility(
        signal2, require_same_length=False, require_same_start=False, require_same_units=False
    )
