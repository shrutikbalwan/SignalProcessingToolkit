"""Session lifecycle and recording bookkeeping."""

from __future__ import annotations

from datetime import datetime

from signal_processing_toolkit.dashboard.state import RecordingState, SessionState, SessionStatus


class SessionService:
    def start(self, state: SessionState) -> SessionState:
        state.status = SessionStatus.RUNNING
        state.started_at = state.started_at or datetime.now()
        return state

    def pause(self, state: SessionState) -> SessionState:
        if state.status == SessionStatus.RUNNING:
            state.status = SessionStatus.PAUSED
        return state

    def resume(self, state: SessionState) -> SessionState:
        if state.status == SessionStatus.PAUSED:
            state.status = SessionStatus.RUNNING
        return state

    def stop(self, state: SessionState) -> SessionState:
        state.status = SessionStatus.STOPPED
        return state

    def toggle_recording(self, recording: RecordingState) -> RecordingState:
        recording.active = not recording.active
        return recording
