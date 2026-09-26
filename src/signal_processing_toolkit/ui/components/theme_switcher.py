from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget


class ThemeSwitcher(QWidget):
    theme_changed = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("themeSwitcher")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.theme_label = QLabel("Theme:")
        self.theme_label.setStyleSheet("color: #0078d4; font-weight: bold;")
        layout.addWidget(self.theme_label)
        self.dark_btn = QPushButton("&Dark")
        self.dark_btn.setObjectName("primaryButton")
        self.dark_btn.setAccessibleName("Use dark theme")
        self.dark_btn.clicked.connect(lambda _checked=False: self.theme_changed.emit("dark"))
        layout.addWidget(self.dark_btn)
        self.light_btn = QPushButton("&Light")
        self.light_btn.setObjectName("secondaryButton")
        self.light_btn.setAccessibleName("Use light theme")
        self.light_btn.clicked.connect(lambda _checked=False: self.theme_changed.emit("light"))
        layout.addWidget(self.light_btn)
        layout.addStretch()
