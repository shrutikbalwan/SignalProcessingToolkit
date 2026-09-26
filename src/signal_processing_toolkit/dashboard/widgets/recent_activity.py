from PyQt6.QtWidgets import QLabel, QListWidget, QVBoxLayout, QWidget

from signal_processing_toolkit.dashboard.state import DashboardEvent


class RecentActivity(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Recent activity"))
        self.list = QListWidget()
        layout.addWidget(self.list)

    def update_events(self, events: list[DashboardEvent]) -> None:
        self.list.clear()
        for event in events[-10:]:
            self.list.addItem(f"{event.severity.value}: {event.description}")
