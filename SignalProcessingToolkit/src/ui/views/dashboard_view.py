from __future__ import annotations

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from src.ui.components.cards.metric_card import MetricCard
from src.ui.components.cards.plot_card import PlotCard
from src.ui.components.cards.signal_card import SignalCard
from src.ui.components.widgets.parameter_slider import ParameterSlider
from src.ui.components.widgets.parameter_spinbox import ParameterSpinbox
from src.ui.components.widgets.waveform_selector import WaveformSelector


class ProfessionalDashboard(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("dashboard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        self._add_header(layout)
        self._add_metrics_row(layout)
        self._add_main_content_row(layout)
        self._add_recent_signals_section(layout)

    def _add_header(self, layout: QVBoxLayout) -> None:
        header = QWidget()
        header_layout = QHBoxLayout(header)

        title = QLabel("Professional Signal Processing Dashboard")
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #0078d4;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        timestamp = QLabel("Last updated: Just now")
        timestamp.setStyleSheet("color: #666; font-size: 14px;")
        header_layout.addWidget(timestamp)

        layout.addWidget(header)

    def _add_metrics_row(self, layout: QVBoxLayout) -> None:
        metrics_row = QWidget()
        metrics_layout = QHBoxLayout(metrics_row)
        metrics_layout.setSpacing(15)

        self.frequency_card = MetricCard("Frequency", "440.00", "Hz", "⚡", "#0078d4")
        metrics_layout.addWidget(self.frequency_card)

        self.amplitude_card = MetricCard("Amplitude", "0.85", "", "📊", "#10a16b")
        metrics_layout.addWidget(self.amplitude_card)

        self.duration_card = MetricCard("Duration", "2.00", "s", "⏱️", "#d83b01")
        metrics_layout.addWidget(self.duration_card)

        self.sampling_card = MetricCard("Sampling Rate", "44100", "Hz", "🔄", "#6264a7")
        metrics_layout.addWidget(self.sampling_card)

        self.rms_card = MetricCard("RMS Value", "0.6325", "", "📈", "#8764b8")
        metrics_layout.addWidget(self.rms_card)

        layout.addWidget(metrics_row)

    def _add_main_content_row(self, layout: QVBoxLayout) -> None:
        content_row = QWidget()
        content_row_layout = QHBoxLayout(content_row)
        content_row_layout.setSpacing(15)

        self.plot_card = PlotCard("Live Signal Plot", None)
        content_row_layout.addWidget(self.plot_card, stretch=2)

        param_panel = QWidget()
        param_layout = QVBoxLayout(param_panel)
        param_layout.setSpacing(10)

        waveform_selector = WaveformSelector()
        param_layout.addWidget(waveform_selector)

        param_slider = ParameterSlider("Frequency", 1.0, 10000.0, 440.0)
        param_layout.addWidget(param_slider)

        param_spinbox = ParameterSpinbox("Amplitude", 0.1, 10.0, 1.0, 0.1)
        param_layout.addWidget(param_spinbox)

        content_row_layout.addWidget(param_panel, stretch=1)

        layout.addWidget(content_row)

    def _add_recent_signals_section(self, layout: QVBoxLayout) -> None:
        recent_section = QWidget()
        recent_layout = QVBoxLayout(recent_section)

        title = QLabel("Recent Signals")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("padding: 10px 0;")
        recent_layout.addWidget(title)

        signals_container = QWidget()
        signals_layout = QHBoxLayout(signals_container)
        signals_layout.setSpacing(10)

        self.sine_card = SignalCard(
            "Sine Wave",
            "Sine_440Hz",
            "Duration: 2.00s, 44100Hz sampling",
        )
        signals_layout.addWidget(self.sine_card)

        self.cosine_card = SignalCard(
            "Cosine Wave",
            "Cos_1000Hz",
            "Duration: 2.00s, 44100Hz sampling",
        )
        signals_layout.addWidget(self.cosine_card)

        self.square_card = SignalCard(
            "Square Wave",
            "Square_220Hz",
            "Duration: 2.00s, 44100Hz sampling",
        )
        signals_layout.addWidget(self.square_card)

        signals_layout.addStretch()
        recent_layout.addWidget(signals_container)

        layout.addWidget(recent_section, stretch=1)

    def update_metrics(self, signal=None) -> None:
        if signal:
            self.frequency_card.update_value(signal.frequency, "Hz")
            self.amplitude_card.update_value(signal.amplitude)
            self.duration_card.update_value(signal.duration, "s")
            self.sampling_card.update_value(signal.sampling_rate, "Hz")
            if hasattr(signal, "rms"):
                self.rms_card.update_value(signal.rms)

    def update_plot_card(self, plot_widget) -> None:
        if plot_widget:
            self.plot_card.set_plot_widget(plot_widget)
