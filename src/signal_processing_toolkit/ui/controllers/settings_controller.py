from __future__ import annotations

from pathlib import Path
from typing import Any

from PyQt6.QtWidgets import QWidget

from signal_processing_toolkit.core.events import EventBus
from signal_processing_toolkit.core.settings import SettingsManager
from signal_processing_toolkit.ui.controllers.base_controller import BaseController
from signal_processing_toolkit.ui.views.settings_view import SettingsView


class SettingsController(BaseController):
    def __init__(self, event_bus: EventBus, config_path: Path | None = None) -> None:
        self.settings_manager = SettingsManager(config_path)
        self.settings_manager.load()
        self._view: SettingsView | None = None
        super().__init__(event_bus)

    def get_view(self) -> SettingsView:
        if self._view is None:
            self._view = SettingsView(self.settings_manager, self.save)
        return self._view

    def save(self, values: dict[str, Any]) -> None:
        for key, value in values.items():
            self.settings_manager.set(key, value)
        self.settings_manager.save()
        self.event_bus.publish("theme:changed", theme=self.settings_manager.theme)
        self.event_bus.publish("settings:updated", settings=values)

    def show_dialog(self, parent: QWidget | None) -> None:
        del parent
        self.event_bus.publish("navigation:request", view="settings")

    def _connect_events(self) -> None:
        self.event_bus.subscribe("settings:open", self._on_open_settings)

    def _on_open_settings(self, **kwargs: object) -> None:
        self.event_bus.publish("navigation:request", view="settings")
