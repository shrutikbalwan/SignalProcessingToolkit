"""Source-selection controls; device construction stays in the controller."""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QPushButton, QWidget


class SourceSelector(QWidget):
    source_requested = pyqtSignal(str)
    replay_requested = pyqtSignal()
    refresh_requested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.addWidget(QLabel("Source"))
        self.source = QComboBox(self)
        self.source.addItem("Demo", "demo")
        self.source.addItem("Audio input", "audio")
        self.source.addItem("Serial sensor", "serial")
        self.source.addItem("Replay", "replay")
        self.source.setAccessibleName("Signal source")
        layout.addWidget(self.source)
        self.refresh = QPushButton("Connect")
        self.refresh.setAccessibleName("Connect selected source")
        self.refresh.clicked.connect(
            lambda: self.source_requested.emit(str(self.source.currentData()))
        )
        layout.addWidget(self.refresh)
        self.refresh_devices = QPushButton("Refresh")
        self.refresh_devices.setAccessibleName("Refresh source devices")
        self.refresh_devices.clicked.connect(self.refresh_requested)
        layout.addWidget(self.refresh_devices)
        self.open_replay = QPushButton("Open replay")
        self.open_replay.setAccessibleName("Open recorded replay")
        self.open_replay.clicked.connect(self.replay_requested)
        layout.addWidget(self.open_replay)

    @property
    def selected_source(self) -> str:
        return str(self.source.currentData())
