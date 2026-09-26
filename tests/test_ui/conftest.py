from __future__ import annotations

import logging

import pytest

pytest.importorskip("PyQt6")
pytest.importorskip("pyqtgraph")

from signal_processing_toolkit.core.events import EventBus
from signal_processing_toolkit.ui.controllers.main_controller import MainController
from signal_processing_toolkit.ui.main_window import MainWindow


@pytest.fixture
def main_window(qtbot, tmp_path):
    event_bus = EventBus()
    controller = MainController(event_bus, settings_path=tmp_path / "settings.json")
    window = MainWindow(event_bus, controller)
    qtbot.addWidget(window)
    window.show()
    yield window
    window.close()


@pytest.fixture(autouse=True)
def fail_on_qt_errors(caplog):
    caplog.set_level(logging.ERROR)
    yield
    failures = [record for record in caplog.records if record.levelno >= logging.ERROR]
    assert not failures, "\n".join(record.getMessage() for record in failures)
