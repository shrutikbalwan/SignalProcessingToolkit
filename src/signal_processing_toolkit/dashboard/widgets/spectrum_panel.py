from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class SpectrumPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Spectrum"))
        self.status = QLabel("Waiting for signal")
        layout.addWidget(self.status)

    def update_spectrum(self, spectrum: list[float]) -> None:
        self.status.setText(f"{len(spectrum)} bins") if spectrum else self.status.setText(
            "Waiting for signal"
        )
