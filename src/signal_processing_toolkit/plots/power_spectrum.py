from __future__ import annotations

from signal_processing_toolkit.models.fft_result import FFTResult
from signal_processing_toolkit.plots.base import BasePlotWidget


class PowerSpectrumPlot(BasePlotWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent, title="Power Spectrum")
        self.set_labels(x_label="Frequency (Hz)", y_label="Power")

    def plot_power(self, result: FFTResult, name: str = "Power Spectrum") -> None:
        self.clear()
        positive = result.positive_spectrum
        power = positive.power
        assert power is not None
        self.plot(positive.frequencies, power, name=name)
        self.auto_range()
