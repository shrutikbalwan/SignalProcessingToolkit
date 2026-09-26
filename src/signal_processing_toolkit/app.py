from signal_processing_toolkit.config import settings
from signal_processing_toolkit.core.application import ApplicationLifecycle
from signal_processing_toolkit.core.events import EventBus
from signal_processing_toolkit.logger import get_logger
from signal_processing_toolkit.ui.controllers.main_controller import MainController
from signal_processing_toolkit.ui.main_window import MainWindow

logger = get_logger(__name__)


class Application:
    def __init__(self) -> None:
        self.event_bus = EventBus()
        self.lifecycle = ApplicationLifecycle()
        self.main_window: MainWindow | None = None
        self._shutdown = False

    def initialize(self) -> None:
        self._ensure_directories()

        logger.info(
            "Initializing Signal Processing Toolkit",
            extra={"version": settings.version, "debug": settings.debug},
        )

        self.lifecycle.initialize()
        self.event_bus.publish("app:initialized")

    def run(self) -> None:
        from PyQt6.QtWidgets import QApplication

        main_controller = MainController(self.event_bus)
        self.main_window = MainWindow(self.event_bus, main_controller=main_controller)
        qt_app = QApplication.instance()
        if isinstance(qt_app, QApplication):
            qt_app.aboutToQuit.connect(self.shutdown)
        self.main_window.show()
        self.event_bus.publish("app:started")
        logger.info("Application started")

    def shutdown(self) -> None:
        if self._shutdown:
            return
        self._shutdown = True
        if self.main_window is not None:
            self.main_window.main_controller.cleanup()
        self.lifecycle.shutdown()
        self.event_bus.clear()
        logger.info("Application stopped")

    def _ensure_directories(self) -> None:
        for dir_path in [
            settings.data_dir,
            settings.export_dir,
            settings.plugins_dir,
            settings.logs_dir,
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)
