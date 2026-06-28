from __future__ import annotations

import pyqtgraph as pg
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QWidget


class CursorInfo(QWidget):
    position_changed = pyqtSignal(float, float)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        self.x_label = QLabel("x: --")
        self.y_label = QLabel("y: --")
        self.x_label.setStyleSheet("color: #888888;")
        self.y_label.setStyleSheet("color: #888888;")
        layout.addWidget(self.x_label)
        layout.addWidget(self.y_label)
        layout.addStretch()

    def set_position(self, x: float, y: float) -> None:
        self.x_label.setText(f"x: {x:.4f}")
        self.y_label.setText(f"y: {y:.4f}")


class CrosshairCursor:
    def __init__(self, plot_widget: pg.PlotWidget) -> None:
        self.plot_widget = plot_widget
        self.v_line = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen("#f44747", width=1))
        self.h_line = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen("#f44747", width=1))
        self.plot_widget.addItem(self.v_line, ignoreBounds=True)
        self.plot_widget.addItem(self.h_line, ignoreBounds=True)
        self._proxy = pg.SignalProxy(
            self.plot_widget.scene().sigMouseMoved,
            rateLimit=60,
            slot=self._mouse_moved,
        )
        self._visible = False

    def _mouse_moved(self, event) -> None:
        pos = event[0]
        if self.plot_widget.sceneBoundingRect().contains(pos):
            mouse_point = self.plot_widget.plotItem.vb.mapSceneToView(pos)
            self.v_line.setPos(mouse_point.x())
            self.h_line.setPos(mouse_point.y())
            self.set_visible(True)

    def set_visible(self, visible: bool) -> None:
        self.v_line.setVisible(visible)
        self.h_line.setVisible(visible)
        self._visible = visible
