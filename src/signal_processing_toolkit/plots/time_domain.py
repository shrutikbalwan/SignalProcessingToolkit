from __future__ import annotations

from signal_processing_toolkit.models.signal import Signal
from signal_processing_toolkit.plots.base import BasePlotWidget


class TimeDomainPlot(BasePlotWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent, title="Time Domain")
        self.set_labels(x_label="Time (s)", y_label="Amplitude")

    def plot_signal(self, signal: Signal, name: str = "Signal") -> None:
        self.clear()
        self._plot_channels(signal, name)
        self.auto_range()

    def plot_multiple(self, signals: list[Signal], names: list[str] | None = None) -> None:
        self.clear()
        for i, signal in enumerate(signals):
            label = names[i] if names and i < len(names) else f"Signal {i + 1}"
            color = self._theme.line_colors[i % len(self._theme.line_colors)]
            if signal.is_mono:
                self.plot(signal.time_vector, signal.time_data, name=label, color=color)
            else:
                self._plot_channels(signal, label, color_offset=i)
        self.auto_range()

    def _plot_channels(self, signal: Signal, name: str, color_offset: int = 0) -> None:
        if signal.is_mono:
            self.plot(signal.time_vector, signal.time_data, name=name)
            return
        for channel, channel_name in enumerate(signal.channel_names or ()):
            color = self._theme.line_colors[(color_offset + channel) % len(self._theme.line_colors)]
            self.plot(
                signal.time_vector,
                signal.time_data[:, channel],
                name=f"{name}: {channel_name}",
                color=color,
            )
