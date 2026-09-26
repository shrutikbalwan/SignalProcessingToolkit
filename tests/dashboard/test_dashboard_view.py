from PyQt6.QtWidgets import QApplication

from signal_processing_toolkit.dashboard.view import DashboardView


def test_dashboard_view_assembles_widgets_and_cleans_up(qapp: QApplication) -> None:
    view = DashboardView()
    assert view.objectName() == "dashboardPage"
    view.controller.start_demo()
    view.controller._tick()
    assert view.signal_panel.status.text() != "No samples"
    view.controller.cleanup()
