from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from src.models.signal import Signal


@dataclass
class PluginMetadata:
    name: str
    version: str
    author: str
    description: str
    category: str = "general"


class SignalPlugin(ABC):
    @abstractmethod
    def get_metadata(self) -> PluginMetadata: ...

    @abstractmethod
    def initialize(self) -> None: ...

    @abstractmethod
    def cleanup(self) -> None: ...

    @abstractmethod
    def process(self, signal: Signal, **params: Any) -> Signal: ...

    def get_widget(self):
        return None
