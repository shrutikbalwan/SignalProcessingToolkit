from __future__ import annotations

from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
)

from src.ui.styles.theme_manager import ThemeManager


class ThemeSwitcher(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("themeSwitcher")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.theme_label = QLabel("Theme:")
        self.theme_label.setStyleSheet("color: #0078d4; font-weight: bold;")
        layout.addWidget(self.theme_label)

        self.dark_btn = QPushButton("Dark")
        self.dark_btn.setObjectName("primaryButton")
        self.dark_btn.clicked.connect(self._switch_to_dark)
        layout.addWidget(self.dark_btn)

        self.light_btn = QPushButton("Light")
        self.light_btn.setObjectName("secondaryButton")
        self.light_btn.clicked.connect(self._switch_to_light)
        layout.addWidget(self.light_btn)

        layout.addStretch()

        self.theme_manager = ThemeManager()

    def _switch_to_dark(self) -> None:
        self.theme_manager.set_theme("dark")
        self._apply_theme()

    def _switch_to_light(self) -> None:
        self.theme_manager.set_theme("light")
        self._apply_theme()

    def _apply_theme(self) -> None:
        app = QApplication.instance()
        if app:
            self.theme_manager.apply_theme(self)
