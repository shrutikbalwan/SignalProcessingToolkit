"""Application dashboard backed by the shared signal state."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QGridLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from signal_processing_toolkit.models.signal import Signal


class DashboardView(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("dashboardView")
        layout = QVBoxLayout(self)
        title = QLabel("Dashboard")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        self.state_stack = QStackedWidget(self)
        self.empty_label = QLabel("Generate or load a signal to begin.")
        self.empty_label.setObjectName("emptyStateLabel")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setAccessibleName("No active signal")
        self.state_stack.addWidget(self.empty_label)

        self.loading_label = QLabel("Loading signal…")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label.setAccessibleName("Loading signal")
        self.state_stack.addWidget(self.loading_label)

        self.error_label = QLabel("")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setWordWrap(True)
        self.state_stack.addWidget(self.error_label)

        content = QWidget(self)
        metrics = QGridLayout(content)
        self.name_value = QLabel("—")
        self.samples_value = QLabel("—")
        self.rate_value = QLabel("—")
        self.duration_value = QLabel("—")
        self.rms_value = QLabel("—")
        for row, (label, value) in enumerate(
            (
                ("Signal", self.name_value),
                ("Samples", self.samples_value),
                ("Sampling rate", self.rate_value),
                ("Duration", self.duration_value),
                ("RMS", self.rms_value),
            )
        ):
            metrics.addWidget(QLabel(f"{label}:"), row, 0)
            metrics.addWidget(value, row, 1)
        metrics.setRowStretch(5, 1)
        self.state_stack.addWidget(content)
        layout.addWidget(self.state_stack, stretch=1)

        demo_title = QLabel("ESP32 Predictive Maintenance Workbench")
        demo_title.setObjectName("sectionTitle")
        layout.addWidget(demo_title)
        self.demo_button = QPushButton("Run simulated healthy inspection")
        self.demo_button.setAccessibleName("Run predictive maintenance demo")
        self.demo_button.clicked.connect(self._run_demo)
        layout.addWidget(self.demo_button)
        self.workbench_status = QLabel("No workbench experiment run")
        self.workbench_status.setAccessibleName("Predictive maintenance status")
        self.workbench_status.setWordWrap(True)
        layout.addWidget(self.workbench_status)
        from signal_processing_toolkit.ui.workers import TaskRunner

        self._demo_runner = TaskRunner(self)
        self._demo_runner.error.connect(self._demo_error)

    def set_signal(self, signal: Signal | None) -> None:
        if signal is None:
            self.state_stack.setCurrentIndex(0)
            return
        self.name_value.setText(signal.metadata.name)
        self.samples_value.setText(str(len(signal.time_data)))
        self.rate_value.setText(f"{signal.sampling_rate:g} Hz")
        self.duration_value.setText(f"{signal.duration:.4f} s")
        self.rms_value.setText(f"{signal.rms:.6g}")
        self.state_stack.setCurrentIndex(3)

    def show_loading(self) -> None:
        self.state_stack.setCurrentIndex(1)

    def show_error(self, message: str) -> None:
        self.error_label.setText(f"Error: {message}")
        self.error_label.setAccessibleName(f"Error: {message}")
        self.state_stack.setCurrentIndex(2)

    def _run_demo(self) -> None:
        from signal_processing_toolkit.demo import PredictiveMaintenanceWorkbench

        if self._demo_runner.is_busy:
            return
        self.demo_button.setEnabled(False)
        self.workbench_status.setText("Running simulated acquisition and analysis…")
        self._demo_runner.submit(
            lambda: PredictiveMaintenanceWorkbench().run(),
            self._show_demo_result,
        )

    def _show_demo_result(self, result: object) -> None:
        self.set_workbench_result(result)
        self.demo_button.setEnabled(True)

    def _demo_error(self, message: str) -> None:
        self.workbench_status.setText(f"Workbench error: {message}")
        self.demo_button.setEnabled(True)

    def set_workbench_result(self, result: object) -> None:
        """Update the dashboard from a completed workbench result."""
        from signal_processing_toolkit.demo import PredictiveMaintenanceWorkbench

        snapshot = PredictiveMaintenanceWorkbench.dashboard_snapshot(result)  # type: ignore[arg-type]
        self.workbench_status.setText(
            f"Prediction: {snapshot.latest_prediction}; packet loss: {snapshot.packet_loss}; "
            f"DSP: {snapshot.dsp_latency_seconds * 1000:.2f} ms; "
            f"inference: {snapshot.inference_latency_seconds * 1000:.2f} ms; "
            f"events: {snapshot.event_count}."
        )
