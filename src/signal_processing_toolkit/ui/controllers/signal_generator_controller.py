from __future__ import annotations

from signal_processing_toolkit.core.events import EventBus
from signal_processing_toolkit.services.signal_service import SignalService
from signal_processing_toolkit.ui.controllers.base_controller import BaseController
from signal_processing_toolkit.ui.viewmodels.signal_generator_vm import SignalGeneratorViewModel
from signal_processing_toolkit.ui.views.signal_generator_view import SignalGeneratorView


class SignalGeneratorController(BaseController):
    def __init__(self, event_bus: EventBus, signal_service: SignalService) -> None:
        self._viewmodel = SignalGeneratorViewModel(signal_service)
        self._view: SignalGeneratorView | None = None
        super().__init__(event_bus)

    def get_view(self) -> SignalGeneratorView:
        if self._view is None:
            self._view = SignalGeneratorView(self._viewmodel)
        return self._view

    def _connect_events(self) -> None:
        self.event_bus.subscribe("signal:generate", self._on_generate_event)
        self.event_bus.subscribe("signal:export", self._on_export_event)

    def _on_generate_event(self, **kwargs) -> None:
        if self._view is not None:
            self._view._on_generate()

    def _on_export_event(self, **kwargs) -> None:
        if self._view is not None:
            self._view._on_export()

    def cleanup(self) -> None:
        self._viewmodel.dispose()
        super().cleanup()
