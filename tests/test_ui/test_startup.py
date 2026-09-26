from __future__ import annotations

import logging

import pytest

pytest.importorskip("PyQt6")

from signal_processing_toolkit.ui.components.sidebar import NAV_ITEMS


def test_headless_ui_startup_and_navigation_have_no_uncaught_errors(
    main_window, qtbot, caplog
) -> None:
    caplog.set_level(logging.ERROR)
    assert main_window.isVisible()
    assert main_window.stacked_widget.currentWidget() is main_window.pages["dashboard"]

    for row, descriptor in enumerate(NAV_ITEMS):
        main_window.sidebar.list_widget.setCurrentRow(row)
        qtbot.waitUntil(lambda expected=row: main_window.stacked_widget.currentIndex() == expected)
        assert main_window.stacked_widget.currentWidget() is main_window.pages[descriptor.key]

    assert not [record for record in caplog.records if record.levelno >= logging.ERROR]


def test_window_close_cleans_controllers_and_monitor(main_window, qtbot) -> None:
    main_window.main_controller.monitor.start()
    main_window.close()
    qtbot.waitUntil(lambda: main_window.main_controller.is_cleaned_up)
    assert not main_window.main_controller.monitor.is_running
