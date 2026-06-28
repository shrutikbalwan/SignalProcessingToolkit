from __future__ import annotations

from src.core.events import EventBus
from src.core.history import UndoRedoManager
from src.models.signal import Signal
from src.services.signal_service import SignalService
from src.ui.controllers.base_controller import BaseController
from src.ui.viewmodels.signal_operations_vm import SignalOperationsViewModel
from src.ui.views.signal_operations_view import SignalOperationsView


class SignalOperationsController(BaseController):
    def __init__(
        self,
        event_bus: EventBus,
        signal_service: SignalService,
        undo_manager: UndoRedoManager | None = None,
    ) -> None:
        self._signal_service = signal_service
        self._undo_manager = undo_manager or UndoRedoManager()
        self._viewmodel = SignalOperationsViewModel(signal_service, self._undo_manager)
        self._view: SignalOperationsView | None = None
        super().__init__(event_bus)

    def get_view(self) -> SignalOperationsView:
        if self._view is None:
            self._view = SignalOperationsView(self._viewmodel)
        return self._view

    def _connect_events(self) -> None:
        self.event_bus.subscribe("signal:generated", self._on_signal_generated)
        self.event_bus.subscribe("signal:loaded", self._on_signal_generated)

    def _on_signal_generated(self, signal: Signal | None = None, **kwargs) -> None:
        if signal is not None:
            signals = self._viewmodel.active_signals.value
            signals.append(signal)
            self._viewmodel.active_signals.value = signals
            if self._view is not None:
                self._view.update_signal_list(signals)

    def cleanup(self) -> None:
        self._viewmodel.dispose()
        super().cleanup()
