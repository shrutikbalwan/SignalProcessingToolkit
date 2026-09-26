from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class SpectrogramPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Spectrogram"))
        layout.addWidget(QLabel("Streaming view ready"))
