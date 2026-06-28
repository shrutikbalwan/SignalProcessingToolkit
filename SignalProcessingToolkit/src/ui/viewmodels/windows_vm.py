from __future__ import annotations

import numpy as np

from src.models.enums import WindowType
from src.models.signal import Signal
from src.services.window_service import WindowMetrics, WindowService
from src.ui.viewmodels.base_viewmodel import BaseViewModel, Observable


class WindowViewModel(BaseViewModel):
    def __init__(self, window_service: WindowService) -> None:
        super().__init__()
        self._service = window_service

        self.window_type = Observable[WindowType](WindowType.HAMMING)
        self.window_length = Observable[int](256)
        self.kaiser_beta = Observable[float](14.0)
        self.input_signal = Observable[Signal | None](None)
        self.compare_types = Observable[list[WindowType]](
            [WindowType.RECTANGULAR, WindowType.HAMMING, WindowType.HANNING, WindowType.BLACKMAN]
        )

        self.window_data = Observable[np.ndarray | None](None)
        self.freq_response = Observable[tuple[np.ndarray, np.ndarray] | None](None)
        self.metrics = Observable[WindowMetrics | None](None)
        self.comparison = Observable[dict[WindowType, np.ndarray]]({})
        self.applied_signal = Observable[Signal | None](None)
        self.status_message = Observable[str]("")

    def compute(self) -> np.ndarray:
        data = self._service.create(
            self.window_type.value,
            self.window_length.value,
            beta=self.kaiser_beta.value,
        )
        self.window_data.value = data
        freqs, mag = self._service.frequency_response(data)
        self.freq_response.value = (freqs, mag)
        self.metrics.value = self._service.compute_metrics(data)
        self.status_message.value = f"Window: {self.window_type.value.value}"
        return data

    def apply_to_signal(self) -> Signal | None:
        signal = self.input_signal.value
        if signal is None:
            self.status_message.value = "No input signal"
            return None
        result = self._service.apply(signal, self.window_type.value, beta=self.kaiser_beta.value)
        self.applied_signal.value = result
        self.status_message.value = f"Applied {self.window_type.value.value} window"
        return result

    def run_comparison(self) -> dict[WindowType, np.ndarray]:
        result = self._service.compare(self.compare_types.value, self.window_length.value)
        self.comparison.value = result
        self.status_message.value = f"Compared {len(result)} window types"
        return result

    def dispose(self) -> None:
        super().dispose()
        self.window_data.value = None
        self.applied_signal.value = None
