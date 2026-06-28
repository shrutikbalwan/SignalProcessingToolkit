from __future__ import annotations

from typing import Any

from src.models.enums import WaveformType
from src.models.signal import Signal
from src.services.signal_service import SignalService
from src.ui.viewmodels.base_viewmodel import BaseViewModel, Observable


class SignalGeneratorViewModel(BaseViewModel):
    def __init__(self, signal_service: SignalService) -> None:
        super().__init__()
        self._signal_service = signal_service

        self.waveform_type = Observable[WaveformType](WaveformType.SINE)
        self.frequency = Observable[float](440.0)
        self.amplitude = Observable[float](1.0)
        self.phase = Observable[float](0.0)
        self.sampling_rate = Observable[float](44100.0)
        self.duration = Observable[float](1.0)
        self.duty_cycle = Observable[float](0.5)
        self.pulse_width = Observable[float](0.01)
        self.chirp_f1 = Observable[float](1000.0)
        self.chirp_method = Observable[str]("linear")
        self.gaussian_mu = Observable[float](0.5)
        self.gaussian_sigma = Observable[float](0.1)
        self.noise_type = Observable[str]("white")

        self.generated_signal = Observable[Signal | None](None)

        self._extra_params: dict[str, Any] = {}

    def generate(self) -> Signal | None:
        waveform = self.waveform_type.value
        extra = self._get_extra_params(waveform)
        signal = self._signal_service.generate(
            self.waveform_type.value,
            sampling_rate=self.sampling_rate.value,
            duration=self.duration.value,
            frequency=self.frequency.value,
            amplitude=self.amplitude.value,
            phase=self.phase.value,
            **extra,
        )
        self.generated_signal.value = signal
        return signal

    def _get_extra_params(self, waveform: WaveformType) -> dict[str, Any]:
        params: dict[str, Any] = {}
        if waveform == WaveformType.SQUARE:
            params["duty"] = self.duty_cycle.value
        elif waveform == WaveformType.PULSE:
            params["pulse_width"] = self.pulse_width.value
        elif waveform == WaveformType.CHIRP:
            params["f1"] = self.chirp_f1.value
            params["method"] = self.chirp_method.value
        elif waveform == WaveformType.GAUSSIAN:
            params["mu"] = self.gaussian_mu.value
            params["sigma"] = self.gaussian_sigma.value
        elif waveform == WaveformType.NOISE:
            params["noise_type"] = self.noise_type.value
        return params

    def dispose(self) -> None:
        super().dispose()
        self.generated_signal.value = None
