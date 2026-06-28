from __future__ import annotations

from PyQt6.QtWidgets import QLabel, QStatusBar


class StatusBar(QStatusBar):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("statusBar")

        self.signal_info = QLabel("No signal loaded")
        self.sampling_info = QLabel("")
        self.view_info = QLabel("")

        self.addWidget(self.signal_info, 1)
        self.addPermanentWidget(self.sampling_info)
        self.addPermanentWidget(self.view_info)

    def set_signal_info(self, text: str) -> None:
        self.signal_info.setText(text)

    def set_sampling_info(self, text: str) -> None:
        self.sampling_info.setText(text)

    def set_view_info(self, text: str) -> None:
        self.view_info.setText(text)
