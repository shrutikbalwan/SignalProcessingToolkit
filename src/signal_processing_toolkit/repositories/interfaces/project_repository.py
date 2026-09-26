from __future__ import annotations

from pathlib import Path
from typing import Protocol

from signal_processing_toolkit.models.project import Project


class IProjectRepository(Protocol):
    def save(self, project: Project) -> None: ...

    def load(self, path: Path) -> Project: ...

    def list_recent(self) -> list[Path]: ...

    def delete(self, path: Path) -> None: ...
