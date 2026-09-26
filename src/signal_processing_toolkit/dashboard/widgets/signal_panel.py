from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class SignalPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Live signal"))
        self.status = QLabel("No samples")
        self.status.setAccessibleName("Live signal status")
        layout.addWidget(self.status)

    def update_samples(self, samples: list[float]) -> None:
        self.status.setText(f"{len(samples)} samples") if samples else self.status.setText(
            "No samples"
        )
