from __future__ import annotations

from src.models.fft_result import FFTResult
from src.plots.base import BasePlotWidget


class FrequencyDomainPlot(BasePlotWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent, title="Frequency Domain")
        self.set_labels(x_label="Frequency (Hz)", y_label="Magnitude (dB)")

    def plot_spectrum(self, result: FFTResult, name: str = "Spectrum") -> None:
        self.clear()
        positive = result.positive_spectrum
        self.plot(positive.frequencies, positive.magnitude_db, name=name)
        self.auto_range()

    def plot_magnitude(self, result: FFTResult, name: str = "Magnitude") -> None:
        self.clear()
        positive = result.positive_spectrum
        self.plot(positive.frequencies, positive.magnitude, name=name)
        self.auto_range()
