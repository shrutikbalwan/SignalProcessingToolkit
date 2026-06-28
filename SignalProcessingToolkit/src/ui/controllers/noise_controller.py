from __future__ import annotations

from src.core.events import EventBus
from src.models.signal import Signal
from src.services.noise_service import NoiseService
from src.ui.controllers.base_controller import BaseController
from src.ui.viewmodels.noise_vm import NoiseViewModel
from src.ui.views.noise_view import NoiseView


class NoiseController(BaseController):
    def __init__(self, event_bus: EventBus) -> None:
        self._service = NoiseService()
        self._viewmodel = NoiseViewModel(self._service)
        self._view: NoiseView | None = None
        super().__init__(event_bus)

    def get_view(self) -> NoiseView:
        if self._view is None:
            self._view = NoiseView(self._viewmodel)
        return self._view

    def _connect_events(self) -> None:
        self.event_bus.subscribe("signal:generated", self._on_signal)
        self.event_bus.subscribe("signal:loaded", self._on_signal)

    def _on_signal(self, signal: Signal | None = None, **kwargs) -> None:
        if signal is not None and self._view is not None:
            self._view.set_input_signal(signal)

    def cleanup(self) -> None:
        self._viewmodel.dispose()
        super().cleanup()
