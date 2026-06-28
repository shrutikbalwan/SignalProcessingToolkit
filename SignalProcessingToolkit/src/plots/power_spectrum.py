from __future__ import annotations

from src.models.fft_result import FFTResult
from src.plots.base import BasePlotWidget


class PowerSpectrumPlot(BasePlotWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent, title="Power Spectrum")
        self.set_labels(x_label="Frequency (Hz)", y_label="Power")

    def plot_power(self, result: FFTResult, name: str = "Power Spectrum") -> None:
        self.clear()
        positive = result.positive_spectrum
        power = positive.magnitude**2
        self.plot(positive.frequencies, power, name=name)
        self.auto_range()
