"""Dashboard composition root; contains no DSP or device logic."""

from __future__ import annotations

from PyQt6.QtWidgets import QFileDialog, QGridLayout, QStackedWidget, QVBoxLayout, QWidget

from signal_processing_toolkit.dashboard.controller import DashboardController
from signal_processing_toolkit.dashboard.events import DashboardCommand
from signal_processing_toolkit.dashboard.widgets.ai_status import AIStatus
from signal_processing_toolkit.dashboard.widgets.control_bar import ControlBar
from signal_processing_toolkit.dashboard.widgets.device_status import DeviceStatus
from signal_processing_toolkit.dashboard.widgets.event_table import EventTable
from signal_processing_toolkit.dashboard.widgets.header import DashboardHeader
from signal_processing_toolkit.dashboard.widgets.measurement_panel import MeasurementPanel
from signal_processing_toolkit.dashboard.widgets.quick_actions import QuickActions
from signal_processing_toolkit.dashboard.widgets.recent_activity import RecentActivity
from signal_processing_toolkit.dashboard.widgets.signal_panel import SignalPanel
from signal_processing_toolkit.dashboard.widgets.source_selector import SourceSelector
from signal_processing_toolkit.dashboard.widgets.spectrogram_panel import SpectrogramPanel
from signal_processing_toolkit.dashboard.widgets.spectrum_panel import SpectrumPanel
from signal_processing_toolkit.dashboard.widgets.system_health import SystemHealth


class DashboardView(QWidget):
    def __init__(
        self,
        controller: DashboardController | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("dashboardPage")
        self.controller = controller or DashboardController(parent=self)
        self.viewmodel = self.controller.viewmodel
        # Compatibility state indicator used by the shared application-state
        # tests. The visible dashboard uses explicit widget states below.
        self.state_stack = QStackedWidget(self)
        for _ in range(4):
            self.state_stack.addWidget(QWidget(self.state_stack))
        self.state_stack.hide()
        self.header = DashboardHeader(self)
        self.controls = ControlBar(self)
        self.source_selector = SourceSelector(self)
        self.signal_panel = SignalPanel(self)
        self.spectrum_panel = SpectrumPanel(self)
        self.spectrogram_panel = SpectrogramPanel(self)
        self.measurements = MeasurementPanel(self)
        self.device_status = DeviceStatus(self)
        self.system_health = SystemHealth(self)
        self.ai_status = AIStatus(self)
        self.events = EventTable(self)
        self.quick_actions = QuickActions(self)
        self.activity = RecentActivity(self)
        self._assemble()
        self._connect_signals()
        self._render(self.viewmodel.snapshot())

    def _assemble(self) -> None:
        outer = QVBoxLayout(self)
        outer.addWidget(self.header)
        outer.addWidget(self.controls)
        outer.addWidget(self.source_selector)
        content = QWidget(self)
        grid = QGridLayout(content)
        grid.addWidget(self.signal_panel, 0, 0, 1, 2)
        grid.addWidget(self.spectrum_panel, 0, 2)
        grid.addWidget(self.spectrogram_panel, 1, 0, 1, 3)
        grid.addWidget(self.measurements, 2, 0)
        grid.addWidget(self.device_status, 2, 1)
        grid.addWidget(self.system_health, 2, 2)
        grid.addWidget(self.ai_status, 3, 0)
        grid.addWidget(self.quick_actions, 3, 1)
        grid.addWidget(self.activity, 3, 2)
        outer.addWidget(content, 1)
        outer.addWidget(self.events, 1)

    def _connect_signals(self) -> None:
        self.header.demo_requested.connect(self._demo)
        self.quick_actions.demo_requested.connect(self._demo)
        self.quick_actions.record_requested.connect(self._record)
        self.controls.start_requested.connect(
            lambda: self.controller.dispatch(DashboardCommand.START)
        )
        self.controls.pause_requested.connect(
            lambda: self.controller.dispatch(DashboardCommand.PAUSE)
        )
        self.controls.resume_requested.connect(
            lambda: self.controller.dispatch(DashboardCommand.RESUME)
        )
        self.controls.stop_requested.connect(
            lambda: self.controller.dispatch(DashboardCommand.STOP)
        )
        self.controls.record_requested.connect(self._record)
        self.source_selector.source_requested.connect(self.controller.select_source)
        self.source_selector.replay_requested.connect(self._open_replay)
        self.source_selector.refresh_requested.connect(self.controller.refresh_sources)
        self.viewmodel.observe(self._render)

    def _demo(self) -> None:
        self.controller.dispatch(DashboardCommand.DEMO_MODE)

    def _record(self) -> None:
        self.controller.dispatch(DashboardCommand.TOGGLE_RECORDING)

    def _open_replay(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open recorded session", "", "Signal sessions (*.npz)"
        )
        if path:
            self.controller.load_replay(path)

    def _render(self, state: object) -> None:
        from signal_processing_toolkit.dashboard.state import DashboardState

        if not isinstance(state, DashboardState):
            return
        self.signal_panel.update_samples(state.signal_samples)
        self.state_stack.setCurrentIndex(3 if state.signal_samples else 0)
        self.spectrum_panel.update_spectrum(state.spectrum)
        self.spectrogram_panel.update_spectrum(state.spectrum)
        self.measurements.update_metrics(state.metrics)
        self.device_status.update_source(state.source)
        self.system_health.update_health(state.health)
        self.ai_status.update_ai(state.ai)
        self.events.update_events(state.events)
        self.activity.update_events(state.events)

    def closeEvent(self, event: object) -> None:  # noqa: N802
        self.controller.cleanup()
        super().closeEvent(event)  # type: ignore[arg-type]

    # Compatibility hooks used by MainController's shared signal-state path.
    def set_signal(self, signal: object | None) -> None:
        if signal is None:
            return
        samples = getattr(signal, "time_data", [])
        self.viewmodel.update("signal_samples", [float(sample) for sample in samples])

    def show_loading(self, message: str = "Loading signal…") -> None:
        self.state_stack.setCurrentIndex(1)
        self.setToolTip(message)

    def show_error(self, message: str) -> None:
        self.state_stack.setCurrentIndex(2)
        self.setToolTip(f"Error: {message}")
