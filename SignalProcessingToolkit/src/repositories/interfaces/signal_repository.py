from __future__ import annotations

from pathlib import Path
from typing import Protocol

from src.models.signal import Signal


class ISignalRepository(Protocol):
    def save(self, signal: Signal, path: Path) -> None: ...

    def load(self, path: Path) -> Signal: ...

    def export_csv(self, signal: Signal, path: Path) -> None: ...

    def export_wav(self, signal: Signal, path: Path) -> None: ...

    def export_txt(self, signal: Signal, path: Path) -> None: ...
