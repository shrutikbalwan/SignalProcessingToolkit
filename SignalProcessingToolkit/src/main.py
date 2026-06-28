import ctypes
import sys
from pathlib import Path

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from src.app import Application


def set_app_user_model_id() -> None:
    app_id = "SignalProcessingToolkit.App.v1"
    if sys.platform == "win32":
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
        except (AttributeError, OSError):
            pass


def main() -> None:
    set_app_user_model_id()

    app = QApplication(sys.argv)
    app.setApplicationName("Signal Processing Toolkit")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("SPT")

    icon_path = Path(__file__).parent.parent / "assets" / "icons" / "app.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    application = Application()
    application.initialize()
    application.run()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
