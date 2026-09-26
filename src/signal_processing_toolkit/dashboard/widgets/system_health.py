from PyQt6.QtWidgets import QFormLayout, QLabel, QWidget

from signal_processing_toolkit.dashboard.state import ProcessingHealth


class SystemHealth(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QFormLayout(self)
        self.latency = QLabel("—")
        self.queue = QLabel("—")
        self.drops = QLabel("—")
        layout.addRow("DSP latency", self.latency)
        layout.addRow("Queue depth", self.queue)
        layout.addRow("Dropped frames", self.drops)

    def update_health(self, health: ProcessingHealth) -> None:
        self.latency.setText(f"{health.processing_latency_ms:.2f} ms")
        self.queue.setText(str(health.queue_depth))
        self.drops.setText(str(health.dropped_frames))
