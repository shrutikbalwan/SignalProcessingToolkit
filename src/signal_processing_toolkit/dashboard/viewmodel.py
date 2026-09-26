"""Observable presentation model for dashboard state."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from signal_processing_toolkit.dashboard.events import StateChanged
from signal_processing_toolkit.dashboard.state import (
    AIState,
    DashboardEvent,
    DashboardState,
    ProcessingHealth,
    RecordingState,
    SessionState,
    SignalMetrics,
    SourceState,
)


class DashboardViewModel:
    def __init__(self, state: DashboardState | None = None) -> None:
        self.state = state or DashboardState()
        self._observers: list[Callable[[DashboardState], None]] = []
        self._field_observers: list[Callable[[StateChanged], None]] = []

    def observe(self, callback: Callable[[DashboardState], None]) -> None:
        if callback not in self._observers:
            self._observers.append(callback)

    def observe_fields(self, callback: Callable[[StateChanged], None]) -> None:
        if callback not in self._field_observers:
            self._field_observers.append(callback)

    def unobserve(self, callback: Callable[[DashboardState], None]) -> None:
        if callback in self._observers:
            self._observers.remove(callback)

    def update(self, field: str, value: Any) -> None:
        if not hasattr(self.state, field):
            raise AttributeError(f"Unknown dashboard state field: {field}")
        setattr(self.state, field, value)
        self._notify(field)

    def update_session(self, session: SessionState) -> None:
        self.state.session = session
        self._notify("session")

    def update_source(self, source: SourceState) -> None:
        self.state.source = source
        self._notify("source")

    def update_metrics(self, metrics: SignalMetrics) -> None:
        self.state.metrics = metrics
        self._notify("metrics")

    def update_health(self, health: ProcessingHealth) -> None:
        self.state.health = health
        self._notify("health")

    def update_ai(self, ai: AIState) -> None:
        self.state.ai = ai
        self._notify("ai")

    def update_recording(self, recording: RecordingState) -> None:
        self.state.recording = recording
        self._notify("recording")

    def add_event(self, event: DashboardEvent) -> None:
        self.state.events.append(event)
        self._notify("events")

    def snapshot(self) -> DashboardState:
        return self.state.copy()

    def _notify(self, field: str) -> None:
        change = StateChanged(field)
        for field_callback in tuple(self._field_observers):
            field_callback(change)
        snapshot = self.snapshot()
        for state_callback in tuple(self._observers):
            state_callback(snapshot)

    def dispose(self) -> None:
        self._observers.clear()
        self._field_observers.clear()
