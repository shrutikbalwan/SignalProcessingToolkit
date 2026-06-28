from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PlotTheme:
    background: str
    foreground: str
    grid: str
    axis: str
    line_colors: list[str]
    highlight: str


DARK_THEME = PlotTheme(
    background="#1e1e1e",
    foreground="#d4d4d4",
    grid="#2d2d2d",
    axis="#888888",
    line_colors=["#569cd6", "#4ec9b0", "#ce9178", "#c586c0", "#dcdcaa", "#9cdcfe"],
    highlight="#f44747",
)

LIGHT_THEME = PlotTheme(
    background="#ffffff",
    foreground="#1e1e1e",
    grid="#e0e0e0",
    axis="#888888",
    line_colors=["#0078d4", "#107c10", "#d9534f", "#8250df", "#d4a017", "#009999"],
    highlight="#d32f2f",
)
