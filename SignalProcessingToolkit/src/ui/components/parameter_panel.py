from __future__ import annotations

from PyQt6.QtWidgets import QWidget


class ParameterPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("parameterPanel")
