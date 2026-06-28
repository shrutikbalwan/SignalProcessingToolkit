from __future__ import annotations

import numpy as np
from PyQt6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.models.enums import DesignMethod, FilterType, ResponseType
from src.models.signal import Signal
from src.plots.base import BasePlotWidget
from src.ui.viewmodels.filters_vm import FilterViewModel


class FilterView(QWidget):
    def __init__(self, viewmodel: FilterViewModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("filtersView")
        self._vm = viewmodel
        self._setup_ui()
        self._bind()

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)

        designer_group = QGroupBox("Filter Designer")
        designer_layout = QFormLayout(designer_group)

        self.ftype_combo = QComboBox()
        for ft in FilterType:
            self.ftype_combo.addItem(ft.value.capitalize(), ft)
        designer_layout.addRow("Filter Type:", self.ftype_combo)

        self.rtype_combo = QComboBox()
        for rt in ResponseType:
            self.rtype_combo.addItem(rt.value.upper(), rt)
        designer_layout.addRow("Response:", self.rtype_combo)

        self.dmethod_combo = QComboBox()
        for dm in DesignMethod:
            self.dmethod_combo.addItem(dm.value.capitalize(), dm)
        designer_layout.addRow("Method:", self.dmethod_combo)

        self.order_spin = QSpinBox()
        self.order_spin.setRange(1, 50)
        self.order_spin.setValue(4)
        designer_layout.addRow("Order:", self.order_spin)

        self.cutoff_spin = QDoubleSpinBox()
        self.cutoff_spin.setRange(0.1, 100000.0)
        self.cutoff_spin.setValue(1000.0)
        self.cutoff_spin.setSuffix(" Hz")
        designer_layout.addRow("Cutoff f1:", self.cutoff_spin)

        self.cutoff2_spin = QDoubleSpinBox()
        self.cutoff2_spin.setRange(0.1, 100000.0)
        self.cutoff2_spin.setValue(2000.0)
        self.cutoff2_spin.setSuffix(" Hz")
        designer_layout.addRow("Cutoff f2:", self.cutoff2_spin)

        self.sr_spin = QDoubleSpinBox()
        self.sr_spin.setRange(100.0, 1000000.0)
        self.sr_spin.setValue(44100.0)
        self.sr_spin.setSuffix(" Hz")
        designer_layout.addRow("Sampling Rate:", self.sr_spin)

        self.ripple_spin = QDoubleSpinBox()
        self.ripple_spin.setRange(0.01, 10.0)
        self.ripple_spin.setValue(1.0)
        self.ripple_spin.setSuffix(" dB")
        designer_layout.addRow("Passband Ripple:", self.ripple_spin)

        self.atten_spin = QDoubleSpinBox()
        self.atten_spin.setRange(1.0, 100.0)
        self.atten_spin.setValue(40.0)
        self.atten_spin.setSuffix(" dB")
        designer_layout.addRow("Stopband Atten:", self.atten_spin)

        button_layout = QHBoxLayout()
        self.design_btn = QPushButton("Design Filter")
        self.design_btn.setObjectName("primaryButton")
        self.apply_btn = QPushButton("Apply to Signal")
        button_layout.addWidget(self.design_btn)
        button_layout.addWidget(self.apply_btn)
        button_layout.addStretch()
        designer_layout.addRow("Actions:", button_layout)

        main_layout.addWidget(designer_group)

        tabs = QTabWidget()
        mag_tab = QWidget()
        mag_layout = QVBoxLayout(mag_tab)
        self.mag_plot = BasePlotWidget(title="Magnitude Response")
        self.mag_plot.set_labels(x_label="Frequency (Hz)", y_label="Magnitude (dB)")
        mag_layout.addWidget(self.mag_plot)
        tabs.addTab(mag_tab, "Magnitude")

        phase_tab = QWidget()
        phase_layout = QVBoxLayout(phase_tab)
        self.phase_plot = BasePlotWidget(title="Phase Response")
        self.phase_plot.set_labels(x_label="Frequency (Hz)", y_label="Phase (rad)")
        phase_layout.addWidget(self.phase_plot)
        tabs.addTab(phase_tab, "Phase")

        imp_tab = QWidget()
        imp_layout = QVBoxLayout(imp_tab)
        self.imp_plot = BasePlotWidget(title="Impulse Response")
        self.imp_plot.set_labels(x_label="Sample", y_label="Amplitude")
        imp_layout.addWidget(self.imp_plot)
        tabs.addTab(imp_tab, "Impulse")

        pz_tab = QWidget()
        pz_layout = QVBoxLayout(pz_tab)
        self.pz_plot = BasePlotWidget(title="Pole-Zero Map")
        self.pz_plot.set_labels(x_label="Real", y_label="Imaginary")
        pz_layout.addWidget(self.pz_plot)
        tabs.addTab(pz_tab, "Pole-Zero")

        out_tab = QWidget()
        out_layout = QVBoxLayout(out_tab)
        self.out_plot = BasePlotWidget(title="Filtered vs Original")
        self.out_plot.set_labels(x_label="Time (s)", y_label="Amplitude")
        out_layout.addWidget(self.out_plot)
        tabs.addTab(out_tab, "Output")

        main_layout.addWidget(tabs, stretch=1)

        self.status_label = QLabel("")
        main_layout.addWidget(self.status_label)

    def _bind(self) -> None:
        self.design_btn.clicked.connect(self._on_design)
        self.apply_btn.clicked.connect(self._on_apply)

    def set_input_signal(self, signal: Signal) -> None:
        self._vm.input_signal.value = signal

    def _on_design(self) -> None:
        self._sync_params()
        coeffs = self._vm.design()
        if coeffs is None:
            return

        fr = self._vm.freq_response.value
        if fr is not None:
            self.mag_plot.clear()
            self.mag_plot.plot(fr.frequencies, fr.magnitude_db, name="Magnitude (dB)")
            self.mag_plot.auto_range()

            self.phase_plot.clear()
            self.phase_plot.plot(fr.frequencies, fr.phase, name="Phase")
            self.phase_plot.auto_range()

        ir = self._vm.impulse_response.value
        if ir is not None:
            self.imp_plot.clear()
            self.imp_plot.plot(np.arange(len(ir.time_data)), ir.time_data, name="Impulse")
            self.imp_plot.auto_range()

        pz = self._vm.pole_zero.value
        if pz is not None:
            self.pz_plot.clear()
            self.pz_plot.plot(np.real(pz.zeros), np.imag(pz.zeros), name="Zeros", color="#4ec9b0")
            self.pz_plot.plot(np.real(pz.poles), np.imag(pz.poles), name="Poles", color="#f44747")
            self.pz_plot.auto_range()

    def _on_apply(self) -> None:
        result = self._vm.apply()
        signal = self._vm.input_signal.value
        if result is not None and signal is not None:
            self.out_plot.clear()
            self.out_plot.plot(signal.time_vector[:500], signal.time_data[:500], name="Original")
            self.out_plot.plot(
                signal.time_vector[:500], result.time_data[:500], name="Filtered", color="#4ec9b0"
            )
            self.out_plot.auto_range()

    def _sync_params(self) -> None:
        self._vm.filter_type.value = self.ftype_combo.currentData()
        self._vm.response_type.value = self.rtype_combo.currentData()
        self._vm.design_method.value = self.dmethod_combo.currentData()
        self._vm.order.value = self.order_spin.value()
        self._vm.cutoff_freq.value = self.cutoff_spin.value()
        self._vm.cutoff_freq2.value = self.cutoff2_spin.value()
        self._vm.sampling_rate.value = self.sr_spin.value()
        self._vm.passband_ripple.value = self.ripple_spin.value()
        self._vm.stopband_atten.value = self.atten_spin.value()
