from __future__ import annotations

from src.models.signal import Signal
from src.plots.base import BasePlotWidget


class TimeDomainPlot(BasePlotWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent, title="Time Domain")
        self.set_labels(x_label="Time (s)", y_label="Amplitude")

    def plot_signal(self, signal: Signal, name: str = "Signal") -> None:
        self.clear()
        self.plot(signal.time_vector, signal.time_data, name=name)
        self.auto_range()

    def plot_multiple(self, signals: list[Signal], names: list[str] | None = None) -> None:
        self.clear()
        for i, signal in enumerate(signals):
            label = names[i] if names and i < len(names) else f"Signal {i + 1}"
            color = self._theme.line_colors[i % len(self._theme.line_colors)]
            self.plot(signal.time_vector, signal.time_data, name=label, color=color)
        self.auto_range()
