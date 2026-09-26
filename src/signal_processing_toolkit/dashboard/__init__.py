"""Reusable dashboard presentation layer for SignalProcessingToolkit.

State and service modules remain importable without the optional GUI extra.
Qt-backed classes are loaded lazily through module attributes.
"""

__all__ = ["DashboardController", "DashboardState", "DashboardView", "DashboardViewModel"]


def __getattr__(name: str):  # noqa: ANN001
    if name == "DashboardState":
        from signal_processing_toolkit.dashboard.state import DashboardState

        return DashboardState
    if name == "DashboardViewModel":
        from signal_processing_toolkit.dashboard.viewmodel import DashboardViewModel

        return DashboardViewModel
    if name == "DashboardController":
        from signal_processing_toolkit.dashboard.controller import DashboardController

        return DashboardController
    if name == "DashboardView":
        from signal_processing_toolkit.dashboard.view import DashboardView

        return DashboardView
    raise AttributeError(name)
