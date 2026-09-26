from PyQt6.QtWidgets import QApplication

from signal_processing_toolkit.dashboard.state import DashboardEvent, EventSeverity
from signal_processing_toolkit.dashboard.widgets.event_table import EventTable


def test_event_table_updates(qapp: QApplication) -> None:
    table = EventTable()
    table.update_events([DashboardEvent(severity=EventSeverity.WARNING, description="test event")])
    assert table.table.rowCount() == 1
    assert table.table.item(0, 3).text() == "test event"
