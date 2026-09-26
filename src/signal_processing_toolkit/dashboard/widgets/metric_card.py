from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class MetricCard(QWidget):
    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.title = QLabel(title)
        self.value = QLabel("—")
        self.value.setObjectName("metricValue")
        self.value.setAccessibleName(f"{title} value")
        layout.addWidget(self.title)
        layout.addWidget(self.value)

    def set_value(self, text: str) -> None:
        self.value.setText(text)
