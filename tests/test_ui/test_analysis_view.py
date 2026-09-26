from __future__ import annotations

import csv

import pytest

pytest.importorskip("PyQt6")


def test_analysis_region_runs_in_background_and_exports(
    main_window, sample_sine, qtbot, tmp_path
) -> None:
    controller = main_window.main_controller
    controller.state.set_current_signal(sample_sine, "test")
    view = controller.analysis
    view.window_length.setValue(128)
    view.overlap.setValue(96)
    view.fft_length.setValue(256)
    view.region.setRegion((0.2, 0.6))
    view.auto_threshold.setChecked(False)
    view.event_threshold.setValue(0.5)
    view.event_hysteresis.setValue(0.1)
    view.transient_prominence.setValue(1.0)

    assert view.analyze_region()
    assert view._tasks.is_busy
    assert not view.analyze_button.isEnabled()
    qtbot.waitUntil(lambda: view._result is not None, timeout=10000)
    qtbot.waitUntil(lambda: not view._tasks.is_busy)

    result = view._result
    assert result is not None
    assert result.selected_signal.start_time == pytest.approx(0.2)
    assert result.selected_signal.duration == pytest.approx(0.4)
    assert result.parameters["window_length"] == 128
    assert result.parameters["event_detection"]["threshold"] == pytest.approx(0.5)
    assert result.parameters["event_detection"]["hysteresis"] == pytest.approx(0.1)
    assert result.parameters["transient_detection"]["prominence"] == pytest.approx(1.0)
    assert view.measurements_table.rowCount() > 0
    assert view.parameters_table.rowCount() > 0
    assert "Parameters:" in view.stft_parameters.text()
    assert "transients=" in view.event_parameters.text()

    output = tmp_path / "measurements.csv"
    view.export_measurements(output)
    with output.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.reader(stream))
    assert ["measurement", "value"] in rows
    assert any(row and row[0] == "dominant_frequency_hz" for row in rows)


def test_analysis_time_cursors_are_linked(main_window, sample_sine) -> None:
    view = main_window.main_controller.analysis
    main_window.main_controller.state.set_current_signal(sample_sine, "test")
    view.cursors.time_line.setValue(0.35)
    assert view.cursors.tf_time_line.value() == pytest.approx(0.35)
    view.cursors.tf_time_line.setValue(0.7)
    assert view.cursors.time_line.value() == pytest.approx(0.7)
    view.cursors.frequency_line.setValue(125.0)
    assert view.cursors.spectrum_frequency_line.value() == pytest.approx(125.0)
    view.cursors.spectrum_frequency_line.setValue(250.0)
    assert view.cursors.frequency_line.value() == pytest.approx(250.0)
