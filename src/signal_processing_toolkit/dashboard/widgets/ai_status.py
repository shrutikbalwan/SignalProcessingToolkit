from PyQt6.QtWidgets import QFormLayout, QLabel, QWidget

from signal_processing_toolkit.dashboard.formatters import percentage
from signal_processing_toolkit.dashboard.state import AIState


class AIStatus(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QFormLayout(self)
        self.model = QLabel("No model loaded")
        self.prediction = QLabel("—")
        self.confidence = QLabel("—")
        layout.addRow("Model", self.model)
        layout.addRow("Prediction", self.prediction)
        layout.addRow("Confidence", self.confidence)

    def update_ai(self, ai: AIState) -> None:
        self.model.setText(ai.model_name)
        self.prediction.setText(ai.predicted_class)
        self.confidence.setText(percentage(ai.confidence))
