from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import numpy as np
import pyqtgraph as pg
from PyQt6.QtCore import QRectF
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
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

from signal_processing_toolkit.dsp.analysis import EventDetectionConfig, STFTConfig
from signal_processing_toolkit.models.signal import Signal
from signal_processing_toolkit.services.analysis_service import (
    AdvancedAnalysisResult,
    AnalysisService,
)
from signal_processing_toolkit.ui.workers import TaskRunner


class LinkedAnalysisCursors:
    """Keep time cursors synchronized between waveform and time-frequency plots."""

    def __init__(
        self,
        time_plot: pg.PlotWidget,
        time_frequency_plot: pg.PlotWidget,
        frequency_plot: pg.PlotWidget,
    ) -> None:
        self.time_line = pg.InfiniteLine(angle=90, movable=True, label="t={value:.4f}s")
        self.tf_time_line = pg.InfiniteLine(angle=90, movable=True)
        self.frequency_line = pg.InfiniteLine(angle=0, movable=True, label="f={value:.2f}Hz")
        self.spectrum_frequency_line = pg.InfiniteLine(angle=90, movable=True)
        time_plot.addItem(self.time_line)
        time_frequency_plot.addItem(self.tf_time_line)
        time_frequency_plot.addItem(self.frequency_line)
        frequency_plot.addItem(self.spectrum_frequency_line)
        self.time_line.sigPositionChanged.connect(
            lambda line: self.tf_time_line.setValue(line.value())
        )
        self.tf_time_line.sigPositionChanged.connect(
            lambda line: self.time_line.setValue(line.value())
        )
        self.frequency_line.sigPositionChanged.connect(
            lambda line: self.spectrum_frequency_line.setValue(line.value())
        )
        self.spectrum_frequency_line.sigPositionChanged.connect(
            lambda line: self.frequency_line.setValue(line.value())
        )


class AnalysisView(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("advancedAnalysisView")
        self._service = AnalysisService()
        self._tasks = TaskRunner(self)
        self._signal: Signal | None = None
        self._result: AdvancedAnalysisResult | None = None
        self._setup_ui()
        self._tasks.busy_changed.connect(self._set_busy)
        self._tasks.error.connect(self._show_error)

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        controls = QGroupBox("Advanced analysis parameters")
        form = QFormLayout(controls)
        self.window_combo = QComboBox()
        self.window_combo.addItems(["hann", "hamming", "blackman", "boxcar"])
        self.window_combo.setAccessibleName("STFT window")
        self.window_length = QSpinBox()
        self.window_length.setRange(16, 65536)
        self.window_length.setValue(256)
        self.window_length.setAccessibleName("STFT window length")
        self.overlap = QSpinBox()
        self.overlap.setRange(0, 65535)
        self.overlap.setValue(128)
        self.overlap.setAccessibleName("STFT overlap samples")
        self.fft_length = QSpinBox()
        self.fft_length.setRange(16, 131072)
        self.fft_length.setValue(512)
        self.fft_length.setAccessibleName("STFT FFT length")
        self.scaling_combo = QComboBox()
        self.scaling_combo.addItems(["spectrum", "psd"])
        self.scaling_combo.setAccessibleName("STFT scaling")
        self.boundary_combo = QComboBox()
        self.boundary_combo.addItems(["zeros", "even", "odd", "constant", "none"])
        self.boundary_combo.setAccessibleName("STFT boundary behavior")
        self.comparison_combo = QComboBox()
        self.comparison_combo.setAccessibleName("Comparison signal for cross spectral analysis")
        self.comparison_combo.addItem("None", None)
        self.auto_threshold = QCheckBox("Automatic")
        self.auto_threshold.setChecked(True)
        self.auto_threshold.setAccessibleName("Automatically calculate event threshold")
        self.event_threshold = QDoubleSpinBox()
        self.event_threshold.setRange(-1e12, 1e12)
        self.event_threshold.setDecimals(6)
        self.event_threshold.setEnabled(False)
        self.event_threshold.setAccessibleName("Event threshold")
        threshold_controls = QHBoxLayout()
        threshold_controls.addWidget(self.auto_threshold)
        threshold_controls.addWidget(self.event_threshold)
        self.event_direction = QComboBox()
        self.event_direction.addItems(["above", "below", "absolute"])
        self.event_direction.setAccessibleName("Event direction")
        self.event_hysteresis = QDoubleSpinBox()
        self.event_hysteresis.setRange(0, 1e12)
        self.event_hysteresis.setDecimals(6)
        self.event_hysteresis.setAccessibleName("Event hysteresis")
        self.event_minimum_duration = QDoubleSpinBox()
        self.event_minimum_duration.setRange(0, 3600)
        self.event_minimum_duration.setDecimals(6)
        self.event_minimum_duration.setAccessibleName("Minimum event duration in seconds")
        self.event_minimum_distance = QDoubleSpinBox()
        self.event_minimum_distance.setRange(0, 3600)
        self.event_minimum_distance.setDecimals(6)
        self.event_minimum_distance.setAccessibleName("Minimum event distance in seconds")
        self.transient_prominence = QDoubleSpinBox()
        self.transient_prominence.setRange(0, 1e12)
        self.transient_prominence.setDecimals(6)
        self.transient_prominence.setSpecialValueText("Automatic")
        self.transient_prominence.setAccessibleName("Transient prominence or automatic")
        self.transient_smoothing = QDoubleSpinBox()
        self.transient_smoothing.setRange(0, 60)
        self.transient_smoothing.setDecimals(6)
        self.transient_smoothing.setValue(0.001)
        self.transient_smoothing.setAccessibleName("Transient smoothing in seconds")
        self.transient_minimum_distance = QDoubleSpinBox()
        self.transient_minimum_distance.setRange(0, 3600)
        self.transient_minimum_distance.setDecimals(6)
        self.transient_minimum_distance.setAccessibleName("Minimum transient distance in seconds")
        form.addRow("Window", self.window_combo)
        form.addRow("Window length", self.window_length)
        form.addRow("Overlap", self.overlap)
        form.addRow("FFT length", self.fft_length)
        form.addRow("Scaling", self.scaling_combo)
        form.addRow("Boundary", self.boundary_combo)
        form.addRow("Comparison signal", self.comparison_combo)
        form.addRow("Event threshold", threshold_controls)
        form.addRow("Event direction", self.event_direction)
        form.addRow("Event hysteresis", self.event_hysteresis)
        form.addRow("Minimum event duration (s)", self.event_minimum_duration)
        form.addRow("Minimum event distance (s)", self.event_minimum_distance)
        form.addRow("Transient prominence", self.transient_prominence)
        form.addRow("Transient smoothing (s)", self.transient_smoothing)
        form.addRow("Minimum transient distance (s)", self.transient_minimum_distance)
        actions = QHBoxLayout()
        self.analyze_button = QPushButton("Analyze selected region")
        self.analyze_button.setAccessibleName("Run advanced analysis")
        self.reset_region_button = QPushButton("Select full signal")
        self.export_button = QPushButton("Export measurements")
        self.export_button.setAccessibleName("Export measurement table")
        actions.addWidget(self.analyze_button)
        actions.addWidget(self.reset_region_button)
        actions.addWidget(self.export_button)
        form.addRow("Actions", actions)
        layout.addWidget(controls)

        tabs = QTabWidget()
        tabs.setAccessibleName("Advanced analysis results")
        time_tab = QWidget()
        time_layout = QVBoxLayout(time_tab)
        self.time_plot = pg.PlotWidget(title="Signal and envelope")
        self.time_plot.setAccessibleName("Time signal and envelope plot")
        self.region = pg.LinearRegionItem()
        self.time_plot.addItem(self.region)
        time_layout.addWidget(self.time_plot)
        self.time_parameters = self._parameter_label(time_layout, "Time-analysis parameters")
        tabs.addTab(time_tab, "Time and envelope")

        stft_tab = QWidget()
        stft_layout = QVBoxLayout(stft_tab)
        self.stft_plot = pg.PlotWidget(title="STFT")
        self.stft_plot.setAccessibleName("STFT time frequency plot")
        self.stft_image = pg.ImageItem()
        self.stft_plot.addItem(self.stft_image)
        stft_layout.addWidget(self.stft_plot)
        self.stft_parameters = self._parameter_label(stft_layout, "STFT parameters")
        tabs.addTab(stft_tab, "STFT")

        wavelet_tab = QWidget()
        wavelet_layout = QVBoxLayout(wavelet_tab)
        self.wavelet_plot = pg.PlotWidget(title="Wavelet scalogram")
        self.wavelet_plot.setAccessibleName("Continuous wavelet scalogram")
        self.wavelet_image = pg.ImageItem()
        self.wavelet_plot.addItem(self.wavelet_image)
        wavelet_layout.addWidget(self.wavelet_plot)
        self.wavelet_parameters = self._parameter_label(wavelet_layout, "Wavelet parameters")
        tabs.addTab(wavelet_tab, "Wavelet")

        envelope_tab = QWidget()
        envelope_layout = QVBoxLayout(envelope_tab)
        self.envelope_spectrum_plot = pg.PlotWidget(title="Envelope spectrum and harmonics")
        self.envelope_spectrum_plot.setAccessibleName("Envelope spectrum and harmonic markers")
        envelope_layout.addWidget(self.envelope_spectrum_plot)
        self.envelope_parameters = self._parameter_label(
            envelope_layout, "Envelope-spectrum parameters"
        )
        tabs.addTab(envelope_tab, "Envelope spectrum")

        cepstrum_tab = QWidget()
        cepstrum_layout = QVBoxLayout(cepstrum_tab)
        self.cepstrum_plot = pg.PlotWidget(title="Real cepstrum")
        self.cepstrum_plot.setAccessibleName("Cepstrum plot")
        cepstrum_layout.addWidget(self.cepstrum_plot)
        self.cepstrum_parameters = self._parameter_label(cepstrum_layout, "Cepstrum parameters")
        tabs.addTab(cepstrum_tab, "Cepstrum")

        cross_tab = QWidget()
        cross_layout = QVBoxLayout(cross_tab)
        self.cross_spectrum_plot = pg.PlotWidget(title="Cross-spectral density")
        self.cross_spectrum_plot.setAccessibleName("Cross spectral density plot")
        self.coherence_plot = pg.PlotWidget(title="Magnitude-squared coherence")
        self.coherence_plot.setAccessibleName("Coherence plot")
        cross_layout.addWidget(self.cross_spectrum_plot)
        cross_layout.addWidget(self.coherence_plot)
        self.cross_parameters = self._parameter_label(cross_layout, "Cross-analysis parameters")
        tabs.addTab(cross_tab, "Cross spectrum and coherence")

        events_tab = QWidget()
        events_layout = QVBoxLayout(events_tab)
        self.events_table = QTableWidget(0, 6)
        self.events_table.setHorizontalHeaderLabels(
            ["Type", "Channel", "Start (s)", "End (s)", "Peak (s)", "Peak value"]
        )
        self.events_table.setAccessibleName("Detected events and transients")
        events_layout.addWidget(self.events_table)
        self.event_parameters = self._parameter_label(events_layout, "Detection parameters")
        tabs.addTab(events_tab, "Events")

        measurements_tab = QWidget()
        measurements_layout = QHBoxLayout(measurements_tab)
        self.measurements_table = QTableWidget(0, 2)
        self.measurements_table.setHorizontalHeaderLabels(["Measurement", "Value"])
        self.measurements_table.setAccessibleName("Exportable measurements")
        self.parameters_table = QTableWidget(0, 2)
        self.parameters_table.setHorizontalHeaderLabels(["Parameter", "Value"])
        self.parameters_table.setAccessibleName("Processing parameters")
        measurements_layout.addWidget(self.measurements_table)
        measurements_layout.addWidget(self.parameters_table)
        tabs.addTab(measurements_tab, "Measurements and parameters")
        layout.addWidget(tabs, stretch=1)

        self.cursors = LinkedAnalysisCursors(
            self.time_plot, self.stft_plot, self.envelope_spectrum_plot
        )
        self.status_label = QLabel("Select or generate a signal.")
        self.status_label.setAccessibleName("Advanced analysis status")
        layout.addWidget(self.status_label)
        self.analyze_button.clicked.connect(self.analyze_region)
        self.reset_region_button.clicked.connect(self.select_full_signal)
        self.export_button.clicked.connect(self._choose_export_path)
        self.auto_threshold.toggled.connect(self.event_threshold.setDisabled)

    @staticmethod
    def _parameter_label(layout: QVBoxLayout, accessible_name: str) -> QLabel:
        label = QLabel("Parameters: not calculated")
        label.setWordWrap(True)
        label.setAccessibleName(accessible_name)
        layout.addWidget(label)
        return label

    def set_input_signal(self, signal: Signal) -> None:
        self._signal = signal
        self.time_plot.clear()
        self.time_plot.addItem(self.region)
        values = signal.time_data if signal.is_mono else signal.time_data[:, 0]
        self.time_plot.plot(signal.time_vector, np.real(values), pen=pg.mkPen("#4aa3ff"))
        self.select_full_signal()
        self.status_label.setText("Ready")

    def update_signal_list(self, signals: list[Signal]) -> None:
        selected_id = getattr(self.comparison_combo.currentData(), "metadata", None)
        selected_id = getattr(selected_id, "id", None)
        self.comparison_combo.clear()
        self.comparison_combo.addItem("None", None)
        selected_row = 0
        for index, signal in enumerate(signals, start=1):
            self.comparison_combo.addItem(signal.metadata.name, signal)
            if signal.metadata.id == selected_id:
                selected_row = index
        self.comparison_combo.setCurrentIndex(selected_row)

    def select_full_signal(self) -> None:
        if self._signal is not None:
            self.region.setRegion(
                (self._signal.start_time, self._signal.start_time + self._signal.duration)
            )

    def _config(self) -> STFTConfig:
        boundary_text = self.boundary_combo.currentText()
        boundary = None if boundary_text == "none" else boundary_text
        return STFTConfig(
            window=self.window_combo.currentText(),
            window_length=self.window_length.value(),
            overlap=self.overlap.value(),
            fft_length=self.fft_length.value(),
            scaling=self.scaling_combo.currentText(),  # type: ignore[arg-type]
            boundary=boundary,  # type: ignore[arg-type]
        )

    def analyze_region(self) -> bool:
        if self._signal is None:
            self._show_error("No signal is available")
            return False
        signal = self._signal
        bounds = tuple(float(value) for value in self.region.getRegion())
        config = self._config()
        if self.auto_threshold.isChecked():
            threshold = float(
                np.mean(np.abs(self._signal.time_data)) + 2 * np.std(self._signal.time_data)
            )
            threshold = max(threshold, np.finfo(float).eps)
        else:
            threshold = self.event_threshold.value()
        event_config = EventDetectionConfig(
            threshold=threshold,
            direction=self.event_direction.currentText(),  # type: ignore[arg-type]
            minimum_duration=self.event_minimum_duration.value(),
            minimum_distance=self.event_minimum_distance.value(),
            hysteresis=self.event_hysteresis.value(),
        )
        comparison = self.comparison_combo.currentData()
        if comparison is signal:
            comparison = None
        prominence = self.transient_prominence.value() or None
        transient_distance = self.transient_minimum_distance.value()
        transient_smoothing = self.transient_smoothing.value()
        return self._tasks.submit_cancellable(
            lambda token: self._service.analyze(
                signal,
                stft_config=config,
                region=(bounds[0], bounds[1]),
                event_config=event_config,
                comparison_signal=comparison,
                transient_prominence=prominence,
                transient_minimum_distance=transient_distance,
                transient_smoothing=transient_smoothing,
                cancellation_check=token.raise_if_cancelled,
            ),
            self._display_result,
        )

    def _display_result(self, result: AdvancedAnalysisResult) -> None:
        self._result = result
        signal = result.selected_signal
        values = signal.time_data if signal.is_mono else signal.time_data[:, 0]
        envelope = result.envelope.time_data if signal.is_mono else result.envelope.time_data[:, 0]
        self.time_plot.clear()
        self.time_plot.addItem(self.region)
        self.time_plot.addItem(self.cursors.time_line)
        self.time_plot.plot(
            signal.time_vector, np.real(values), pen=pg.mkPen("#4aa3ff"), name="signal"
        )
        self.time_plot.plot(signal.time_vector, envelope, pen=pg.mkPen("#ffb347"), name="envelope")
        stft_values = result.stft.magnitude
        if stft_values.ndim == 3:
            stft_values = stft_values[:, :, 0]
        self.stft_image.setImage(20 * np.log10(np.maximum(stft_values.T, 1e-15)), autoLevels=True)
        if result.stft.times.size and result.stft.frequencies.size:
            self.stft_image.setRect(
                QRectF(
                    float(result.stft.times[0]),
                    float(result.stft.frequencies[0]),
                    max(float(np.ptp(result.stft.times)), 1 / signal.sampling_rate),
                    max(float(np.ptp(result.stft.frequencies)), 1.0),
                )
            )
        wavelet_values = result.wavelet.scalogram
        if wavelet_values.ndim == 3:
            wavelet_values = wavelet_values[:, :, 0]
        self.wavelet_image.setImage(wavelet_values.T, autoLevels=True)
        self.wavelet_image.setRect(
            QRectF(
                float(result.wavelet.times[0]),
                float(np.min(result.wavelet.frequencies)),
                max(float(np.ptp(result.wavelet.times)), 1 / signal.sampling_rate),
                max(float(np.ptp(result.wavelet.frequencies)), 1.0),
            )
        )
        envelope_result = result.envelope_spectrum
        self.envelope_spectrum_plot.clear()
        self.envelope_spectrum_plot.addItem(self.cursors.spectrum_frequency_line)
        self.envelope_spectrum_plot.plot(
            envelope_result.frequencies,
            envelope_result.magnitude,
            pen=pg.mkPen("#4aa3ff"),
        )
        for marker in result.harmonics:
            if marker.in_band:
                self.envelope_spectrum_plot.addItem(
                    pg.InfiniteLine(pos=marker.frequency, angle=90, pen=pg.mkPen("#ffb347"))
                )
        self.cepstrum_plot.clear()
        cepstrum_values = result.cepstrum.values
        if cepstrum_values.ndim == 2:
            cepstrum_values = cepstrum_values[:, 0]
        self.cepstrum_plot.plot(result.cepstrum.quefrencies, cepstrum_values)
        self.cross_spectrum_plot.clear()
        self.coherence_plot.clear()
        if result.cross_spectrum is not None and result.coherence is not None:
            cross_values = np.abs(result.cross_spectrum.values)
            coherence_values = result.coherence.values
            if cross_values.ndim == 2:
                cross_values = cross_values[:, 0]
                coherence_values = coherence_values[:, 0]
            self.cross_spectrum_plot.plot(result.cross_spectrum.frequencies, cross_values)
            self.coherence_plot.plot(result.coherence.frequencies, coherence_values)
        detected = [
            *(("event", event) for event in result.events.events),
            *(("transient", event) for event in result.transients.events),
        ]
        self.events_table.setRowCount(len(detected))
        for row, (kind, event) in enumerate(detected):
            for column, value in enumerate(
                (
                    kind,
                    event.channel,
                    event.start_time,
                    event.end_time,
                    event.peak_time,
                    event.peak_value,
                )
            ):
                self.events_table.setItem(row, column, QTableWidgetItem(str(value)))
        self.time_parameters.setText(
            "Parameters: analytic envelope; instantaneous phase gradient; "
            f"region={signal.start_time:g}..{signal.start_time + signal.duration:g} s"
        )
        self.stft_parameters.setText(
            f"Parameters: {json.dumps(result.stft.parameters, default=str)}"
        )
        self.wavelet_parameters.setText(
            f"Parameters: {json.dumps(result.wavelet.parameters, default=str)}"
        )
        self.envelope_parameters.setText(
            f"Parameters: FFT length={result.envelope_spectrum.n_points}; "
            f"harmonics={len(result.harmonics)}"
        )
        self.cepstrum_parameters.setText(
            f"Parameters: {json.dumps(result.cepstrum.parameters, default=str)}"
        )
        self.cross_parameters.setText(
            "Parameters: no comparison signal"
            if result.cross_spectrum is None
            else f"Parameters: {json.dumps(result.cross_spectrum.parameters, default=str)}"
        )
        self.event_parameters.setText(
            "Parameters: events="
            f"{json.dumps(result.events.parameters, default=str)}; transients="
            f"{json.dumps(result.transients.parameters, default=str)}"
        )
        self._fill_table(self.measurements_table, result.measurements)
        self._fill_table(self.parameters_table, result.parameters)
        self.status_label.setText(
            f"Analyzed {signal.n_samples} samples; detected {len(result.events.events)} events "
            f"and {len(result.transients.events)} transients"
        )

    @staticmethod
    def _fill_table(table: QTableWidget, values: dict[str, Any]) -> None:
        table.setRowCount(len(values))
        for row, (name, value) in enumerate(values.items()):
            table.setItem(row, 0, QTableWidgetItem(str(name)))
            table.setItem(row, 1, QTableWidgetItem(json.dumps(value, default=str)))

    def export_measurements(self, path: Path) -> None:
        if self._result is None:
            raise ValueError("Run analysis before exporting measurements")
        with path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(["measurement", "value"])
            writer.writerows(self._result.measurements.items())
            writer.writerow([])
            writer.writerow(["parameter", "value"])
            writer.writerows(
                (name, json.dumps(value, default=str))
                for name, value in self._result.parameters.items()
            )

    def _choose_export_path(self) -> None:
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export measurements", "analysis_measurements.csv", "CSV files (*.csv)"
        )
        if filename:
            self.export_measurements(Path(filename))

    def _set_busy(self, busy: bool) -> None:
        self.analyze_button.setEnabled(not busy)
        self.status_label.setText("Processing…" if busy else self.status_label.text())

    def _show_error(self, message: str) -> None:
        self.status_label.setText(f"Error: {message}")
