"""Small, deterministic formatters shared by dashboard widgets."""

from __future__ import annotations

import math
from datetime import datetime


def value(value: float | int | None, unit: str = "", precision: int = 3) -> str:
    if value is None or (isinstance(value, float) and not math.isfinite(value)):
        return "—"
    suffix = f" {unit}" if unit else ""
    return f"{value:.{precision}f}{suffix}"


def percentage(value_: float | None, precision: int = 1) -> str:
    return value(None if value_ is None else value_ * 100, "%", precision)


def duration(seconds: float | None) -> str:
    if seconds is None or seconds < 0 or not math.isfinite(seconds):
        return "—"
    minutes, remaining = divmod(seconds, 60)
    return f"{int(minutes):02d}:{remaining:04.1f}"


def timestamp(timestamp_: datetime | None) -> str:
    return "—" if timestamp_ is None else timestamp_.strftime("%H:%M:%S")
