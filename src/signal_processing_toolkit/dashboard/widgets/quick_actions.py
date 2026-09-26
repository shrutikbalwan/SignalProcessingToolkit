from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QPushButton, QVBoxLayout, QWidget


class QuickActions(QWidget):
    demo_requested = pyqtSignal()
    record_requested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        demo = QPushButton("Start Demo Mode")
        demo.setAccessibleName("Start demo mode")
        demo.clicked.connect(self.demo_requested)
        record = QPushButton("Toggle Recording")
        record.setAccessibleName("Toggle recording")
        record.clicked.connect(self.record_requested)
        layout.addWidget(demo)
        layout.addWidget(record)
