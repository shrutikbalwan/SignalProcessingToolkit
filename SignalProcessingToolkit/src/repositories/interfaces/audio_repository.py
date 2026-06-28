from __future__ import annotations

from pathlib import Path
from typing import Protocol

from src.models.audio import AudioSignal


class IAudioRepository(Protocol):
    def load(self, path: Path) -> AudioSignal: ...

    def save(self, audio: AudioSignal, path: Path) -> None: ...

    def get_metadata(self, path: Path) -> dict: ...

    def get_supported_formats(self) -> set[str]: ...
