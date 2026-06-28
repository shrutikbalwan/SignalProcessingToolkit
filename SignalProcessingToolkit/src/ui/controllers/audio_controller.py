from __future__ import annotations

from src.core.events import EventBus
from src.services.audio_service import AudioService
from src.ui.controllers.base_controller import BaseController
from src.ui.viewmodels.audio_vm import AudioViewModel
from src.ui.views.audio_view import AudioView


class AudioController(BaseController):
    def __init__(self, event_bus: EventBus) -> None:
        self._service = AudioService()
        self._viewmodel = AudioViewModel(self._service)
        self._view: AudioView | None = None
        super().__init__(event_bus)

    def get_view(self) -> AudioView:
        if self._view is None:
            self._view = AudioView(self._viewmodel)
        return self._view

    def cleanup(self) -> None:
        self._viewmodel.dispose()
        super().cleanup()
