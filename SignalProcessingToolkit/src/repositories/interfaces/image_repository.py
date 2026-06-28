from __future__ import annotations

from pathlib import Path
from typing import Protocol

from src.models.image import ImageSignal


class IImageRepository(Protocol):
    def load(self, path: Path) -> ImageSignal: ...

    def save(self, image: ImageSignal, path: Path) -> None: ...

    def get_supported_formats(self) -> set[str]: ...
