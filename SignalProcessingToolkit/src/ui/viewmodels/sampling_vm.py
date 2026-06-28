from __future__ import annotations

from src.models.signal import Signal
from src.services.sampling_service import AliasingReport, SamplingService
from src.ui.viewmodels.base_viewmodel import BaseViewModel, Observable


class SamplingViewModel(BaseViewModel):
    def __init__(self, sampling_service: SamplingService) -> None:
        super().__init__()
        self._sampling_service = sampling_service

        self.input_signal = Observable[Signal | None](None)
        self.target_rate = Observable[float](44100.0)
        self.downsample_factor = Observable[int](2)
        self.upsample_factor = Observable[int](2)

        self.sampled_signal = Observable[Signal | None](None)
        self.reconstructed_signal = Observable[Signal | None](None)
        self.downsampled_signal = Observable[Signal | None](None)
        self.upsampled_signal = Observable[Signal | None](None)
        self.aliasing_report = Observable[AliasingReport | None](None)
        self.aliased_signal = Observable[Signal | None](None)

        self.status_message = Observable[str]("")

    def resample(self) -> Signal | None:
        signal = self.input_signal.value
        if signal is None:
            self.status_message.value = "No input signal"
            return None
        result = self._sampling_service.sample(signal, self.target_rate.value)
        self.sampled_signal.value = result
        self.status_message.value = f"Resampled to {self.target_rate.value:.0f} Hz"
        return result

    def reconstruct(self) -> Signal | None:
        orig = self.input_signal.value
        sampled = self.sampled_signal.value
        if sampled is None or orig is None:
            self.status_message.value = "Resample a signal first"
            return None
        result = self._sampling_service.reconstruct(sampled, orig.sampling_rate)
        self.reconstructed_signal.value = result
        self.status_message.value = "Reconstructed to original rate"
        return result

    def downsample(self) -> Signal | None:
        signal = self.input_signal.value
        if signal is None:
            self.status_message.value = "No input signal"
            return None
        result = self._sampling_service.downsample(signal, self.downsample_factor.value)
        self.downsampled_signal.value = result
        self.status_message.value = f"Downsampled by factor {self.downsample_factor.value}"
        return result

    def upsample(self) -> Signal | None:
        signal = self.input_signal.value
        if signal is None:
            self.status_message.value = "No input signal"
            return None
        result = self._sampling_service.upsample(signal, self.upsample_factor.value)
        self.upsampled_signal.value = result
        self.status_message.value = f"Upsampled by factor {self.upsample_factor.value}"
        return result

    def check_aliasing(self) -> AliasingReport | None:
        signal = self.input_signal.value
        if signal is None:
            self.status_message.value = "No input signal"
            return None
        report = self._sampling_service.detect_aliasing(signal, self.target_rate.value)
        self.aliasing_report.value = report
        if report.aliased:
            demo = self._sampling_service.demo_aliasing(signal, self.target_rate.value)
            self.aliased_signal.value = demo["aliased_signal"]
            self.status_message.value = (
                f"ALIASING: {report.original_frequency:.1f} Hz > Nyquist "
                f"({report.nyquist:.1f} Hz) → aliased to {report.aliased_frequency:.1f} Hz"
            )
        else:
            self.aliased_signal.value = None
            self.status_message.value = "No aliasing detected"
        return report

    def dispose(self) -> None:
        super().dispose()
        self.sampled_signal.value = None
        self.reconstructed_signal.value = None
        self.downsampled_signal.value = None
        self.upsampled_signal.value = None
        self.aliased_signal.value = None
