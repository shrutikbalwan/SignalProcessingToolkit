from __future__ import annotations

from src.core.events import EventBus
from src.models.project import Project
from src.models.signal import Signal
from src.services.export_service import ExportService
from src.ui.controllers.base_controller import BaseController
from src.ui.viewmodels.export_vm import ExportViewModel


class ExportController(BaseController):
    def __init__(self, event_bus: EventBus) -> None:
        self._service = ExportService()
        self._viewmodel = ExportViewModel(self._service)
        super().__init__(event_bus)

    def get_viewmodel(self) -> ExportViewModel:
        return self._viewmodel

    def _connect_events(self) -> None:
        self.event_bus.subscribe("signal:generated", self._on_signal)
        self.event_bus.subscribe("signal:loaded", self._on_signal)
        self.event_bus.subscribe("signal:operations_result", self._on_signal)
        self.event_bus.subscribe("project:new", self._on_new_project)

    def _on_signal(self, signal: Signal | None = None, **kwargs) -> None:
        if signal is not None:
            self._viewmodel.signal.value = signal

    def _on_new_project(self, **kwargs) -> None:
        project = Project(name="Untitled Project")
        self._viewmodel.project.value = project

    def cleanup(self) -> None:
        self._viewmodel.dispose()
        super().cleanup()
