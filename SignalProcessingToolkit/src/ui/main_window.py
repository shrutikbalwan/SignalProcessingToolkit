from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QAction, QDragEnterEvent, QDropEvent, QKeySequence
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QSplitter,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from src.core.events import EventBus
from src.core.plugins import PluginManager
from src.core.recent_files import RecentFilesManager
from src.ui.components.graph_area import GraphArea
from src.ui.components.parameter_panel import ParameterPanel
from src.ui.components.sidebar import Sidebar
from src.ui.components.statusbar import StatusBar
from src.ui.components.theme_switcher import ThemeSwitcher
from src.ui.components.toolbar import MainToolBar
from src.ui.controllers.main_controller import MainController
from src.ui.styles.theme_manager import ThemeManager
from src.ui.views.dashboard_view import ProfessionalDashboard

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    recent_menu: QMenu

    def __init__(
        self,
        event_bus: EventBus,
        main_controller: MainController | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.event_bus = event_bus
        self.theme_manager = ThemeManager()
        self.main_controller = main_controller or MainController(event_bus)

        self.recent_files = RecentFilesManager()
        self.plugin_manager = PluginManager()
        self._setup_window()
        self._create_toolbar()
        self._create_statusbar()
        self.stacked_widget = QStackedWidget()
        self._create_menus()
        self._create_central_widget()
        self._register_views()
        self._connect_events()
        self._apply_theme()
        self._add_theme_switcher_to_toolbar()
        self.setAcceptDrops(True)
        self._discover_plugins()

    def _setup_window(self) -> None:
        self.setWindowTitle("Signal Processing Toolkit")
        self.setMinimumSize(QSize(1300, 900))
        self.resize(1600, 1000)

    def _create_toolbar(self) -> None:
        self.toolbar = MainToolBar(self)
        self.addToolBar(self.toolbar)

    def _create_statusbar(self) -> None:
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("Ready")

    def _create_top_toolbar(self) -> QWidget:
        toolbar = QWidget()
        toolbar.setObjectName("topToolbar")
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(15, 10, 15, 10)

        title_label = QLabel("Signal Processing Controller")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #0078d4;")
        layout.addWidget(title_label)

        layout.addStretch()

        self.theme_switcher = ThemeSwitcher(self)
        layout.addWidget(self.theme_switcher)

        return toolbar

    def _create_central_widget(self) -> None:
        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.sidebar = Sidebar(self)

        central_widget = QWidget()
        central_layout = QVBoxLayout(central_widget)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)

        self.top_toolbar = self._create_top_toolbar()
        central_layout.addWidget(self.top_toolbar)

        content_splitter = QSplitter(Qt.Orientation.Horizontal)

        self.graph_area = GraphArea(self)
        content_splitter.addWidget(self.graph_area)

        self.parameter_panel = ParameterPanel(self)
        content_splitter.addWidget(self.parameter_panel)
        content_splitter.setSizes([800, 300])
        content_splitter.setStretchFactor(0, 2)
        content_splitter.setStretchFactor(1, 1)

        central_layout.addWidget(content_splitter)

        self.statusbar_widget = StatusBar(self)
        central_layout.addWidget(self.statusbar_widget)

        splitter.addWidget(self.sidebar)
        splitter.addWidget(central_widget)
        splitter.setSizes([250, 1350])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        self.setCentralWidget(splitter)

    def _create_menus(self) -> None:
        menubar = self.menuBar()
        assert menubar is not None

        file_menu = menubar.addMenu("&File")
        assert file_menu is not None
        self._add_action(file_menu, "&New Project", "Ctrl+N", self._on_new_project)
        self._add_action(file_menu, "&Open Project", "Ctrl+O", self._on_open_project)
        self._add_action(file_menu, "&Save Project", "Ctrl+S", self._on_save_project)
        self._add_action(file_menu, "Save &As...", "Ctrl+Shift+S", self._on_save_as)
        file_menu.addSeparator()
        recent_menu = file_menu.addMenu("&Recent Files")
        self.recent_menu = recent_menu if recent_menu is not None else QMenu("&Recent Files", self)
        self._update_recent_menu()
        file_menu.addSeparator()
        self._add_action(file_menu, "E&xit", "Ctrl+Q", self.close)

        edit_menu = menubar.addMenu("&Edit")
        assert edit_menu is not None
        self._add_action(edit_menu, "&Undo", "Ctrl+Z", self._on_undo)
        self._add_action(edit_menu, "&Redo", "Ctrl+Y", self._on_redo)

        view_menu = menubar.addMenu("&View")
        assert view_menu is not None
        self._add_action(view_menu, "&Dark Theme", "", lambda: self._switch_theme("dark"))
        self._add_action(view_menu, "&Light Theme", "", lambda: self._switch_theme("light"))
        view_menu.addSeparator()
        self._add_action(view_menu, "&Live Monitor", "Ctrl+M", self._on_live_monitor)

        tools_menu = menubar.addMenu("&Tools")
        assert tools_menu is not None
        self._add_action(tools_menu, "&Settings", "Ctrl+,", self._on_settings)
        tools_menu.addSeparator()
        self._add_action(tools_menu, "&Plugin Manager", "", self._on_plugin_manager)

        help_menu = menubar.addMenu("&Help")
        assert help_menu is not None
        self._add_action(help_menu, "&About", "", self._on_about)

    def _add_theme_switcher_to_toolbar(self) -> None:
        if hasattr(self, "toolbar"):
            self.toolbar.addWidget(self.theme_switcher)

    def _register_views(self) -> None:
        from PyQt6.QtWidgets import QWidget as _QWidget

        prof_dash = ProfessionalDashboard(self)
        if isinstance(prof_dash, _QWidget):
            self.stacked_widget.addWidget(prof_dash)
        for _name, view in self.main_controller.get_views():
            if isinstance(view, _QWidget):
                self.stacked_widget.addWidget(view)

    def _connect_events(self) -> None:
        self.sidebar.navigation_changed.connect(self._on_navigation_changed)
        self.event_bus.subscribe("status:message", self._on_status_message)

    def _apply_theme(self) -> None:
        self.theme_manager.apply_theme(self)

    def _switch_theme(self, theme: str) -> None:
        self.theme_manager.set_theme(theme)  # type: ignore[arg-type]
        self._apply_theme()
        self.event_bus.publish("theme:changed", theme=theme)

    def _on_navigation_changed(self, index: int, name: str) -> None:
        if 0 <= index < self.stacked_widget.count():
            self.stacked_widget.setCurrentIndex(index)
        self.event_bus.publish("navigation:changed", view=name)

    def _on_status_message(self, message: str) -> None:
        self.statusbar.showMessage(message)

    def _on_new_project(self) -> None:
        self.event_bus.publish("project:new")

    def _on_open_project(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Project", "", "Project Files (*.spt);;All Files (*)"
        )
        if path:
            self.event_bus.publish("project:open", path=Path(path))

    def _on_save_project(self) -> None:
        self.event_bus.publish("project:save")

    def _on_save_as(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Project As", "", "Project Files (*.spt);;All Files (*)"
        )
        if path:
            self.event_bus.publish("project:save_as", path=Path(path))

    def _on_undo(self) -> None:
        self.event_bus.publish("edit:undo")

    def _on_redo(self) -> None:
        self.event_bus.publish("edit:redo")

    def _on_settings(self) -> None:
        if self.main_controller:
            self.main_controller.settings.show_dialog(self)

    def _on_about(self) -> None:
        QMessageBox.about(
            self,
            "About Signal Processing Toolkit",
            "Signal Processing Toolkit v1.0.0\n\n"
            "A professional desktop application for signal "
            "generation, analysis, processing, and visualization.",
        )

    def dragEnterEvent(self, event: QDragEnterEvent | None) -> None:  # noqa: N802
        if event is None:
            return
        mime = event.mimeData()
        if mime and mime.hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent | None) -> None:  # noqa: N802
        if event is None:
            return
        mime = event.mimeData()
        if mime is None:
            return
        for url in mime.urls():
            path = Path(url.toLocalFile())
            if path.suffix.lower() in {".wav", ".csv", ".txt", ".npz", ".spt"}:
                self.recent_files.add(path, file_type=path.suffix[1:])
                self.event_bus.publish("file:dropped", path=path)
        self._update_recent_menu()

    def _update_recent_menu(self) -> None:
        self.recent_menu.clear()
        for f in self.recent_files.files:
            action = self.recent_menu.addAction(f.get("name", "?"))
            p = Path(f["path"])
            action.triggered.connect(
                lambda checked, path=p: self.event_bus.publish("project:open", path=path)
            )

    def _on_live_monitor(self) -> None:
        self.sidebar.list_widget.setCurrentRow(0)
        self.event_bus.publish("monitor:open")

    def _on_plugin_manager(self) -> None:
        plugins = self.plugin_manager.get_all_plugins()
        names = (
            "\n".join(
                f"{m.get_metadata().name} v{m.get_metadata().version}" for m in plugins.values()
            )
            if plugins
            else "No plugins discovered."
        )
        QMessageBox.information(self, "Plugin Manager", f"Installed plugins:\n\n{names}")

    def _discover_plugins(self) -> None:
        discovered = self.plugin_manager.discover()
        if discovered:
            logger.info("Discovered %d plugin(s)", len(discovered))

    def _add_action(self, menu: QMenu, label: str, shortcut: str, slot: Callable) -> QAction:
        action = QAction(label, self)
        if shortcut:
            action.setShortcut(QKeySequence(shortcut))
        action.triggered.connect(slot)
        menu.addAction(action)
        return action
