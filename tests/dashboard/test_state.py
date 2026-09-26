from signal_processing_toolkit.dashboard.state import DashboardState, SessionStatus, SourceType


def test_state_initialization() -> None:
    state = DashboardState()
    assert state.session.status is SessionStatus.IDLE
    assert state.source.source_type is SourceType.NONE
    assert state.metrics.rms is None


def test_state_copy_is_detached() -> None:
    state = DashboardState()
    snapshot = state.copy()
    snapshot.session.project_name = "Changed"
    assert state.session.project_name == "Untitled session"
