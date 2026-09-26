from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QKeySequence, QShortcut
from PyQt6.QtWidgets import QLabel, QListWidget, QListWidgetItem, QVBoxLayout, QWidget


@dataclass(frozen=True, slots=True)
class NavigationItem:
    title: str
    key: str
    shortcut: str | None = None


NAV_ITEMS = (
    NavigationItem("Dashboard", "dashboard", "Alt+1"),
    NavigationItem("Signal Generator", "generator", "Alt+2"),
    NavigationItem("Signal Operations", "operations", "Alt+3"),
    NavigationItem("Sampling", "sampling", "Alt+4"),
    NavigationItem("Convolution", "convolution", "Alt+5"),
    NavigationItem("Correlation", "correlation", "Alt+6"),
    NavigationItem("FFT Analysis", "fft", "Alt+7"),
    NavigationItem("Advanced Analysis", "analysis", "Ctrl+Alt+A"),
    NavigationItem("Edge AI", "edge_ai", "Ctrl+Alt+I"),
    NavigationItem("Pipeline Editor", "pipelines", "Ctrl+Alt+P"),
    NavigationItem("Window Functions", "windows", "Alt+8"),
    NavigationItem("Digital Filters", "filters", "Alt+9"),
    NavigationItem("Noise Processing", "noise"),
    NavigationItem("Audio", "audio"),
    NavigationItem("Image Processing", "image"),
    NavigationItem("Live Monitor", "monitor", "Ctrl+M"),
    NavigationItem("Settings", "settings", "Ctrl+,"),
)


class Sidebar(QWidget):
    navigation_changed = pyqtSignal(int, str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(220)
        self._shortcuts: list[QShortcut] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        header = QLabel("  Signal Toolkit")
        header.setObjectName("sidebarHeader")
        header.setFixedHeight(48)
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        header.setFont(font)
        layout.addWidget(header)

        self.list_widget = QListWidget()
        self.list_widget.setObjectName("sidebarList")
        self.list_widget.setAccessibleName("Application pages")
        self.list_widget.setSpacing(2)
        for row, descriptor in enumerate(NAV_ITEMS):
            item = QListWidgetItem(descriptor.title)
            item.setData(Qt.ItemDataRole.UserRole, descriptor.key)
            if descriptor.shortcut:
                item.setToolTip(f"{descriptor.title} ({descriptor.shortcut})")
                shortcut = QShortcut(QKeySequence(descriptor.shortcut), self)
                shortcut.activated.connect(
                    lambda selected=row: self.list_widget.setCurrentRow(selected)
                )
                self._shortcuts.append(shortcut)
            self.list_widget.addItem(item)
        self.list_widget.currentRowChanged.connect(self._on_item_changed)
        layout.addWidget(self.list_widget)
        self.list_widget.setCurrentRow(0)

    def _on_item_changed(self, row: int) -> None:
        item = self.list_widget.item(row)
        if item is not None:
            self.navigation_changed.emit(row, str(item.data(Qt.ItemDataRole.UserRole)))

    def select(self, key: str) -> None:
        for row, descriptor in enumerate(NAV_ITEMS):
            if descriptor.key == key:
                self.list_widget.setCurrentRow(row)
                return
        raise KeyError(f"Unknown navigation page: {key}")
