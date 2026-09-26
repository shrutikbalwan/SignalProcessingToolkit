from __future__ import annotations

import pytest

pytest.importorskip("PyQt6")

from PyQt6.QtCore import Qt


def test_generated_signal_propagates_to_analysis_and_export(main_window, qtbot) -> None:
    controller = main_window.main_controller
    generator = controller.signal_generator.get_view()
    qtbot.mouseClick(generator.generate_btn, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: controller.state.current_signal is not None)
    signal = controller.state.current_signal

    assert controller.fft._viewmodel.input_signal.value is signal
    assert controller.filters._viewmodel.input_signal.value is signal
    assert controller.sampling._viewmodel.input_signal.value is signal
    assert controller.noise._viewmodel.input_signal.value is signal
    assert controller.analysis._signal is signal
    assert controller.edge_ai._input_signal is signal
    assert controller.convolution._viewmodel.input_signal.value is signal
    assert controller.convolution._viewmodel.kernel_signal.value is signal
    assert controller.correlation._viewmodel.input_a.value is signal
    assert controller.correlation._viewmodel.input_b.value is signal
    assert controller.export.get_viewmodel().signal.value is signal
    assert controller.signal_operations._viewmodel.active_signals.value == [signal]
    assert controller.dashboard.state_stack.currentIndex() == 3


def test_signal_pages_move_from_empty_to_content(main_window, sample_sine) -> None:
    controller = main_window.main_controller
    assert all(page.state == "empty" for page in controller._stateful_pages.values())
    controller.state.set_current_signal(sample_sine, "test")
    assert all(page.state == "content" for page in controller._stateful_pages.values())


def test_loaded_signal_event_updates_the_shared_state(main_window, sample_sine) -> None:
    main_window.event_bus.publish("signal:loaded", signal=sample_sine, source="file")
    assert main_window.main_controller.state.current_signal is sample_sine
    assert main_window.main_controller.fft._viewmodel.input_signal.value is sample_sine


def test_signal_pages_expose_loading_and_error_states(main_window) -> None:
    controller = main_window.main_controller
    main_window.event_bus.publish("signal:loading")
    assert all(page.state == "loading" for page in controller._stateful_pages.values())
    main_window.event_bus.publish("signal:error", message="Unreadable signal")
    assert all(page.state == "error" for page in controller._stateful_pages.values())
