from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from src.models.signal import Signal


@dataclass
class Project:
    name: str
    path: str = ""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    created_at: datetime = field(default_factory=datetime.now)
    modified_at: datetime = field(default_factory=datetime.now)
    signals: list[Signal] = field(default_factory=list)
    settings: dict[str, Any] = field(default_factory=dict)
    version: str = "1.0"

    def add_signal(self, signal: Signal) -> None:
        self.signals.append(signal)
        self.modified_at = datetime.now()

    def remove_signal(self, signal_id: str) -> None:
        self.signals = [s for s in self.signals if s.metadata.id != signal_id]
        self.modified_at = datetime.now()

    def get_signal(self, signal_id: str) -> Signal | None:
        for signal in self.signals:
            if signal.metadata.id == signal_id:
                return signal
        return None

    @property
    def signal_count(self) -> int:
        return len(self.signals)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "path": self.path,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "modified_at": self.modified_at.isoformat(),
            "signal_count": self.signal_count,
            "settings": self.settings,
        }
