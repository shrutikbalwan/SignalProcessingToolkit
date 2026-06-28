from __future__ import annotations

from src.core.events import EventBus
from src.models.signal import Signal
from src.services.fft_service import FFTService
from src.ui.controllers.base_controller import BaseController
from src.ui.viewmodels.fft_vm import FFTViewModel
from src.ui.views.fft_view import FFTView


class FFTController(BaseController):
    def __init__(self, event_bus: EventBus) -> None:
        self._service = FFTService()
        self._viewmodel = FFTViewModel(self._service)
        self._view: FFTView | None = None
        super().__init__(event_bus)

    def get_view(self) -> FFTView:
        if self._view is None:
            self._view = FFTView(self._viewmodel)
        return self._view

    def _connect_events(self) -> None:
        self.event_bus.subscribe("signal:generated", self._on_signal)
        self.event_bus.subscribe("signal:loaded", self._on_signal)
        self.event_bus.subscribe("signal:operations_result", self._on_signal)

    def _on_signal(self, signal: Signal | None = None, **kwargs) -> None:
        if signal is not None and self._view is not None:
            self._view.set_input_signal(signal)

    def cleanup(self) -> None:
        self._viewmodel.dispose()
        super().cleanup()
