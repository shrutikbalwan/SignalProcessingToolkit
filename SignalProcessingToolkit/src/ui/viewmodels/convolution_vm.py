from __future__ import annotations

from src.models.signal import Signal
from src.services.convolution_service import ConvolutionService
from src.ui.viewmodels.base_viewmodel import BaseViewModel, Observable


class ConvolutionViewModel(BaseViewModel):
    def __init__(self, convolution_service: ConvolutionService) -> None:
        super().__init__()
        self._service = convolution_service

        self.input_signal = Observable[Signal | None](None)
        self.kernel_signal = Observable[Signal | None](None)
        self.mode = Observable[str]("linear")

        self.output = Observable[Signal | None](None)
        self.impulse_response = Observable[Signal | None](None)
        self.status_message = Observable[str]("")

    def execute(self) -> Signal | None:
        signal = self.input_signal.value
        kernel = self.kernel_signal.value
        if signal is None or kernel is None:
            self.status_message.value = "Select both input and kernel signals"
            return None

        mode = self.mode.value
        if mode == "linear":
            result = self._service.linear(signal, kernel)
        elif mode == "circular":
            result = self._service.circular(signal, kernel)
        elif mode == "same":
            result = self._service.same(signal, kernel)
        elif mode == "valid":
            result = self._service.valid(signal, kernel)
        else:
            self.status_message.value = f"Unknown mode: {mode}"
            return None

        self.output.value = result
        self.impulse_response.value = kernel
        self.status_message.value = (
            f"Convolution ({mode}) complete — {len(result.time_data)} samples"
        )
        return result

    def dispose(self) -> None:
        super().dispose()
        self.output.value = None
