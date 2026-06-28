from __future__ import annotations

from PyQt6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from src.models.enums import NoiseType
from src.models.signal import Signal
from src.plots.time_domain import TimeDomainPlot
from src.ui.viewmodels.noise_vm import NoiseViewModel


class NoiseView(QWidget):
    def __init__(self, viewmodel: NoiseViewModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("noiseView")
        self._vm = viewmodel
        self._setup_ui()
        self._bind()

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)

        gen_group = QGroupBox("Noise Generation")
        gen_layout = QFormLayout(gen_group)
        self.noise_combo = QComboBox()
        for nt in NoiseType:
            self.noise_combo.addItem(nt.value.capitalize(), nt)
        gen_layout.addRow("Type:", self.noise_combo)
        self.noise_amp_spin = QDoubleSpinBox()
        self.noise_amp_spin.setRange(0.01, 10.0)
        self.noise_amp_spin.setValue(0.1)
        self.noise_amp_spin.setSingleStep(0.05)
        gen_layout.addRow("Amplitude:", self.noise_amp_spin)
        self.gen_noise_btn = QPushButton("Generate Noise")
        gen_layout.addRow(self.gen_noise_btn)
        main_layout.addWidget(gen_group)

        add_group = QGroupBox("Add Noise to Signal")
        add_layout = QFormLayout(add_group)
        self.snr_spin = QDoubleSpinBox()
        self.snr_spin.setRange(-20.0, 100.0)
        self.snr_spin.setValue(20.0)
        self.snr_spin.setSuffix(" dB")
        add_layout.addRow("SNR:", self.snr_spin)
        self.add_noise_btn = QPushButton("Add Noise")
        self.add_noise_btn.setObjectName("primaryButton")
        add_layout.addRow(self.add_noise_btn)
        main_layout.addWidget(add_group)

        remove_group = QGroupBox("Noise Removal")
        remove_layout = QFormLayout(remove_group)
        self.method_combo = QComboBox()
        self.method_combo.addItems(["moving_average", "median", "wiener", "savgol", "adaptive_lms"])
        remove_layout.addRow("Method:", self.method_combo)

        self.param_stack = QStackedWidget()
        self.param_stack.addWidget(self._make_ma_widget())
        self.param_stack.addWidget(self._make_median_widget())
        self.param_stack.addWidget(self._make_wiener_widget())
        self.param_stack.addWidget(self._make_savgol_widget())
        self.param_stack.addWidget(self._make_lms_widget())
        remove_layout.addRow("Params:", self.param_stack)

        self.remove_noise_btn = QPushButton("Remove Noise")
        remove_layout.addRow(self.remove_noise_btn)
        main_layout.addWidget(remove_group)

        plot_group = QGroupBox("Signal Comparison")
        plot_layout = QVBoxLayout(plot_group)
        self.original_plot = TimeDomainPlot()
        self.original_plot.plot_widget.setTitle("Original / Noisy")
        self.denoised_plot = TimeDomainPlot()
        self.denoised_plot.plot_widget.setTitle("Denoised")
        plot_layout.addWidget(self.original_plot)
        plot_layout.addWidget(self.denoised_plot)
        main_layout.addWidget(plot_group, stretch=1)

        metrics_group = QGroupBox("Metrics")
        metrics_grid = QGridLayout(metrics_group)
        self.snr_before_label = QLabel("SNR Before: --")
        self.snr_after_label = QLabel("SNR After: --")
        self.noise_floor_label = QLabel("Noise Floor: --")
        self.improvement_label = QLabel("Improvement: --")
        metrics_grid.addWidget(self.snr_before_label, 0, 0)
        metrics_grid.addWidget(self.snr_after_label, 0, 1)
        metrics_grid.addWidget(self.noise_floor_label, 1, 0)
        metrics_grid.addWidget(self.improvement_label, 1, 1)
        main_layout.addWidget(metrics_group)

        self.status_label = QLabel("")
        main_layout.addWidget(self.status_label)

    def _make_ma_widget(self) -> QWidget:
        w = QWidget()
        layout = QHBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        self.ma_window_spin = QSpinBox()
        self.ma_window_spin.setRange(3, 101)
        self.ma_window_spin.setValue(5)
        self.ma_window_spin.setSingleStep(2)
        layout.addWidget(QLabel("Window:"))
        layout.addWidget(self.ma_window_spin)
        layout.addStretch()
        return w

    def _make_median_widget(self) -> QWidget:
        w = QWidget()
        layout = QHBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        self.med_kernel_spin = QSpinBox()
        self.med_kernel_spin.setRange(3, 51)
        self.med_kernel_spin.setValue(5)
        self.med_kernel_spin.setSingleStep(2)
        layout.addWidget(QLabel("Kernel:"))
        layout.addWidget(self.med_kernel_spin)
        layout.addStretch()
        return w

    def _make_wiener_widget(self) -> QWidget:
        w = QWidget()
        layout = QHBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        self.wn_window_spin = QSpinBox()
        self.wn_window_spin.setRange(3, 101)
        self.wn_window_spin.setValue(5)
        layout.addWidget(QLabel("Window:"))
        layout.addWidget(self.wn_window_spin)
        layout.addStretch()
        return w

    def _make_savgol_widget(self) -> QWidget:
        w = QWidget()
        layout = QHBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        self.sg_win_spin = QSpinBox()
        self.sg_win_spin.setRange(5, 101)
        self.sg_win_spin.setValue(11)
        self.sg_win_spin.setSingleStep(2)
        self.sg_order_spin = QSpinBox()
        self.sg_order_spin.setRange(1, 10)
        self.sg_order_spin.setValue(3)
        layout.addWidget(QLabel("Window:"))
        layout.addWidget(self.sg_win_spin)
        layout.addWidget(QLabel("Order:"))
        layout.addWidget(self.sg_order_spin)
        layout.addStretch()
        return w

    def _make_lms_widget(self) -> QWidget:
        w = QWidget()
        layout = QHBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        self.lms_mu_spin = QDoubleSpinBox()
        self.lms_mu_spin.setRange(0.0001, 1.0)
        self.lms_mu_spin.setValue(0.01)
        self.lms_mu_spin.setSingleStep(0.005)
        self.lms_len_spin = QSpinBox()
        self.lms_len_spin.setRange(4, 256)
        self.lms_len_spin.setValue(32)
        layout.addWidget(QLabel("μ:"))
        layout.addWidget(self.lms_mu_spin)
        layout.addWidget(QLabel("Taps:"))
        layout.addWidget(self.lms_len_spin)
        layout.addStretch()
        return w

    def _bind(self) -> None:
        self.gen_noise_btn.clicked.connect(self._on_gen_noise)
        self.add_noise_btn.clicked.connect(self._on_add_noise)
        self.remove_noise_btn.clicked.connect(self._on_remove_noise)
        self.method_combo.currentIndexChanged.connect(self.param_stack.setCurrentIndex)

    def set_input_signal(self, signal: Signal) -> None:
        self._vm.input_signal.value = signal

    def _on_gen_noise(self) -> None:
        self._vm.noise_type.value = self.noise_combo.currentData()
        self._vm.noise_amplitude.value = self.noise_amp_spin.value()
        noise = self._vm.generate_noise_only()
        if noise is not None:
            self.original_plot.clear()
            self.original_plot.plot(noise.time_vector[:1000], noise.time_data[:1000], name="Noise")
            self.original_plot.auto_range()

    def _on_add_noise(self) -> None:
        self._vm.noise_type.value = self.noise_combo.currentData()
        self._vm.snr_db.value = self.snr_spin.value()
        noisy = self._vm.add_noise_to_signal()
        clean = self._vm.input_signal.value
        if noisy is not None and clean is not None:
            self.original_plot.clear()
            self.original_plot.plot(clean.time_vector[:500], clean.time_data[:500], name="Clean")
            self.original_plot.plot(
                noisy.time_vector[:500], noisy.time_data[:500], name="Noisy", color="#f44747"
            )
            self.original_plot.auto_range()
            self._update_metrics()

    def _on_remove_noise(self) -> None:
        self._sync_remove_params()
        result = self._vm.remove_noise()
        if result is not None:
            self.denoised_plot.clear()
            self.denoised_plot.plot(
                result.time_vector[:500], result.time_data[:500], name="Denoised"
            )
            self.denoised_plot.auto_range()
            self._update_metrics()

    def _sync_remove_params(self) -> None:
        self._vm.removal_method.value = self.method_combo.currentText()
        self._vm.moving_avg_window.value = self.ma_window_spin.value()
        self._vm.median_kernel.value = self.med_kernel_spin.value()
        self._vm.wiener_window.value = self.wn_window_spin.value()
        self._vm.savgol_window.value = self.sg_win_spin.value()
        self._vm.savgol_order.value = self.sg_order_spin.value()
        self._vm.lms_mu.value = self.lms_mu_spin.value()
        self._vm.lms_length.value = self.lms_len_spin.value()

    def _update_metrics(self) -> None:
        before = self._vm.snr_before.value
        after = self._vm.snr_after.value
        floor_val = self._vm.noise_floor.value
        self.snr_before_label.setText(f"SNR Before: {before:.2f} dB")
        self.snr_after_label.setText(f"SNR After: {after:.2f} dB")
        self.noise_floor_label.setText(f"Noise Floor: {floor_val:.4f}")
        if after > 0:
            self.improvement_label.setText(f"Improvement: {after - before:.2f} dB")
