from __future__ import annotations

from src.models.fft_result import FFTResult, SpectrumPeak
from src.models.signal import Signal
from src.services.fft_service import FFTService
from src.ui.viewmodels.base_viewmodel import BaseViewModel, Observable


class FFTViewModel(BaseViewModel):
    def __init__(self, fft_service: FFTService) -> None:
        super().__init__()
        self._service = fft_service

        self.input_signal = Observable[Signal | None](None)
        self.spectrum_type = Observable[str]("magnitude")
        self.fft_size = Observable[int](4096)
        self.min_peak_height = Observable[float](0.1)
        self.min_peak_distance = Observable[int](5)

        self.result = Observable[FFTResult | None](None)
        self.peaks = Observable[list[SpectrumPeak]]([])
        self.inverse_signal = Observable[Signal | None](None)
        self.status_message = Observable[str]("")

    def compute(self) -> FFTResult | None:
        signal = self.input_signal.value
        if signal is None:
            self.status_message.value = "No input signal"
            return None

        st = self.spectrum_type.value
        n = self.fft_size.value

        if st == "magnitude":
            result = self._service.compute_magnitude_spectrum(signal, n)
        elif st == "power":
            result = self._service.compute_power_spectrum(signal, n)
        elif st == "phase":
            result = self._service.compute_phase_spectrum(signal, n)
        else:
            result = self._service.compute(signal, n).positive_spectrum

        result.peaks = self._service.detect_peaks(
            result, self.min_peak_height.value, self.min_peak_distance.value
        )

        self.result.value = result
        self.peaks.value = result.peaks

        dom_freq = result.dominant_frequency
        n_peaks = len(result.peaks)
        self.status_message.value = (
            f"FFT complete — {n} points, dominant: {dom_freq:.2f} Hz, {n_peaks} peak(s) detected"
        )
        return result

    def compute_inverse(self) -> Signal | None:
        result = self.result.value
        if result is None:
            self.status_message.value = "Compute FFT first"
            return None
        signal = self._service.compute_inverse(result)
        self.inverse_signal.value = signal
        self.status_message.value = "IFFT complete"
        return signal

    def update_peaks(self) -> None:
        result = self.result.value
        if result is None:
            return
        result.peaks = self._service.detect_peaks(
            result, self.min_peak_height.value, self.min_peak_distance.value
        )
        self.peaks.value = result.peaks

    def dispose(self) -> None:
        super().dispose()
        self.result.value = None
        self.inverse_signal.value = None
