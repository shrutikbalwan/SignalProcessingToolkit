"""Command-line entry point for Signal Processing Toolkit."""

from __future__ import annotations

import argparse
import ctypes
import sys
from collections.abc import Sequence
from pathlib import Path

from signal_processing_toolkit import __version__


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="spt",
        description="Launch the Signal Processing Toolkit desktop application.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def set_app_user_model_id() -> None:
    """Set the Windows application identifier when the platform supports it."""
    if sys.platform == "win32":
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "SignalProcessingToolkit.App.v1"
            )
        except (AttributeError, OSError):
            pass


def _run_gui() -> int:
    try:
        from PyQt6.QtGui import QIcon
        from PyQt6.QtWidgets import QApplication
    except ModuleNotFoundError as exc:
        if exc.name and exc.name.startswith("PyQt6"):
            print(
                "The desktop interface requires the 'gui' extra. "
                'Install it with: pip install "signal-processing-toolkit[gui]"',
                file=sys.stderr,
            )
            return 1
        raise

    # Application loads GUI code, so its import belongs behind the optional PyQt check.
    from signal_processing_toolkit.app import Application

    set_app_user_model_id()
    qt_app = QApplication(sys.argv)
    qt_app.setApplicationName("Signal Processing Toolkit")
    qt_app.setApplicationVersion(__version__)
    qt_app.setOrganizationName("Signal Processing Toolkit")

    icon_path = Path(__file__).parent / "resources" / "icons" / "app.ico"
    if icon_path.exists():
        qt_app.setWindowIcon(QIcon(str(icon_path)))

    application = Application()
    application.initialize()
    application.run()
    return int(qt_app.exec())


def main(argv: Sequence[str] | None = None) -> int:
    """Parse CLI arguments and launch the desktop application."""
    _build_parser().parse_args(argv)
    return _run_gui()


if __name__ == "__main__":
    raise SystemExit(main())
