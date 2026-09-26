from PyQt6.QtWidgets import QFormLayout, QLabel, QWidget

from signal_processing_toolkit.dashboard.formatters import value
from signal_processing_toolkit.dashboard.state import SignalMetrics


class MeasurementPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._fields = {}
        layout = QFormLayout(self)
        for name, label in (
            ("rms", "RMS"),
            ("peak", "Peak"),
            ("peak_to_peak", "Peak-to-peak"),
            ("crest_factor", "Crest factor"),
            ("dominant_frequency", "Dominant frequency"),
            ("band_power", "Band power"),
            ("snr", "SNR"),
            ("thd", "THD"),
        ):
            field = QLabel("—")
            self._fields[name] = field
            layout.addRow(label, field)

    def update_metrics(self, metrics: SignalMetrics) -> None:
        for name, field in self._fields.items():
            field.setText(value(getattr(metrics, name), ""))
