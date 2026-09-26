import numpy as np
import pyqtgraph as pg
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class SpectrogramPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Spectrogram"))
        self.plot = pg.PlotWidget(self)
        self.plot.setLabel("left", "Frame")
        self.plot.setLabel("bottom", "Frequency bin")
        self.plot.setAccessibleName("Streaming spectrogram")
        self.image = pg.ImageItem()
        self.plot.addItem(self.image)
        self._rows = np.empty((0, 0))
        layout.addWidget(self.plot)

    def update_spectrum(self, spectrum: list[float]) -> None:
        if not spectrum:
            return
        current = np.asarray(spectrum, dtype=float)
        if self._rows.shape[1:] != (len(current),):
            self._rows = np.empty((0, len(current)))
        self._rows = np.vstack((self._rows, current[None, :]))[-80:]
        self.image.setImage(self._rows, autoLevels=False)
