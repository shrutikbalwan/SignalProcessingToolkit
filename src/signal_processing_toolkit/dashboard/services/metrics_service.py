"""Numerical metrics adapter kept independent of Qt."""

from __future__ import annotations

import math
from collections.abc import Sequence

import numpy as np

from signal_processing_toolkit.dashboard.state import SignalMetrics


class MetricsService:
    def spectrum(self, samples: Sequence[float]) -> list[float]:
        """Return normalized single-sided magnitudes for dashboard display."""
        if not samples:
            return []
        values = np.asarray(samples, dtype=float)
        magnitudes = np.abs(np.fft.rfft(values - np.mean(values)))
        if len(values) > 1:
            magnitudes *= 2.0 / len(values)
            magnitudes[0] /= 2.0
        return [float(item) for item in magnitudes]

    def calculate(self, samples: Sequence[float], sampling_rate: float) -> SignalMetrics:
        if not samples:
            return SignalMetrics()
        mean_square = sum(sample * sample for sample in samples) / len(samples)
        rms = math.sqrt(mean_square)
        peak = max(abs(sample) for sample in samples)
        peak_to_peak = max(samples) - min(samples)
        dominant = 0.0
        if len(samples) > 1 and sampling_rate > 0:
            spectrum = np.abs(np.fft.rfft(np.asarray(samples, dtype=float)))
            if len(spectrum) > 1:
                dominant = float(np.argmax(spectrum[1:]) + 1) * sampling_rate / len(samples)
        return SignalMetrics(
            rms=rms,
            peak=peak,
            peak_to_peak=peak_to_peak,
            crest_factor=peak / rms if rms else None,
            dominant_frequency=dominant,
        )
