from __future__ import annotations

from src.models.signal import Signal
from src.services.correlation_service import CorrelationResult, CorrelationService
from src.ui.viewmodels.base_viewmodel import BaseViewModel, Observable


class CorrelationViewModel(BaseViewModel):
    def __init__(self, correlation_service: CorrelationService) -> None:
        super().__init__()
        self._service = correlation_service

        self.input_a = Observable[Signal | None](None)
        self.input_b = Observable[Signal | None](None)
        self.max_lag = Observable[int](200)

        self.result = Observable[CorrelationResult | None](None)
        self.output_signal = Observable[Signal | None](None)
        self.status_message = Observable[str]("")

    def auto_correlate(self) -> CorrelationResult | None:
        signal = self.input_a.value
        if signal is None:
            self.status_message.value = "Select a signal"
            return None
        result = self._service.auto_correlation(signal, self.max_lag.value)
        self.result.value = result
        self.status_message.value = f"Auto-correlation — peak lag: {result.peak_lag} samples"
        return result

    def cross_correlate(self) -> CorrelationResult | None:
        a = self.input_a.value
        b = self.input_b.value
        if a is None or b is None:
            self.status_message.value = "Select both signals A and B"
            return None
        result = self._service.cross_correlation(a, b, self.max_lag.value)
        self.result.value = result
        self.status_message.value = (
            f"Cross-correlation — peak lag: {result.peak_lag} samples "
            f"(value: {result.peak_value:.4f})"
        )
        return result

    def dispose(self) -> None:
        super().dispose()
        self.result.value = None
