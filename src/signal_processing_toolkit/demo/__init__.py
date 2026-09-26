"""Runnable demonstrations shipped with SignalProcessingToolkit."""

from typing import Any

__all__ = [
    "ExperimentConfig",
    "ExperimentResult",
    "DashboardSnapshot",
    "PredictiveMaintenanceWorkbench",
    "SimulatedMaintenanceSource",
]


def __getattr__(name: str) -> Any:
    if name in __all__:
        from . import predictive_maintenance

        return getattr(predictive_maintenance, name)
    raise AttributeError(name)
