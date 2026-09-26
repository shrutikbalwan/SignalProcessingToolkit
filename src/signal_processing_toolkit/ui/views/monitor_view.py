from __future__ import annotations

import logging

import numpy as np
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from signal_processing_toolkit.plots.base import BasePlotWidget
from signal_processing_toolkit.streaming import (
    OverflowPolicy,
    PipelineState,
    PlotSink,
    StreamPipeline,
    SyntheticSource,
)

logger = logging.getLogger(__name__)


class LiveMonitorView(QWidget):
    """Non-blocking live monitor backed by the reusable streaming engine."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._timer = QTimer(self)
        self._timer.setInterval(50)
        self._timer.timeout.connect(self._update_plot)
        self._plot_sink = PlotSink(maximum_samples=8192)
        self._pipeline = StreamPipeline(
            queue_capacity=8, overflow_policy=OverflowPolicy.DROP_OLDEST
        )

        layout = QVBoxLayout(self)
        controls = QHBoxLayout()
        wave_label = QLabel("&Type:")
        self.wave_combo = QComboBox()
        wave_label.setBuddy(self.wave_combo)
        self.wave_combo.setAccessibleName("Monitor waveform type")
        self.wave_combo.addItems(["sine", "square", "sawtooth", "noise"])
        controls.addWidget(wave_label)
        controls.addWidget(self.wave_combo)

        frequency_label = QLabel("&Frequency (Hz):")
        self.freq_spin = QDoubleSpinBox()
        frequency_label.setBuddy(self.freq_spin)
        self.freq_spin.setAccessibleName("Monitor frequency in hertz")
        self.freq_spin.setRange(1, 20000)
        self.freq_spin.setValue(440)
        controls.addWidget(frequency_label)
        controls.addWidget(self.freq_spin)

        self.toggle_btn = QPushButton("Start")
        self.toggle_btn.setAccessibleName("Start live monitor")
        self.toggle_btn.clicked.connect(self._toggle)
        controls.addWidget(self.toggle_btn)
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.setAccessibleName("Pause live monitor")
        self.pause_btn.setEnabled(False)
        self.pause_btn.clicked.connect(self._toggle_pause)
        controls.addWidget(self.pause_btn)
        layout.addLayout(controls)

        self.metrics_label = QLabel("Stopped")
        self.metrics_label.setAccessibleName("Live stream metrics")
        layout.addWidget(self.metrics_label)

        self.plot = BasePlotWidget(self)
        self.plot.set_labels(x_label="Time (s)", y_label="Amplitude")
        self._curve = self.plot.plot(np.empty(0), np.empty(0), name="Monitor")
        layout.addWidget(self.plot)

        self._running = False
        self._update_count = 0

    def _toggle(self) -> None:
        if self._running:
            self.stop()
        else:
            self.start()

    def _toggle_pause(self) -> None:
        if self._pipeline.state is PipelineState.PAUSED:
            self.resume()
        elif self._pipeline.state is PipelineState.RUNNING:
            self.pause()

    def start(self) -> None:
        if self._running:
            return
        if self._pipeline.state in {PipelineState.STOPPED, PipelineState.FAILED}:
            self._pipeline.reset()
        source = SyntheticSource(
            sampling_rate=44_100,
            chunk_size=1024,
            frequency=self.freq_spin.value(),
            waveform=self.wave_combo.currentText(),
            real_time=True,
        )
        self._pipeline.configure(source, sinks=[self._plot_sink])
        self._pipeline.start()
        self._timer.start()
        self.toggle_btn.setText("Stop")
        self.toggle_btn.setAccessibleName("Stop live monitor")
        self.pause_btn.setEnabled(True)
        self._running = True

    def pause(self) -> None:
        self._pipeline.pause()
        self.pause_btn.setText("Resume")
        self.pause_btn.setAccessibleName("Resume live monitor")

    def resume(self) -> None:
        self._pipeline.resume()
        self.pause_btn.setText("Pause")
        self.pause_btn.setAccessibleName("Pause live monitor")

    def _update_plot(self) -> None:
        if self._pipeline.state is PipelineState.FAILED:
            logger.error("Live monitor pipeline failed: %s", self._pipeline.error)
            self.stop()
            return
        values, sampling_rate = self._plot_sink.snapshot()
        if values.size:
            channel = values[:, 0] if values.ndim == 2 else values
            x = np.arange(channel.size, dtype=float) / sampling_rate
            self._curve.setData(x, channel)
            self._update_count += 1
        metrics = self._pipeline.metrics
        self.metrics_label.setText(
            f"Queue {metrics.queue_depth}/8 · Dropped {metrics.dropped_frames} · "
            f"Latency {metrics.last_processing_latency_seconds * 1000:.2f} ms"
        )

    def stop(self) -> None:
        self._timer.stop()
        if self._pipeline.state in {
            PipelineState.RUNNING,
            PipelineState.PAUSED,
            PipelineState.FAILED,
        }:
            self._pipeline.stop()
        self._running = False
        self.toggle_btn.setText("Start")
        self.toggle_btn.setAccessibleName("Start live monitor")
        self.pause_btn.setText("Pause")
        self.pause_btn.setAccessibleName("Pause live monitor")
        self.pause_btn.setEnabled(False)

    def shutdown(self) -> None:
        self.stop()
        self._pipeline.close()

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def update_interval(self) -> int:
        return self._timer.interval()

    @property
    def update_count(self) -> int:
        return self._update_count

    @property
    def pipeline(self) -> StreamPipeline:
        return self._pipeline
