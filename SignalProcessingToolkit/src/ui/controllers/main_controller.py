from __future__ import annotations

from src.core.events import EventBus
from src.core.history import UndoRedoManager
from src.services.signal_service import SignalService
from src.ui.controllers.audio_controller import AudioController
from src.ui.controllers.convolution_controller import ConvolutionController
from src.ui.controllers.correlation_controller import CorrelationController
from src.ui.controllers.export_controller import ExportController
from src.ui.controllers.fft_controller import FFTController
from src.ui.controllers.filters_controller import FilterController
from src.ui.controllers.image_controller import ImageController
from src.ui.controllers.noise_controller import NoiseController
from src.ui.controllers.sampling_controller import SamplingController
from src.ui.controllers.settings_controller import SettingsController
from src.ui.controllers.signal_generator_controller import SignalGeneratorController
from src.ui.controllers.signal_operations_controller import SignalOperationsController
from src.ui.controllers.windows_controller import WindowController


class MainController:
    def __init__(self, event_bus: EventBus) -> None:
        self.event_bus = event_bus
        self.signal_service = SignalService()
        self.undo_manager = UndoRedoManager()

        self.signal_generator = SignalGeneratorController(event_bus, self.signal_service)
        self.signal_operations = SignalOperationsController(
            event_bus, self.signal_service, self.undo_manager
        )
        self.sampling = SamplingController(event_bus)
        self.convolution = ConvolutionController(event_bus)
        self.correlation = CorrelationController(event_bus)
        self.fft = FFTController(event_bus)
        self.windows = WindowController(event_bus)
        self.filters = FilterController(event_bus)
        self.noise = NoiseController(event_bus)
        self.audio = AudioController(event_bus)
        self.image = ImageController(event_bus)
        self.export = ExportController(event_bus)
        self.settings = SettingsController(event_bus)

    def get_views(self) -> list[tuple[str, object]]:
        return [
            ("dashboard", None),
            ("generator", self.signal_generator.get_view()),
            ("operations", self.signal_operations.get_view()),
            ("sampling", self.sampling.get_view()),
            ("convolution", self.convolution.get_view()),
            ("correlation", self.correlation.get_view()),
            ("fft", self.fft.get_view()),
            ("windows", self.windows.get_view()),
            ("filters", self.filters.get_view()),
            ("noise", self.noise.get_view()),
            ("audio", self.audio.get_view()),
            ("image", self.image.get_view()),
        ]

    def cleanup(self) -> None:
        self.signal_generator.cleanup()
        self.signal_operations.cleanup()
        self.sampling.cleanup()
        self.convolution.cleanup()
        self.correlation.cleanup()
        self.fft.cleanup()
        self.windows.cleanup()
        self.filters.cleanup()
        self.noise.cleanup()
        self.audio.cleanup()
        self.image.cleanup()
        self.export.cleanup()
