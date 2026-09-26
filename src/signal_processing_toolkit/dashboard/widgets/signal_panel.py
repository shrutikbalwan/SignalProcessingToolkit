import pyqtgraph as pg
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class SignalPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Live signal"))
        self.plot = pg.PlotWidget(self)
        self.plot.setLabel("left", "Amplitude")
        self.plot.setLabel("bottom", "Sample")
        self.plot.showGrid(x=True, y=True, alpha=0.25)
        self.plot.setAccessibleName("Live signal plot")
        self.curve = self.plot.plot(pen=pg.mkPen("#4fc3f7", width=2))
        layout.addWidget(self.plot)

    def update_samples(self, samples: list[float]) -> None:
        self.curve.setData(samples)
