from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QWidget


class ControlBar(QWidget):
    start_requested = pyqtSignal()
    pause_requested = pyqtSignal()
    resume_requested = pyqtSignal()
    stop_requested = pyqtSignal()
    record_requested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        for label, signal, name in (
            ("Start", self.start_requested, "Start session"),
            ("Pause", self.pause_requested, "Pause session"),
            ("Resume", self.resume_requested, "Resume session"),
            ("Stop", self.stop_requested, "Stop session"),
            ("Record", self.record_requested, "Toggle recording"),
        ):
            button = QPushButton(label)
            button.setAccessibleName(name)
            button.clicked.connect(signal)
            layout.addWidget(button)
        layout.addStretch()
