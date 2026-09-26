from PyQt6.QtWidgets import QApplication

from signal_processing_toolkit.dashboard.view import DashboardView


def test_dashboard_view_assembles_widgets_and_cleans_up(qapp: QApplication) -> None:
    view = DashboardView()
    assert view.objectName() == "dashboardPage"
    view.controller.start_demo()
    view.controller._tick()
    assert len(view.viewmodel.state.signal_samples) > 0
    assert len(view.viewmodel.state.spectrum) > 0
    view.controller.cleanup()
