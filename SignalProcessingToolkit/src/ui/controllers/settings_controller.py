from __future__ import annotations

from PyQt6.QtWidgets import QWidget

from src.core.events import EventBus
from src.core.settings import SettingsManager
from src.ui.controllers.base_controller import BaseController


class SettingsController(BaseController):
    def __init__(self, event_bus: EventBus) -> None:
        self.settings_manager = SettingsManager()
        super().__init__(event_bus)

    def show_dialog(self, parent: QWidget | None) -> None:
        from src.ui.components.dialogs.settings_dialog import SettingsDialog

        dialog = SettingsDialog(parent)
        if dialog.exec():
            new_settings = dialog.get_settings()
            self.settings_manager.set("theme", new_settings["theme"])
            self.event_bus.publish("theme:changed", theme=new_settings["theme"])
            self.event_bus.publish("settings:updated", settings=new_settings)

    def _connect_events(self) -> None:
        self.event_bus.subscribe("settings:open", self._on_open_settings)

    def _on_open_settings(self, **kwargs) -> None:
        pass
