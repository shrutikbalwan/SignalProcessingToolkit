from __future__ import annotations

import json

import pytest

pytest.importorskip("PyQt6")

from PyQt6.QtCore import Qt, QTimer

from signal_processing_toolkit.core.settings import SettingsManager


def test_live_monitor_can_start_stop_and_restart_without_duplicate_connections(
    main_window, qtbot
) -> None:
    monitor = main_window.main_controller.monitor
    assert not monitor.is_running
    assert monitor._timer.receivers(monitor._timer.timeout) == 1

    monitor.start()
    qtbot.waitUntil(lambda: monitor.update_count >= 1, timeout=1500)
    monitor.stop()
    stopped_count = monitor.update_count
    qtbot.wait(monitor.update_interval + 100)
    assert monitor.update_count == stopped_count

    monitor.start()
    qtbot.waitUntil(lambda: monitor.update_count > stopped_count, timeout=1500)
    monitor.stop()
    assert monitor._timer.receivers(monitor._timer.timeout) == 1


def test_live_monitor_keeps_qt_event_loop_responsive(main_window, qtbot) -> None:
    monitor = main_window.main_controller.monitor
    heartbeats = 0
    timer = QTimer()
    timer.setInterval(10)

    def beat() -> None:
        nonlocal heartbeats
        heartbeats += 1

    timer.timeout.connect(beat)
    timer.start()
    monitor.start()
    qtbot.waitUntil(lambda: monitor.update_count >= 3, timeout=2000)
    monitor.pause()
    paused_count = monitor.pipeline.metrics.produced_frames
    qtbot.wait(100)
    assert monitor.pipeline.metrics.produced_frames <= paused_count + 1
    monitor.resume()
    qtbot.waitUntil(
        lambda: monitor.pipeline.metrics.produced_frames > paused_count + 1,
        timeout=1000,
    )
    monitor.stop()
    timer.stop()
    assert heartbeats >= 10


def test_settings_and_theme_are_persisted(main_window, qtbot, tmp_path) -> None:
    settings_view = main_window.main_controller.settings.get_view()
    settings_view.theme_combo.setCurrentText("light")
    settings_view.sampling_rate_spin.setValue(48000)
    qtbot.mouseClick(settings_view.save_button, Qt.MouseButton.LeftButton)

    path = tmp_path / "settings.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["theme"] == "light"
    assert data["default_sampling_rate"] == 48000
    assert main_window.theme_manager.current_theme == "light"

    loaded = SettingsManager(path)
    loaded.load()
    assert loaded.theme == "light"
    assert loaded.get("default_sampling_rate") == 48000
