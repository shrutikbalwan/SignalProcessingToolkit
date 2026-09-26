from PyQt6.QtWidgets import QApplication

from signal_processing_toolkit.dashboard.controller import DashboardController
from signal_processing_toolkit.dashboard.events import DashboardCommand
from signal_processing_toolkit.dashboard.state import SessionStatus, SourceType
from signal_processing_toolkit.streaming.sources import SyntheticSource


def test_demo_start_stop_and_restart(qapp: QApplication) -> None:
    controller = DashboardController()
    controller.dispatch(DashboardCommand.DEMO_MODE)
    controller._tick()
    assert controller.viewmodel.state.source.source_type is SourceType.DEMO
    assert controller.viewmodel.state.session.status is SessionStatus.RUNNING
    assert controller.viewmodel.state.signal_samples
    controller.stop()
    controller.start_demo()
    assert controller.timer_active
    controller.cleanup()
    assert not controller.timer_active


def test_recording_and_ai_updates(qapp: QApplication) -> None:
    controller = DashboardController()
    controller.start_demo()
    controller.dispatch(DashboardCommand.TOGGLE_RECORDING)
    controller._tick()
    assert controller.viewmodel.state.recording.active
    assert controller.viewmodel.state.recording.samples_written > 0
    controller.set_ai_prediction("healthy", 0.95)
    assert controller.viewmodel.state.ai.predicted_class == "healthy"
    assert controller.viewmodel.state.events[-1].event_type == "ai_prediction"
    controller.cleanup()


def test_external_stream_source_uses_dashboard_state_path(qapp: QApplication) -> None:
    controller = DashboardController()
    controller.attach_source(
        SyntheticSource(real_time=False, chunk_size=32), SourceType.REPLAY, "fake replay"
    )
    controller.start_source()
    for _ in range(20):
        controller._tick()
        if controller.viewmodel.state.signal_samples:
            break
    assert controller.viewmodel.state.source.device_name == "fake replay"
    assert controller.viewmodel.state.signal_samples
    assert controller.viewmodel.state.spectrum
    controller.cleanup()
