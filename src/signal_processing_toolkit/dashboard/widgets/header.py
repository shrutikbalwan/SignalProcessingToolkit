from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget


class DashboardHeader(QWidget):
    demo_requested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        self.title = QLabel("Signal Processing Workbench")
        self.title.setObjectName("dashboardTitle")
        layout.addWidget(self.title)
        layout.addStretch()
        button = QPushButton("Demo Mode")
        button.setAccessibleName("Start demo mode")
        button.clicked.connect(self.demo_requested)
        layout.addWidget(button)
