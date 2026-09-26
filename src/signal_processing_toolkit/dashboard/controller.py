"""Translate dashboard actions into service calls and state updates."""

from __future__ import annotations

from datetime import datetime

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from signal_processing_toolkit.dashboard.events import DashboardAction, DashboardCommand
from signal_processing_toolkit.dashboard.services import (
    DemoSource,
    MetricsService,
    MonitoringService,
    SessionService,
)
from signal_processing_toolkit.dashboard.state import (
    AIState,
    ConnectionStatus,
    DashboardEvent,
    EventSeverity,
    SourceState,
    SourceType,
)
from signal_processing_toolkit.dashboard.viewmodel import DashboardViewModel


class DashboardController(QObject):
    state_changed = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(
        self, viewmodel: DashboardViewModel | None = None, parent: QObject | None = None
    ) -> None:
        super().__init__(parent)
        self.viewmodel = viewmodel or DashboardViewModel()
        self.demo_source = DemoSource()
        self.metrics = MetricsService()
        self.monitoring = MonitoringService()
        self.sessions = SessionService()
        self._timer = QTimer(self)
        self._timer.setInterval(100)
        self._timer.timeout.connect(self._tick)
        self.demo_source.subscribe(self._on_chunk)
        self._closed = False

    def dispatch(self, action: DashboardAction | DashboardCommand) -> None:
        command = action.command if isinstance(action, DashboardAction) else action
        handlers = {
            DashboardCommand.START: self.start,
            DashboardCommand.DEMO_MODE: self.start_demo,
            DashboardCommand.PAUSE: self.pause,
            DashboardCommand.RESUME: self.resume,
            DashboardCommand.STOP: self.stop,
            DashboardCommand.TOGGLE_RECORDING: self.toggle_recording,
        }
        handlers[command]()

    def start_demo(self) -> None:
        self.viewmodel.update_source(
            SourceState(
                source_type=SourceType.DEMO,
                device_name="Deterministic demo source",
                connected=True,
                connection_status=ConnectionStatus.CONNECTED,
                sampling_rate=self.demo_source.sampling_rate,
                channels=1,
                frame_rate=10.0,
            )
        )
        self.start()

    def start(self) -> None:
        if self.viewmodel.state.session.status.value == "running":
            return
        session = self.sessions.start(self.viewmodel.state.session)
        self.viewmodel.update_session(session)
        self.demo_source.start()
        self._timer.start()
        self.viewmodel.add_event(
            DashboardEvent(event_type="session", description="Session started")
        )
        self.state_changed.emit()

    def pause(self) -> None:
        self.viewmodel.update_session(self.sessions.pause(self.viewmodel.state.session))
        self._timer.stop()
        self.viewmodel.add_event(DashboardEvent(event_type="session", description="Session paused"))
        self.state_changed.emit()

    def resume(self) -> None:
        self.viewmodel.update_session(self.sessions.resume(self.viewmodel.state.session))
        if self.viewmodel.state.session.status.value == "running":
            self.demo_source.start()
            self._timer.start()
        self.state_changed.emit()

    def stop(self) -> None:
        self._timer.stop()
        self.demo_source.stop()
        self.viewmodel.update_session(self.sessions.stop(self.viewmodel.state.session))
        source = self.viewmodel.state.source
        source.connected = False
        source.connection_status = ConnectionStatus.DISCONNECTED
        self.viewmodel.update_source(source)
        self.viewmodel.add_event(
            DashboardEvent(event_type="session", description="Session stopped")
        )
        self.state_changed.emit()

    def toggle_recording(self) -> None:
        recording = self.sessions.toggle_recording(self.viewmodel.state.recording)
        self.viewmodel.update_recording(recording)

    def set_ai_prediction(self, class_name: str, confidence: float) -> None:
        self.viewmodel.update_ai(
            AIState(
                model_loaded=True,
                model_name=self.viewmodel.state.ai.model_name
                if self.viewmodel.state.ai.model_loaded
                else "Dashboard model",
                predicted_class=class_name,
                confidence=confidence,
            )
        )
        self.viewmodel.add_event(
            DashboardEvent(
                severity=EventSeverity.WARNING if confidence < 0.8 else EventSeverity.INFO,
                event_type="ai_prediction",
                description=class_name,
                confidence=confidence,
            )
        )

    def _tick(self) -> None:
        if self._closed:
            return
        self.demo_source.next_chunk()
        session = self.viewmodel.state.session
        if session.started_at:
            session.elapsed_seconds = (datetime.now() - session.started_at).total_seconds()
            self.viewmodel.update_session(session)

    def _on_chunk(self, chunk: list[float], sequence: int) -> None:
        del sequence
        samples = (self.viewmodel.state.signal_samples + chunk)[-2_000:]
        self.viewmodel.update("signal_samples", samples)
        self.viewmodel.update("spectrum", self.metrics.spectrum(samples))
        self.viewmodel.update_metrics(
            self.metrics.calculate(samples, self.demo_source.sampling_rate)
        )
        self.viewmodel.update_health(
            self.monitoring.update(processing_latency_ms=0.1, queue_depth=0)
        )
        if self.viewmodel.state.recording.active:
            recording = self.viewmodel.state.recording
            recording.samples_written += len(chunk)
            recording.duration_seconds = recording.samples_written / self.demo_source.sampling_rate
            self.viewmodel.update_recording(recording)

    def cleanup(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._timer.stop()
        self.demo_source.stop()
        self.demo_source.unsubscribe(self._on_chunk)
        self.viewmodel.dispose()

    @property
    def timer_active(self) -> bool:
        return self._timer.isActive()
