from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from signal_processing_toolkit.dashboard.formatters import timestamp
from signal_processing_toolkit.dashboard.state import DashboardEvent


class EventTable(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(("Time", "Severity", "Type", "Description"))
        self.table.setAccessibleName("Dashboard events")
        layout.addWidget(self.table)

    def update_events(self, events: list[DashboardEvent]) -> None:
        self.table.setRowCount(len(events))
        for row, event in enumerate(events):
            for column, text in enumerate(
                (
                    timestamp(event.timestamp),
                    event.severity.value,
                    event.event_type,
                    event.description,
                )
            ):
                self.table.setItem(row, column, QTableWidgetItem(text))
