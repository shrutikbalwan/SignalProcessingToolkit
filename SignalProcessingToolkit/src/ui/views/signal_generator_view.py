from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from src.models.enums import WaveformType
from src.plots.time_domain import TimeDomainPlot
from src.ui.viewmodels.signal_generator_vm import SignalGeneratorViewModel

PARAM_LABELS: dict[str, str] = {
    "sine": "No extra parameters",
    "cosine": "No extra parameters",
    "square": "Duty Cycle",
    "triangle": "No extra parameters",
    "sawtooth": "No extra parameters",
    "pulse": "Pulse Width",
    "chirp": "Chirp End Freq / Method",
    "gaussian": "Mean (µ) / Std Dev (σ)",
    "noise": "Noise Type",
    "dc": "No extra parameters",
}


class SignalGeneratorView(QWidget):
    def __init__(self, viewmodel: SignalGeneratorViewModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("signalGeneratorView")
        self._vm = viewmodel
        self._setup_ui()
        self._bind()

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(12)

        controls_group = QGroupBox("Signal Parameters")
        controls_layout = QGridLayout(controls_group)

        self.waveform_combo = QComboBox()
        for wt in WaveformType:
            self.waveform_combo.addItem(wt.value.capitalize(), wt)
        controls_layout.addWidget(QLabel("Waveform:"), 0, 0)
        controls_layout.addWidget(self.waveform_combo, 0, 1)

        self.freq_spin = QDoubleSpinBox()
        self.freq_spin.setRange(0.1, 100000.0)
        self.freq_spin.setValue(440.0)
        self.freq_spin.setSuffix(" Hz")
        controls_layout.addWidget(QLabel("Frequency:"), 0, 2)
        controls_layout.addWidget(self.freq_spin, 0, 3)

        self.amp_spin = QDoubleSpinBox()
        self.amp_spin.setRange(0.0, 100.0)
        self.amp_spin.setValue(1.0)
        self.amp_spin.setSingleStep(0.1)
        controls_layout.addWidget(QLabel("Amplitude:"), 1, 0)
        controls_layout.addWidget(self.amp_spin, 1, 1)

        self.phase_spin = QDoubleSpinBox()
        self.phase_spin.setRange(-360.0, 360.0)
        self.phase_spin.setValue(0.0)
        self.phase_spin.setSuffix(" °")
        controls_layout.addWidget(QLabel("Phase:"), 1, 2)
        controls_layout.addWidget(self.phase_spin, 1, 3)

        self.sr_spin = QDoubleSpinBox()
        self.sr_spin.setRange(100.0, 1000000.0)
        self.sr_spin.setValue(44100.0)
        self.sr_spin.setSuffix(" Hz")
        controls_layout.addWidget(QLabel("Sampling Rate:"), 2, 0)
        controls_layout.addWidget(self.sr_spin, 2, 1)

        self.dur_spin = QDoubleSpinBox()
        self.dur_spin.setRange(0.001, 60.0)
        self.dur_spin.setValue(1.0)
        self.dur_spin.setSuffix(" s")
        controls_layout.addWidget(QLabel("Duration:"), 2, 2)
        controls_layout.addWidget(self.dur_spin, 2, 3)

        self.extra_stack = QStackedWidget()
        self.extra_stack.addWidget(self._make_extra_none())
        self.extra_stack.addWidget(self._make_extra_none())
        self.extra_stack.addWidget(self._make_extra_duty())
        self.extra_stack.addWidget(self._make_extra_none())
        self.extra_stack.addWidget(self._make_extra_none())
        self.extra_stack.addWidget(self._make_extra_pulse())
        self.extra_stack.addWidget(self._make_extra_chirp())
        self.extra_stack.addWidget(self._make_extra_gaussian())
        self.extra_stack.addWidget(self._make_extra_noise())
        self.extra_stack.addWidget(self._make_extra_none())
        controls_layout.addWidget(QLabel("Extra:"), 3, 0)
        controls_layout.addWidget(self.extra_stack, 3, 1, 1, 3)

        main_layout.addWidget(controls_group)

        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout(preview_group)
        self.plot = TimeDomainPlot()
        preview_layout.addWidget(self.plot)
        main_layout.addWidget(preview_group, stretch=1)

        button_layout = QHBoxLayout()
        self.generate_btn = QPushButton("Generate")
        self.generate_btn.setObjectName("primaryButton")
        self.export_btn = QPushButton("Export...")
        button_layout.addStretch()
        button_layout.addWidget(self.generate_btn)
        button_layout.addWidget(self.export_btn)
        main_layout.addLayout(button_layout)

    def _make_extra_none(self) -> QLabel:
        return QLabel("No extra parameters")

    def _make_extra_duty(self) -> QWidget:
        w = QWidget()
        layout = QHBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        self.duty_spin = QDoubleSpinBox()
        self.duty_spin.setRange(0.01, 0.99)
        self.duty_spin.setValue(0.5)
        self.duty_spin.setSingleStep(0.05)
        layout.addWidget(QLabel("Duty:"))
        layout.addWidget(self.duty_spin)
        layout.addStretch()
        return w

    def _make_extra_pulse(self) -> QWidget:
        w = QWidget()
        layout = QHBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        self.pw_spin = QDoubleSpinBox()
        self.pw_spin.setRange(0.0001, 1.0)
        self.pw_spin.setValue(0.01)
        self.pw_spin.setSuffix(" s")
        layout.addWidget(QLabel("Pulse Width:"))
        layout.addWidget(self.pw_spin)
        layout.addStretch()
        return w

    def _make_extra_chirp(self) -> QWidget:
        w = QWidget()
        layout = QHBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        self.chirp_f1_spin = QDoubleSpinBox()
        self.chirp_f1_spin.setRange(1.0, 100000.0)
        self.chirp_f1_spin.setValue(1000.0)
        self.chirp_f1_spin.setSuffix(" Hz")
        self.chirp_method_combo = QComboBox()
        self.chirp_method_combo.addItems(["linear", "quadratic", "logarithmic", "hyperbolic"])
        layout.addWidget(QLabel("f1:"))
        layout.addWidget(self.chirp_f1_spin)
        layout.addWidget(QLabel("Method:"))
        layout.addWidget(self.chirp_method_combo)
        layout.addStretch()
        return w

    def _make_extra_gaussian(self) -> QWidget:
        w = QWidget()
        layout = QHBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        self.gauss_mu_spin = QDoubleSpinBox()
        self.gauss_mu_spin.setRange(0.0, 10.0)
        self.gauss_mu_spin.setValue(0.5)
        self.gauss_sigma_spin = QDoubleSpinBox()
        self.gauss_sigma_spin.setRange(0.001, 10.0)
        self.gauss_sigma_spin.setValue(0.1)
        layout.addWidget(QLabel("µ:"))
        layout.addWidget(self.gauss_mu_spin)
        layout.addWidget(QLabel("σ:"))
        layout.addWidget(self.gauss_sigma_spin)
        layout.addStretch()
        return w

    def _make_extra_noise(self) -> QWidget:
        w = QWidget()
        layout = QHBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        self.noise_type_combo = QComboBox()
        self.noise_type_combo.addItems(["white", "pink", "brownian"])
        layout.addWidget(QLabel("Type:"))
        layout.addWidget(self.noise_type_combo)
        layout.addStretch()
        return w

    def _bind(self) -> None:
        self.waveform_combo.currentIndexChanged.connect(self._on_waveform_changed)
        self.freq_spin.valueChanged.connect(lambda v: setattr(self._vm.frequency, "value", v))
        self.amp_spin.valueChanged.connect(lambda v: setattr(self._vm.amplitude, "value", v))
        self.phase_spin.valueChanged.connect(lambda v: setattr(self._vm.phase, "value", v))
        self.sr_spin.valueChanged.connect(lambda v: setattr(self._vm.sampling_rate, "value", v))
        self.dur_spin.valueChanged.connect(lambda v: setattr(self._vm.duration, "value", v))

        self.generate_btn.clicked.connect(self._on_generate)
        self.export_btn.clicked.connect(self._on_export)

    def _on_waveform_changed(self, index: int) -> None:
        wt = self.waveform_combo.currentData()
        self._vm.waveform_type.value = wt
        self.extra_stack.setCurrentIndex(index)

    def _on_generate(self) -> None:
        self._sync_extra_params()
        signal = self._vm.generate()
        if signal is not None:
            self.plot.plot_signal(signal, name=self._vm.waveform_type.value.value.capitalize())

    def _sync_extra_params(self) -> None:
        wt = self._vm.waveform_type.value
        if wt == WaveformType.SQUARE:
            self._vm.duty_cycle.value = self.duty_spin.value()
        elif wt == WaveformType.PULSE:
            self._vm.pulse_width.value = self.pw_spin.value()
        elif wt == WaveformType.CHIRP:
            self._vm.chirp_f1.value = self.chirp_f1_spin.value()
            self._vm.chirp_method.value = self.chirp_method_combo.currentText()
        elif wt == WaveformType.GAUSSIAN:
            self._vm.gaussian_mu.value = self.gauss_mu_spin.value()
            self._vm.gaussian_sigma.value = self.gauss_sigma_spin.value()
        elif wt == WaveformType.NOISE:
            self._vm.noise_type.value = self.noise_type_combo.currentText()

    def _on_export(self) -> None:
        signal = self._vm.generated_signal.value
        if signal is None:
            QMessageBox.warning(self, "No Signal", "Generate a signal first.")
            return
        path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Export Signal",
            "",
            "CSV (*.csv);; NumPy (*.npz);; WAV (*.wav);; Text (*.txt)",
        )
        if not path:
            return
        p = Path(path)
        from src.repositories.implementations.file_signal_repository import FileSignalRepository

        repo = FileSignalRepository()
        if p.suffix == ".csv":
            repo.export_csv(signal, p)
        elif p.suffix == ".npz":
            repo.save(signal, p)
        elif p.suffix == ".wav":
            repo.export_wav(signal, p)
        elif p.suffix == ".txt":
            repo.export_txt(signal, p)
        QMessageBox.information(self, "Exported", f"Signal exported to {p.name}")
