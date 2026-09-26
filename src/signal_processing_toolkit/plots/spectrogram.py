from __future__ import annotations

import numpy as np
import pyqtgraph as pg
from PyQt6.QtWidgets import QVBoxLayout, QWidget

from signal_processing_toolkit.dsp.analysis import STFTConfig, stft
from signal_processing_toolkit.models.signal import Signal
from signal_processing_toolkit.plots.themes import DARK_THEME, PlotTheme


class SpectrogramPlot(QWidget):
    def __init__(self, parent=None, theme: PlotTheme | None = None) -> None:
        super().__init__(parent)
        self._theme = theme or DARK_THEME
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        pg.setConfigOptions(antialias=True)
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground(self._theme.background)
        self.img_item = pg.ImageItem()
        self.plot_widget.addItem(self.img_item)
        self.plot_widget.setLabel("bottom", "Time (s)")
        self.plot_widget.setLabel("left", "Frequency (Hz)")

        self.color_bar = pg.ColorBarItem(
            values=(0, 1),
            colorMap=pg.colormap.get("inferno"),
        )
        self.color_bar.setImageItem(self.img_item)

        layout.addWidget(self.plot_widget)

    def plot(self, signal: Signal, nperseg: int = 256) -> None:
        self.display(self.compute_data(signal, nperseg))

    @staticmethod
    def compute_data(signal: Signal, nperseg: int = 256) -> tuple[np.ndarray, ...]:
        result = stft(
            signal,
            STFTConfig(
                window_length=min(nperseg, signal.n_samples),
                overlap=min(nperseg // 2, max(0, signal.n_samples - 1)),
                fft_length=nperseg,
                scaling="psd",
                boundary=None,
                padded=False,
            ),
        )
        power = result.power
        if power.ndim == 3:
            power = power[:, :, 0]
        return result.frequencies, result.times, power

    def display(self, data: tuple[np.ndarray, ...]) -> None:
        frequencies, times, sxx = data
        self.img_item.setImage(np.log10(sxx + 1e-10))
        self.img_item.setRect(
            0,
            frequencies[0],
            times[-1] - times[0],
            frequencies[-1] - frequencies[0],
        )
        self.plot_widget.autoRange()
