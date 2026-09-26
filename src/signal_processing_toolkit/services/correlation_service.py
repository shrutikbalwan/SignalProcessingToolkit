from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import signal as sp_signal

from signal_processing_toolkit.models.signal import Signal


@dataclass
class CorrelationResult:
    lags: np.ndarray
    values: np.ndarray
    sampling_rate: float
    time_origin: float
    peak_lag: float = 0.0
    peak_value: float | complex = 0.0
    peak_channel: int = 0

    @property
    def lag_seconds(self) -> np.ndarray:
        return self.time_origin + self.lags / self.sampling_rate


def _channels(first: np.ndarray, second: np.ndarray) -> np.ndarray:
    if first.ndim == 1:
        return np.asarray(sp_signal.correlate(first, second, mode="full", method="auto"))
    return np.stack(
        [
            sp_signal.correlate(first[:, channel], second[:, channel], mode="full", method="auto")
            for channel in range(first.shape[Signal.CHANNEL_AXIS])
        ],
        axis=Signal.CHANNEL_AXIS,
    )


def _normalize(values: np.ndarray, first: np.ndarray, second: np.ndarray) -> np.ndarray:
    axes = Signal.SAMPLE_AXIS
    denominator = np.sqrt(
        np.sum(np.abs(first) ** 2, axis=axes) * np.sum(np.abs(second) ** 2, axis=axes)
    )
    if np.any(denominator == 0):
        raise ValueError("Normalized correlation is undefined for a zero-energy signal")
    return values / denominator


class CorrelationService:
    def auto_correlation(
        self, signal: Signal, max_lag: int | None = None, *, normalize: bool = True
    ) -> CorrelationResult:
        return self.cross_correlation(signal, signal, max_lag, normalize=normalize)

    def cross_correlation(
        self,
        first: Signal,
        second: Signal,
        max_lag: int | None = None,
        *,
        normalize: bool = True,
    ) -> CorrelationResult:
        first.validate_compatibility(
            second, require_same_length=False, require_same_start=False, require_same_units=False
        )
        if first.n_samples == 0 or second.n_samples == 0:
            raise ValueError("Correlation is undefined for empty signals")
        lags = sp_signal.correlation_lags(first.n_samples, second.n_samples, mode="full")
        values = _channels(first.time_data, second.time_data)
        if normalize:
            values = _normalize(values, first.time_data, second.time_data)
        if max_lag is not None:
            if max_lag < 0:
                raise ValueError("max_lag must be non-negative")
            keep = np.abs(lags) <= max_lag
            lags, values = lags[keep], values[keep]
        peak = np.unravel_index(int(np.argmax(np.abs(values))), values.shape)
        return CorrelationResult(
            lags=lags,
            values=values,
            sampling_rate=first.sampling_rate,
            time_origin=first.start_time - second.start_time,
            peak_lag=float(lags[peak[0]]),
            peak_value=values[peak].item(),
            peak_channel=int(peak[1]) if values.ndim == 2 else 0,
        )
