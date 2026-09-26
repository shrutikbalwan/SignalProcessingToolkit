from __future__ import annotations

from signal_processing_toolkit.core.events import EventBus
from signal_processing_toolkit.services.image_service import ImageService
from signal_processing_toolkit.ui.controllers.base_controller import BaseController
from signal_processing_toolkit.ui.viewmodels.image_vm import ImageViewModel
from signal_processing_toolkit.ui.views.image_view import ImageView


class ImageController(BaseController):
    def __init__(self, event_bus: EventBus) -> None:
        self._service = ImageService()
        self._viewmodel = ImageViewModel(self._service)
        self._view: ImageView | None = None
        super().__init__(event_bus)

    def get_view(self) -> ImageView:
        if self._view is None:
            self._view = ImageView(self._viewmodel)
        return self._view

    def cleanup(self) -> None:
        self._viewmodel.dispose()
        super().cleanup()
