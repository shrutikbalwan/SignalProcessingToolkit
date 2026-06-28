from __future__ import annotations

from src.core.events import EventBus
from src.models.signal import Signal
from src.services.convolution_service import ConvolutionService
from src.ui.controllers.base_controller import BaseController
from src.ui.viewmodels.convolution_vm import ConvolutionViewModel
from src.ui.views.convolution_view import ConvolutionView


class ConvolutionController(BaseController):
    def __init__(self, event_bus: EventBus) -> None:
        self._service = ConvolutionService()
        self._viewmodel = ConvolutionViewModel(self._service)
        self._view: ConvolutionView | None = None
        self._signals: list[Signal] = []
        super().__init__(event_bus)

    def get_view(self) -> ConvolutionView:
        if self._view is None:
            self._view = ConvolutionView(self._viewmodel)
        return self._view

    def _connect_events(self) -> None:
        self.event_bus.subscribe("signal:generated", self._on_signal)
        self.event_bus.subscribe("signal:loaded", self._on_signal)
        self.event_bus.subscribe("signal:operations_result", self._on_signal)

    def _on_signal(self, signal: Signal | None = None, **kwargs) -> None:
        if signal is not None:
            self._signals.append(signal)
            if self._view is not None:
                self._view.update_signal_list(self._signals)

    def cleanup(self) -> None:
        self._viewmodel.dispose()
        super().cleanup()
