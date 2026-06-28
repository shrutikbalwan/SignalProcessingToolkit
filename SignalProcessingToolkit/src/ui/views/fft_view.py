from __future__ import annotations

from typing import Any

from PyQt6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.models.signal import Signal
from src.plots.cursors import CrosshairCursor
from src.plots.frequency_domain import FrequencyDomainPlot
from src.plots.spectrogram import SpectrogramPlot
from src.ui.viewmodels.fft_vm import FFTViewModel


class FFTView(QWidget):
    def __init__(self, viewmodel: FFTViewModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("fftView")
        self._vm = viewmodel
        self._setup_ui()
        self._bind()

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)

        controls_group = QGroupBox("FFT Controls")
        controls_layout = QFormLayout(controls_group)

        self.spectrum_combo = QComboBox()
        self.spectrum_combo.addItems(["magnitude", "power", "phase"])
        controls_layout.addRow("Spectrum Type:", self.spectrum_combo)

        self.fft_size_spin = QSpinBox()
        self.fft_size_spin.setRange(64, 65536)
        self.fft_size_spin.setValue(4096)
        self.fft_size_spin.setSingleStep(512)
        controls_layout.addRow("FFT Size:", self.fft_size_spin)

        peak_layout = QHBoxLayout()
        self.peak_height_spin = QDoubleSpinBox()
        self.peak_height_spin.setRange(0.0, 100.0)
        self.peak_height_spin.setValue(0.1)
        self.peak_height_spin.setSingleStep(0.05)
        self.peak_dist_spin = QSpinBox()
        self.peak_dist_spin.setRange(1, 1000)
        self.peak_dist_spin.setValue(5)
        self.update_peaks_btn = QPushButton("Update Peaks")
        peak_layout.addWidget(QLabel("Min Height:"))
        peak_layout.addWidget(self.peak_height_spin)
        peak_layout.addWidget(QLabel("Min Distance:"))
        peak_layout.addWidget(self.peak_dist_spin)
        peak_layout.addWidget(self.update_peaks_btn)
        controls_layout.addRow("Peak Detection:", peak_layout)

        button_layout = QHBoxLayout()
        self.compute_btn = QPushButton("Compute FFT")
        self.compute_btn.setObjectName("primaryButton")
        self.inverse_btn = QPushButton("IFFT")
        button_layout.addWidget(self.compute_btn)
        button_layout.addWidget(self.inverse_btn)
        button_layout.addStretch()
        controls_layout.addRow("Actions:", button_layout)

        main_layout.addWidget(controls_group)

        tabs = QTabWidget()
        spectrum_tab = QWidget()
        spectrum_layout = QVBoxLayout(spectrum_tab)
        self.freq_plot = FrequencyDomainPlot()
        spectrum_layout.addWidget(self.freq_plot)
        tabs.addTab(spectrum_tab, "Spectrum")

        self.crosshair = CrosshairCursor(self.freq_plot.plot_widget)

        spectrogram_tab = QWidget()
        spectrogram_layout = QVBoxLayout(spectrogram_tab)
        self.spectrogram_plot = SpectrogramPlot()
        spectrogram_layout.addWidget(self.spectrogram_plot)
        tabs.addTab(spectrogram_tab, "Spectrogram")
        main_layout.addWidget(tabs, stretch=1)

        peaks_group = QGroupBox("Detected Peaks")
        peaks_layout = QVBoxLayout(peaks_group)
        self.peaks_table = QTableWidget()
        self.peaks_table.setColumnCount(4)
        self.peaks_table.setHorizontalHeaderLabels(["Freq (Hz)", "Magnitude", "Mag (dB)", "Phase"])
        header = self.peaks_table.horizontalHeader()
        if header is not None:
            header.setStretchLastSection(True)
        self.peaks_table.setMaximumHeight(150)
        peaks_layout.addWidget(self.peaks_table)
        main_layout.addWidget(peaks_group)

        self.status_label = QLabel("")
        main_layout.addWidget(self.status_label)

    def _bind(self) -> None:
        self.compute_btn.clicked.connect(self._on_compute)
        self.inverse_btn.clicked.connect(self._on_inverse)
        self.update_peaks_btn.clicked.connect(self._on_update_peaks)
        self.spectrum_combo.currentTextChanged.connect(self._vm.spectrum_type.__setattr__)

    def set_input_signal(self, signal: Signal) -> None:
        self._vm.input_signal.value = signal
        self.spectrogram_plot.plot(signal)

    def _on_compute(self) -> None:
        self._sync_params()
        result = self._vm.compute()
        if result is not None:
            self._display_result(result)

    def _on_inverse(self) -> None:
        inverse = self._vm.compute_inverse()
        if inverse is not None:
            self.freq_plot.clear()
            self.freq_plot.plot(inverse.time_vector, inverse.time_data, name="IFFT Result")
            self.freq_plot.auto_range()

    def _on_update_peaks(self) -> None:
        self._sync_peak_params()
        self._vm.update_peaks()
        self._populate_peaks_table()

    def _sync_params(self) -> None:
        self._vm.fft_size.value = self.fft_size_spin.value()
        self._sync_peak_params()

    def _sync_peak_params(self) -> None:
        self._vm.min_peak_height.value = self.peak_height_spin.value()
        self._vm.min_peak_distance.value = self.peak_dist_spin.value()

    def _display_result(self, result: Any) -> None:
        st = self._vm.spectrum_type.value
        if st == "magnitude":
            self.freq_plot.plot_spectrum(result, name="Magnitude Spectrum")
        elif st == "power":
            self.freq_plot.plot_magnitude(result)
            self.freq_plot.plot_widget.setTitle("Power Spectrum")
        elif st == "phase":
            self.freq_plot.clear()
            self.freq_plot.plot(result.frequencies, result.phase, name="Phase Spectrum")
            self.freq_plot.plot_widget.setTitle("Phase Spectrum")
            self.freq_plot.set_labels(y_label="Phase (rad)")
        self.freq_plot.auto_range()
        self._populate_peaks_table()

    def _populate_peaks_table(self) -> None:
        peaks = self._vm.peaks.value
        self.peaks_table.setRowCount(len(peaks))
        for i, p in enumerate(peaks):
            self.peaks_table.setItem(i, 0, QTableWidgetItem(f"{p.frequency:.2f}"))
            self.peaks_table.setItem(i, 1, QTableWidgetItem(f"{p.magnitude:.4f}"))
            self.peaks_table.setItem(i, 2, QTableWidgetItem(f"{p.magnitude_db:.2f}"))
            self.peaks_table.setItem(i, 3, QTableWidgetItem(f"{p.phase:.4f}"))
