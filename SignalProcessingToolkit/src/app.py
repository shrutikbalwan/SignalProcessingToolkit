from src.config import settings
from src.core.application import ApplicationLifecycle
from src.core.events import EventBus
from src.logger import get_logger
from src.ui.controllers.main_controller import MainController
from src.ui.main_window import MainWindow

logger = get_logger(__name__)


class Application:
    def __init__(self) -> None:
        self.event_bus = EventBus()
        self.lifecycle = ApplicationLifecycle()
        self.main_window: MainWindow | None = None

    def initialize(self) -> None:
        self._ensure_directories()

        logger.info(
            "Initializing Signal Processing Toolkit",
            extra={"version": settings.version, "debug": settings.debug},
        )

        self.lifecycle.initialize()
        self.event_bus.publish("app:initialized")

    def run(self) -> None:
        main_controller = MainController(self.event_bus)
        self.main_window = MainWindow(self.event_bus, main_controller=main_controller)
        self.main_window.show()
        self.event_bus.publish("app:started")
        logger.info("Application started")

    def _ensure_directories(self) -> None:
        for dir_path in [
            settings.data_dir,
            settings.export_dir,
            settings.plugins_dir,
            settings.logs_dir,
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)
