from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
from PyQt6.QtCore import QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from signal_processing_toolkit.ai.model import EdgeModel
from signal_processing_toolkit.ai.streaming import (
    DetectionSettings,
    EventDetector,
    InferencePoint,
)
from signal_processing_toolkit.models.signal import Signal
from signal_processing_toolkit.plots.base import BasePlotWidget
from signal_processing_toolkit.ui.workers import CancellationToken, TaskRunner


class EdgeAIView(QWidget):
    """Edge-model loader and bounded probability history display."""

    model_loaded = pyqtSignal(object)
    event_detected = pyqtSignal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("edgeAIView")
        self._tasks = TaskRunner(self)
        self._model: EdgeModel | None = None
        self._input_signal: Signal | None = None
        self._detector: EventDetector | None = None
        self._pending_analysis = False
        self._times: list[float] = []
        self._confidence: list[float] = []
        self._series: dict[str, list[float]] = {}
        self._curves: dict[str, Any] = {}
        self._max_history = 2000
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        title = QLabel("Edge AI")
        title.setAccessibleName("Edge AI analysis")
        layout.addWidget(title)

        controls = QHBoxLayout()
        self.load_button = QPushButton("Load ONNX / ORT model")
        self.load_button.setAccessibleName("Load Edge AI model")
        self.load_button.clicked.connect(self._choose_model)
        controls.addWidget(self.load_button)
        self.status_label = QLabel("No model loaded. Model metadata sidecar is required.")
        self.status_label.setAccessibleName("Edge AI status")
        controls.addWidget(self.status_label, 1)
        layout.addLayout(controls)

        settings = QFormLayout()
        self.threshold = QDoubleSpinBox()
        self.threshold.setRange(0.0, 1.0)
        self.threshold.setSingleStep(0.05)
        self.threshold.setValue(0.8)
        self.threshold.setAccessibleName("Detection confidence threshold")
        self.threshold.valueChanged.connect(self._configure_detector)
        settings.addRow("&Threshold:", self.threshold)
        self.smoothing = QSpinBox()
        self.smoothing.setRange(1, 1000)
        self.smoothing.setValue(1)
        self.smoothing.setAccessibleName("Probability smoothing window")
        self.smoothing.valueChanged.connect(self._configure_detector)
        settings.addRow("&Smoothing windows:", self.smoothing)
        self.cooldown = QDoubleSpinBox()
        self.cooldown.setRange(0, 3600)
        self.cooldown.setSuffix(" s")
        self.cooldown.setAccessibleName("Detection cooldown in seconds")
        self.cooldown.valueChanged.connect(self._configure_detector)
        settings.addRow("&Cooldown:", self.cooldown)
        layout.addLayout(settings)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Class", "Probability"])
        self.table.setAccessibleName("Current class probabilities")
        layout.addWidget(self.table)
        self.plot = BasePlotWidget(self)
        self.plot.set_labels(x_label="Device time (s)", y_label="Probability")
        self.plot.plot_widget.setYRange(0, 1)
        layout.addWidget(self.plot)
        self._tasks.busy_changed.connect(self._set_busy)
        self._tasks.error.connect(self.show_error)

    def _choose_model(self) -> None:
        selected, _ = QFileDialog.getOpenFileName(
            self, "Load Edge AI model", "", "ONNX models (*.onnx *.ort)"
        )
        if selected:
            self.load_model(Path(selected))

    def load_model(self, path: Path) -> bool:
        self.status_label.setText("Loading and validating model…")
        return self._tasks.submit(lambda: EdgeModel.load(path), self.set_model, self.show_error)

    def set_model(self, model: EdgeModel) -> None:
        self._model = model
        self._times.clear()
        self._series = {label: [] for label in model.metadata.labels}
        self._confidence.clear()
        self.plot.clear()
        colors = ("#22d3ee", "#f59e0b", "#a78bfa", "#34d399", "#fb7185")
        self._curves = {
            label: self.plot.plot(
                np.empty(0), np.empty(0), name=label, color=colors[index % len(colors)]
            )
            for index, label in enumerate(model.metadata.labels)
        }
        self._curves["__confidence__"] = self.plot.plot(
            np.empty(0), np.empty(0), name="Confidence", color="#f8fafc"
        )
        self.table.setRowCount(len(model.metadata.labels))
        for row, label in enumerate(model.metadata.labels):
            self.table.setItem(row, 0, QTableWidgetItem(label))
            self.table.setItem(row, 1, QTableWidgetItem("—"))
        self.status_label.setText(
            f"{model.path.name} · {', '.join(model.session.providers)} · "
            f"SHA-256 {model.checksum_sha256[:12]}…"
        )
        self._configure_detector()
        self.model_loaded.emit(model)
        if self._input_signal is not None:
            if self._tasks.is_busy:
                self._pending_analysis = True
            else:
                QTimer.singleShot(0, self._analyze_current_signal)

    def set_input_signal(self, signal: Signal | None) -> None:
        self._input_signal = signal
        if signal is None:
            if self._model is None:
                self.status_label.setText("No model loaded. Model metadata sidecar is required.")
            else:
                self.status_label.setText("Model ready. Generate or load a signal to analyze.")
            return
        if self._model is None:
            self.status_label.setText("Signal ready. Load an ONNX or ORT model to analyze it.")
            return
        self._analyze_current_signal()

    def _analyze_current_signal(self) -> None:
        model = self._model
        signal = self._input_signal
        if model is None or signal is None:
            return
        if self._tasks.is_busy:
            self._pending_analysis = True
            return
        self._pending_analysis = False
        self.status_label.setText("Running windowed inference…")
        self._tasks.submit_cancellable(
            lambda token: self._infer_signal(model, signal, token),
            self._show_inference,
            self.show_error,
        )

    @staticmethod
    def _infer_signal(
        model: EdgeModel, signal: Signal, token: CancellationToken
    ) -> list[InferencePoint]:
        pipeline = model.metadata.preprocessing
        if not np.isclose(signal.sampling_rate, pipeline.sampling_rate, rtol=0, atol=1e-12):
            raise ValueError(
                f"Model expects {pipeline.sampling_rate:g} Hz but the signal is "
                f"{signal.sampling_rate:g} Hz; resample explicitly before inference"
            )
        window_samples = pipeline.window_samples
        if signal.n_samples < window_samples:
            raise ValueError(
                f"Signal has {signal.n_samples} samples; model requires {window_samples}"
            )
        data = signal.time_data[:, np.newaxis] if signal.time_data.ndim == 1 else signal.time_data
        hop_samples = max(1, window_samples // 2)
        starts = list(range(0, signal.n_samples - window_samples + 1, hop_samples))
        points: list[InferencePoint] = []
        for batch_start in range(0, len(starts), 128):
            token.raise_if_cancelled()
            selected_starts = starts[batch_start : batch_start + 128]
            windows = np.stack(
                [data[start : start + window_samples] for start in selected_starts], axis=0
            )
            result = model.predict(windows)
            point_latency = result.latency_seconds / len(selected_starts)
            for start, probabilities in zip(selected_starts, result.probabilities, strict=True):
                index = int(np.argmax(probabilities))
                timestamp = signal.start_time + start / signal.sampling_rate
                points.append(
                    InferencePoint(
                        sequence=start // hop_samples,
                        device_timestamp=timestamp,
                        host_timestamp=timestamp,
                        labels=result.labels,
                        probabilities=tuple(float(value) for value in probabilities),
                        confidence=float(probabilities[index]),
                        predicted_label=result.labels[index],
                        latency_seconds=point_latency,
                    )
                )
        return points

    def _show_inference(self, points: list[InferencePoint]) -> None:
        self._times.clear()
        self._confidence.clear()
        for values in self._series.values():
            values.clear()
        if self._detector is not None:
            self._detector.reset()
        for point in points:
            self.append_inference(point)

    def append_inference(self, point: InferencePoint) -> None:
        if tuple(self._series) != point.labels:
            raise ValueError("Inference labels do not match the displayed model")
        self._times.append(point.device_timestamp)
        if len(self._times) > self._max_history:
            self._times.pop(0)
        self._confidence.append(point.confidence)
        if len(self._confidence) > self._max_history:
            self._confidence.pop(0)
        for row, (label, probability) in enumerate(
            zip(point.labels, point.probabilities, strict=True)
        ):
            self._series[label].append(probability)
            if len(self._series[label]) > self._max_history:
                self._series[label].pop(0)
            item = self.table.item(row, 1)
            if item is not None:
                item.setText(f"{probability:.4f}")
            self._curves[label].setData(np.asarray(self._times), np.asarray(self._series[label]))
        self._curves["__confidence__"].setData(
            np.asarray(self._times), np.asarray(self._confidence)
        )
        status = (
            f"{point.predicted_label}: {point.confidence:.1%} · "
            f"latency {point.latency_seconds * 1000:.2f} ms"
        )
        event = None if self._detector is None else self._detector.update(point)
        if event is not None:
            status = f"Detected {event.label}: {event.confidence:.1%} · {status}"
            self.event_detected.emit(event)
        self.status_label.setText(status)

    def _configure_detector(self) -> None:
        if self._model is None:
            return
        self._detector = EventDetector(
            self._model.metadata.labels,
            DetectionSettings(
                threshold=self.threshold.value(),
                smoothing_window=self.smoothing.value(),
                cooldown_seconds=self.cooldown.value(),
            ),
        )

    def show_error(self, message: str) -> None:
        self.status_label.setText(f"Error: {message}")

    def _set_busy(self, busy: bool) -> None:
        self.load_button.setEnabled(not busy)
        if not busy and self._pending_analysis:
            QTimer.singleShot(0, self._analyze_current_signal)

    @property
    def model(self) -> EdgeModel | None:
        return self._model
