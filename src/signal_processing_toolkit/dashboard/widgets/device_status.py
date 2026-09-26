from PyQt6.QtWidgets import QFormLayout, QLabel, QWidget

from signal_processing_toolkit.dashboard.state import SourceState


class DeviceStatus(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QFormLayout(self)
        self.connection = QLabel("Disconnected")
        self.device = QLabel("No source")
        self.rate = QLabel("—")
        layout.addRow("Connection", self.connection)
        layout.addRow("Device", self.device)
        layout.addRow("Rate", self.rate)

    def update_source(self, source: SourceState) -> None:
        self.connection.setText(source.connection_status.value)
        self.device.setText(source.device_name)
        self.rate.setText(f"{source.sampling_rate:g} Hz" if source.sampling_rate else "—")
