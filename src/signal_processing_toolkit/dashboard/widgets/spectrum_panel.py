import pyqtgraph as pg
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class SpectrumPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Spectrum"))
        self.plot = pg.PlotWidget(self)
        self.plot.setLabel("left", "Magnitude")
        self.plot.setLabel("bottom", "Bin")
        self.plot.showGrid(x=True, y=True, alpha=0.25)
        self.plot.setAccessibleName("Spectrum plot")
        self.curve = self.plot.plot(pen=pg.mkPen("#ffb74d", width=2))
        layout.addWidget(self.plot)

    def update_spectrum(self, spectrum: list[float]) -> None:
        self.curve.setData(spectrum)
