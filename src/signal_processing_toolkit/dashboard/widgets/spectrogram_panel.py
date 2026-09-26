import numpy as np
import pyqtgraph as pg
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class SpectrogramPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Spectrogram"))
        self.image = pg.ImageView(self)
        self.image.ui.histogram.hide()
        self.image.ui.roiBtn.hide()
        self.image.ui.menuBtn.hide()
        self.image.setAccessibleName("Streaming spectrogram")
        self._rows = np.empty((0, 0))
        layout.addWidget(self.image)

    def update_spectrum(self, spectrum: list[float]) -> None:
        if not spectrum:
            return
        current = np.asarray(spectrum, dtype=float)
        if self._rows.shape[1:] != (len(current),):
            self._rows = np.empty((0, len(current)))
        self._rows = np.vstack((self._rows, current[None, :]))[-80:]
        self.image.setImage(self._rows, autoLevels=False, autoRange=False)
