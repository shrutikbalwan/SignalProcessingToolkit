from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QLabel, QListWidget, QListWidgetItem, QVBoxLayout, QWidget

NAV_ITEMS = [
    ("Dashboard", "dashboard"),
    ("Signal Generator", "generator"),
    ("Signal Operations", "operations"),
    ("Sampling", "sampling"),
    ("Convolution", "convolution"),
    ("Correlation", "correlation"),
    ("FFT Analysis", "fft"),
    ("Window Functions", "windows"),
    ("Digital Filters", "filters"),
    ("Noise Processing", "noise"),
    ("Audio", "audio"),
    ("Image Processing", "image"),
    ("Settings", "settings"),
]


class Sidebar(QWidget):
    navigation_changed = pyqtSignal(int, str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(220)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QLabel("  Signal Toolkit")
        header.setObjectName("sidebarHeader")
        header.setFixedHeight(48)
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        header.setFont(font)
        layout.addWidget(header)

        self.list_widget = QListWidget()
        self.list_widget.setObjectName("sidebarList")
        self.list_widget.setSpacing(2)

        for display_name, _ in NAV_ITEMS:
            item = QListWidgetItem(display_name)
            self.list_widget.addItem(item)

        self.list_widget.currentRowChanged.connect(self._on_item_changed)
        self.list_widget.setCurrentRow(0)

        layout.addWidget(self.list_widget)

    def _on_item_changed(self, row: int) -> None:
        if 0 <= row < len(NAV_ITEMS):
            _, name = NAV_ITEMS[row]
            self.navigation_changed.emit(row, name)
