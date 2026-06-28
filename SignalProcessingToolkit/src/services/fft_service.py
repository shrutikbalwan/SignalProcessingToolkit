from __future__ import annotations

import numpy as np
from scipy.fft import fft, fftfreq, ifft

from src.models.fft_result import FFTResult, SpectrumPeak
from src.models.signal import Signal


class FFTService:
    def compute(self, signal: Signal, n_points: int | None = None) -> FFTResult:
        n = n_points or len(signal.time_data)
        spectrum = fft(signal.time_data, n=n)
        freqs = fftfreq(n, d=1.0 / signal.sampling_rate)
        magnitude = np.abs(spectrum)
        phase = np.angle(spectrum)
        result = FFTResult(
            frequencies=freqs,
            magnitude=magnitude,
            phase=phase,
            n_points=n,
            sampling_rate=signal.sampling_rate,
        )
        result.peaks = result.find_peaks()
        return result

    def compute_inverse(self, result: FFTResult) -> Signal:
        time_data = np.real(ifft(result.magnitude * np.exp(1j * result.phase)))
        return Signal(
            time_data=time_data,
            sampling_rate=result.sampling_rate,
        )

    def compute_magnitude_spectrum(self, signal: Signal, n_points: int | None = None) -> FFTResult:
        result = self.compute(signal, n_points)
        return result.positive_spectrum

    def compute_power_spectrum(self, signal: Signal, n_points: int | None = None) -> FFTResult:
        result = self.compute(signal, n_points)
        result.magnitude = result.magnitude**2
        return result.positive_spectrum

    def compute_phase_spectrum(self, signal: Signal, n_points: int | None = None) -> FFTResult:
        result = self.compute(signal, n_points)
        return result.positive_spectrum

    def detect_peaks(
        self, result: FFTResult, min_height: float = 0.1, min_distance: int = 5
    ) -> list[SpectrumPeak]:
        return result.find_peaks(min_height=min_height, min_distance=min_distance)
