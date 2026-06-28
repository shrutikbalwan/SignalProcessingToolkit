from __future__ import annotations

import numpy as np
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
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.models.enums import WindowType
from src.models.signal import Signal
from src.plots.base import BasePlotWidget
from src.ui.viewmodels.windows_vm import WindowViewModel


class WindowView(QWidget):
    def __init__(self, viewmodel: WindowViewModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("windowsView")
        self._vm = viewmodel
        self._setup_ui()
        self._bind()

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)

        controls_group = QGroupBox("Window Controls")
        controls_layout = QFormLayout(controls_group)

        self.window_combo = QComboBox()
        for wt in WindowType:
            self.window_combo.addItem(wt.value.capitalize(), wt)
        controls_layout.addRow("Type:", self.window_combo)

        self.length_spin = QSpinBox()
        self.length_spin.setRange(8, 65536)
        self.length_spin.setValue(256)
        self.length_spin.setSingleStep(16)
        controls_layout.addRow("Length:", self.length_spin)

        self.beta_spin = QDoubleSpinBox()
        self.beta_spin.setRange(0.0, 100.0)
        self.beta_spin.setValue(14.0)
        self.beta_spin.setSingleStep(0.5)
        controls_layout.addRow("Kaiser β:", self.beta_spin)

        button_layout = QHBoxLayout()
        self.compute_btn = QPushButton("Compute Window")
        self.compute_btn.setObjectName("primaryButton")
        self.apply_btn = QPushButton("Apply to Signal")
        self.compare_btn = QPushButton("Compare")
        button_layout.addWidget(self.compute_btn)
        button_layout.addWidget(self.apply_btn)
        button_layout.addWidget(self.compare_btn)
        controls_layout.addRow("Actions:", button_layout)

        main_layout.addWidget(controls_group)

        tabs = QTabWidget()
        time_tab = QWidget()
        time_layout = QVBoxLayout(time_tab)
        self.time_plot = BasePlotWidget(title="Window (Time Domain)")
        self.time_plot.set_labels(x_label="Sample", y_label="Amplitude")
        time_layout.addWidget(self.time_plot)
        tabs.addTab(time_tab, "Time Domain")

        freq_tab = QWidget()
        freq_layout = QVBoxLayout(freq_tab)
        self.freq_plot = BasePlotWidget(title="Frequency Response")
        self.freq_plot.set_labels(x_label="Normalized Frequency", y_label="Magnitude (dB)")
        freq_layout.addWidget(self.freq_plot)
        tabs.addTab(freq_tab, "Frequency Response")

        compare_tab = QWidget()
        compare_layout = QVBoxLayout(compare_tab)
        self.compare_plot = BasePlotWidget(title="Window Comparison")
        self.compare_plot.set_labels(x_label="Sample", y_label="Amplitude")
        compare_layout.addWidget(self.compare_plot)
        tabs.addTab(compare_tab, "Comparison")

        main_layout.addWidget(tabs, stretch=1)

        metrics_group = QGroupBox("Window Metrics")
        metrics_grid = QGridLayout(metrics_group)
        self.energy_label = QLabel("Energy: --")
        self.coherent_gain_label = QLabel("Coherent Gain: --")
        self.enbw_label = QLabel("ENBW: --")
        self.scallop_label = QLabel("Scalloping Loss: --")
        self.sidelobe_label = QLabel("Max Sidelobe: --")
        self.mainlobe_label = QLabel("Mainlobe Width: --")
        metrics_grid.addWidget(self.energy_label, 0, 0)
        metrics_grid.addWidget(self.coherent_gain_label, 0, 1)
        metrics_grid.addWidget(self.enbw_label, 1, 0)
        metrics_grid.addWidget(self.scallop_label, 1, 1)
        metrics_grid.addWidget(self.sidelobe_label, 2, 0)
        metrics_grid.addWidget(self.mainlobe_label, 2, 1)
        main_layout.addWidget(metrics_group)

        self.status_label = QLabel("")
        main_layout.addWidget(self.status_label)

    def _bind(self) -> None:
        self.compute_btn.clicked.connect(self._on_compute)
        self.apply_btn.clicked.connect(self._on_apply)
        self.compare_btn.clicked.connect(self._on_compare)

    def set_input_signal(self, signal: Signal) -> None:
        self._vm.input_signal.value = signal

    def _on_compute(self) -> None:
        self._sync_params()
        data = self._vm.compute()
        if data is not None:
            self.time_plot.clear()
            self.time_plot.plot(np.arange(len(data)), data, name=self._vm.window_type.value.value)
            self.time_plot.auto_range()

            fr = self._vm.freq_response.value
            if fr is not None:
                self.freq_plot.clear()
                self.freq_plot.plot(fr[0], fr[1], name=self._vm.window_type.value.value)
                self.freq_plot.auto_range()

            self._update_metrics()

    def _on_apply(self) -> None:
        result = self._vm.apply_to_signal()
        if result is not None:
            self.time_plot.clear()
            self.time_plot.plot(result.time_vector, result.time_data, name="Windowed Signal")
            self.time_plot.auto_range()

    def _on_compare(self) -> None:
        self._sync_params()
        comparison = self._vm.run_comparison()
        self.compare_plot.clear()
        colors = self.compare_plot._theme.line_colors
        for i, (wt, data) in enumerate(comparison.items()):
            color = colors[i % len(colors)]
            self.compare_plot.plot(np.arange(len(data)), data, name=wt.value, color=color)
        self.compare_plot.auto_range()

    def _sync_params(self) -> None:
        self._vm.window_type.value = self.window_combo.currentData()
        self._vm.window_length.value = self.length_spin.value()
        self._vm.kaiser_beta.value = self.beta_spin.value()

    def _update_metrics(self) -> None:
        m = self._vm.metrics.value
        if m is None:
            return
        self.energy_label.setText(f"Energy: {m.energy:.4f}")
        self.coherent_gain_label.setText(f"Coherent Gain: {m.coherent_gain:.4f}")
        self.enbw_label.setText(f"ENBW: {m.enbw:.4f}")
        self.scallop_label.setText(f"Scalloping Loss: {m.scalloping_loss:.4f}")
        self.sidelobe_label.setText(f"Max Sidelobe: {m.max_sidelobe_db:.2f} dB")
        self.mainlobe_label.setText(f"Mainlobe Width: {m.mainlobe_width:.4f}")
