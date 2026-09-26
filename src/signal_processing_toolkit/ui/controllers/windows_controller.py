from __future__ import annotations

from signal_processing_toolkit.core.events import EventBus
from signal_processing_toolkit.models.signal import Signal
from signal_processing_toolkit.services.window_service import WindowService
from signal_processing_toolkit.ui.controllers.base_controller import BaseController
from signal_processing_toolkit.ui.viewmodels.windows_vm import WindowViewModel
from signal_processing_toolkit.ui.views.windows_view import WindowView


class WindowController(BaseController):
    def __init__(self, event_bus: EventBus) -> None:
        self._service = WindowService()
        self._viewmodel = WindowViewModel(self._service)
        self._view: WindowView | None = None
        super().__init__(event_bus)

    def get_view(self) -> WindowView:
        if self._view is None:
            self._view = WindowView(self._viewmodel)
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
