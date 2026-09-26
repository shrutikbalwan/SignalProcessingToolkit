"""Commands and notifications exchanged by dashboard components."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class DashboardCommand(StrEnum):
    START = "start"
    PAUSE = "pause"
    RESUME = "resume"
    STOP = "stop"
    TOGGLE_RECORDING = "toggle_recording"
    DEMO_MODE = "demo_mode"


@dataclass(frozen=True, slots=True)
class DashboardAction:
    command: DashboardCommand


@dataclass(frozen=True, slots=True)
class StateChanged:
    field: str
