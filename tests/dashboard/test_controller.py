from PyQt6.QtWidgets import QApplication

from signal_processing_toolkit.dashboard.controller import DashboardController
from signal_processing_toolkit.dashboard.events import DashboardCommand
from signal_processing_toolkit.dashboard.state import SessionStatus, SourceType


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
