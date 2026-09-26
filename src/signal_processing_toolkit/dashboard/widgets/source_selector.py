"""Source-selection controls; device construction stays in the controller."""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QWidget,
)


class SourceSelector(QWidget):
    source_requested = pyqtSignal(str)
    configuration_requested = pyqtSignal(float, int, str, str)
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
        self.rate = QDoubleSpinBox(self)
        self.rate.setRange(1.0, 192_000.0)
        self.rate.setValue(1_000.0)
        self.rate.setSuffix(" Hz")
        self.rate.setAccessibleName("Source sampling rate")
        layout.addWidget(self.rate)
        self.channels = QSpinBox(self)
        self.channels.setRange(1, 32)
        self.channels.setValue(1)
        self.channels.setAccessibleName("Source channels")
        layout.addWidget(self.channels)
        self.port = QLineEdit(self)
        self.port.setPlaceholderText("Serial port")
        self.port.setAccessibleName("Serial port")
        layout.addWidget(self.port)
        self.device = QComboBox(self)
        self.device.setAccessibleName("Discovered source device")
        self.device.setMinimumWidth(180)
        layout.addWidget(self.device)
        self.refresh = QPushButton("Connect")
        self.refresh.setAccessibleName("Connect selected source")
        self.refresh.clicked.connect(self._request_source)
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

    def _request_source(self) -> None:
        self.configuration_requested.emit(
            self.rate.value(),
            self.channels.value(),
            self.port.text().strip(),
            str(self.device.currentData() or ""),
        )
        self.source_requested.emit(self.selected_source)

    def update_devices(self, devices: list[tuple[str, str]]) -> None:
        self.device.clear()
        for label, identifier in devices:
            self.device.addItem(label, identifier)
