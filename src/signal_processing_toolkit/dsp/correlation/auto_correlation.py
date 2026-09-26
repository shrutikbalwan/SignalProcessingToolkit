from __future__ import annotations

import numpy as np
from scipy import signal as sp_signal

from signal_processing_toolkit.models.signal import Signal
from signal_processing_toolkit.services.correlation_service import CorrelationService


def auto_correlation(signal: Signal, max_lag: int | None = None, normalize: bool = True) -> Signal:
    result = CorrelationService().auto_correlation(signal, max_lag, normalize=normalize)
    return signal.updated(
        time_data=result.values,
        start_time=float(result.lag_seconds[0]),
        operation="auto_correlation",
        parameters={"normalized": normalize},
    )


def biased_auto_correlation(signal: Signal, max_lag: int | None = None) -> Signal:
    result = CorrelationService().auto_correlation(signal, max_lag, normalize=False)
    return signal.updated(
        time_data=result.values / signal.n_samples,
        start_time=float(result.lag_seconds[0]),
        operation="biased_auto_correlation",
    )


def unbiased_auto_correlation(signal: Signal, max_lag: int | None = None) -> Signal:
    result = CorrelationService().auto_correlation(signal, max_lag, normalize=False)
    overlap = signal.n_samples - np.abs(result.lags)
    scale = overlap if result.values.ndim == 1 else overlap[:, np.newaxis]
    return signal.updated(
        time_data=result.values / scale,
        start_time=float(result.lag_seconds[0]),
        operation="unbiased_auto_correlation",
    )


def find_period(signal: Signal, min_period: int = 2, max_period: int | None = None) -> int:
    if signal.n_samples == 0:
        raise ValueError("Period is undefined for an empty signal")
    values = sp_signal.correlate(signal.time_data, signal.time_data, mode="full")
    values = values[signal.n_samples - 1 :]
    upper = len(values) if max_period is None else min(max_period, len(values))
    if min_period >= upper:
        return 0
    return int(np.argmax(np.abs(values[min_period:upper])) + min_period)
