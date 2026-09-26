from signal_processing_toolkit.dashboard.state import AIState
from signal_processing_toolkit.dashboard.viewmodel import DashboardViewModel


def test_viewmodel_updates_and_notifies() -> None:
    model = DashboardViewModel()
    fields: list[str] = []
    snapshots = []
    model.observe_fields(lambda change: fields.append(change.field))
    model.observe(snapshots.append)
    model.update_ai(AIState(model_loaded=True, model_name="test"))
    assert fields == ["ai"]
    assert snapshots[-1].ai.model_name == "test"
