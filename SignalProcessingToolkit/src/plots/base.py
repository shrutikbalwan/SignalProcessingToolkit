from __future__ import annotations

from typing import Any

import numpy as np
import pyqtgraph as pg
from PyQt6.QtWidgets import QVBoxLayout, QWidget

from src.plots.themes import DARK_THEME, PlotTheme


class BasePlotWidget(QWidget):
    def __init__(
        self,
        parent: QWidget | None = None,
        theme: PlotTheme | None = None,
        title: str = "",
    ) -> None:
        super().__init__(parent)
        self._theme = theme or DARK_THEME
        self._title = title
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        pg.setConfigOptions(antialias=True, foreground=self._theme.foreground)
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground(self._theme.background)
        self.plot_widget.addLegend()
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)

        if self._title:
            self.plot_widget.setTitle(self._title)

        self.plot_item = self.plot_widget.getPlotItem()
        self._configure_axis()

        layout.addWidget(self.plot_widget)

    def _configure_axis(self) -> None:
        axis = self.plot_item.getAxis("bottom")
        left = self.plot_item.getAxis("left")
        for ax in (axis, left):
            ax.setPen(self._theme.axis)
            ax.setTextPen(self._theme.foreground)

    def plot(
        self,
        x: np.ndarray,
        y: np.ndarray,
        name: str = "Signal",
        color: str | None = None,
        **kwargs: Any,
    ) -> pg.PlotDataItem:
        pen = pg.mkPen(color or self._theme.line_colors[0], width=2)
        return self.plot_widget.plot(x, y, pen=pen, name=name, **kwargs)

    def clear(self) -> None:
        self.plot_widget.clear()

    def set_labels(self, x_label: str = "", y_label: str = "") -> None:
        if x_label:
            self.plot_widget.setLabel("bottom", x_label)
        if y_label:
            self.plot_widget.setLabel("left", y_label)

    def set_theme(self, theme: PlotTheme) -> None:
        self._theme = theme
        self.plot_widget.setBackground(theme.background)

    def enable_zoom(self, enabled: bool = True) -> None:
        self.plot_widget.setMouseEnabled(x=enabled, y=enabled)

    def auto_range(self) -> None:
        self.plot_widget.autoRange()
