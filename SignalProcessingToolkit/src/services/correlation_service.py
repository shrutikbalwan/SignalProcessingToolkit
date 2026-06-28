from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from src.models.signal import Signal


@dataclass
class CorrelationResult:
    lags: np.ndarray
    values: np.ndarray
    peak_lag: float = 0.0
    peak_value: float = 0.0


class CorrelationService:
    def auto_correlation(self, signal: Signal, max_lag: int | None = None) -> CorrelationResult:
        data = signal.time_data
        n = len(data)
        max_lag = max_lag or n // 2
        lags = np.arange(-max_lag, max_lag + 1)
        values = np.correlate(data, data, mode="full")
        center = n - 1
        values = values[center - max_lag : center + max_lag + 1] / n
        peak_idx = np.argmax(np.abs(values))
        return CorrelationResult(
            lags=lags,
            values=values,
            peak_lag=float(lags[peak_idx]),
            peak_value=float(values[peak_idx]),
        )

    def cross_correlation(
        self, s1: Signal, s2: Signal, max_lag: int | None = None
    ) -> CorrelationResult:
        n = max(len(s1.time_data), len(s2.time_data))
        max_lag = max_lag or n // 2
        lags = np.arange(-max_lag, max_lag + 1)
        values = np.correlate(s1.time_data, s2.time_data, mode="full")
        center = n - 1
        values = values[center - max_lag : center + max_lag + 1] / n
        peak_idx = np.argmax(np.abs(values))
        return CorrelationResult(
            lags=lags,
            values=values,
            peak_lag=float(lags[peak_idx]),
            peak_value=float(values[peak_idx]),
        )
