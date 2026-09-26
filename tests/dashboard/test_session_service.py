from signal_processing_toolkit.dashboard.services.session_service import SessionService
from signal_processing_toolkit.dashboard.state import SessionState, SessionStatus


def test_session_transitions() -> None:
    service = SessionService()
    state = service.start(SessionState())
    assert state.status is SessionStatus.RUNNING
    assert service.pause(state).status is SessionStatus.PAUSED
    assert service.resume(state).status is SessionStatus.RUNNING
    assert service.stop(state).status is SessionStatus.STOPPED
