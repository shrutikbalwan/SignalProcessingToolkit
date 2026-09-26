from __future__ import annotations

from PyQt6.QtCore import QSize
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QToolBar


class MainToolBar(QToolBar):
    def __init__(self, parent=None) -> None:
        super().__init__("Main Toolbar", parent)
        self.setObjectName("mainToolbar")
        self.setIconSize(QSize(24, 24))
        self.setMovable(False)

        self._add_action("New", "Ctrl+N", "Create new project")
        self._add_action("Open", "Ctrl+O", "Open project")
        self._add_action("Save", "Ctrl+S", "Save project")
        self.addSeparator()
        self._add_action("Undo", "Ctrl+Z", "Undo")
        self._add_action("Redo", "Ctrl+Y", "Redo")
        self.addSeparator()
        self._add_action("Export", "Ctrl+E", "Export signal")

    def _add_action(self, name: str, shortcut: str, tooltip: str) -> None:
        action = QAction(name, self)
        action.setToolTip(f"{tooltip} ({shortcut})")
        self.addAction(action)
