from __future__ import annotations

from signal_processing_toolkit.models.fft_result import FFTResult, SpectrumPeak
from signal_processing_toolkit.models.signal import Signal


class FFTService:
    def compute(self, signal: Signal, n_points: int | None = None) -> FFTResult:
        from signal_processing_toolkit.dsp.fft.fft_engine import compute_fft

        return compute_fft(signal, n_points)

    def compute_inverse(self, result: FFTResult) -> Signal:
        from signal_processing_toolkit.dsp.fft.inverse_fft import inverse_fft

        return inverse_fft(result)

    def compute_magnitude_spectrum(self, signal: Signal, n_points: int | None = None) -> FFTResult:
        result = self.compute(signal, n_points)
        return result.positive_spectrum

    def compute_power_spectrum(self, signal: Signal, n_points: int | None = None) -> FFTResult:
        return self.compute(signal, n_points)

    def compute_phase_spectrum(self, signal: Signal, n_points: int | None = None) -> FFTResult:
        result = self.compute(signal, n_points)
        return result.positive_spectrum

    def detect_peaks(
        self, result: FFTResult, min_height: float = 0.1, min_distance: int = 5
    ) -> list[SpectrumPeak]:
        return result.find_peaks(min_height=min_height, min_distance=min_distance)
