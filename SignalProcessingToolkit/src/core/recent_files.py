from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.config import settings


class RecentFilesManager:
    def __init__(self, storage_path: Path | None = None) -> None:
        self._storage_path = storage_path or settings.data_dir / "recent_files.json"
        self._files: list[dict[str, Any]] = []
        self._load()

    @property
    def files(self) -> list[dict[str, Any]]:
        return list(self._files)

    @property
    def paths(self) -> list[Path]:
        return [Path(f["path"]) for f in self._files if "path" in f]

    def add(self, path: Path, file_type: str = "unknown") -> None:
        entry = {"path": str(path), "name": path.name, "type": file_type}
        self._files = [e for e in self._files if e.get("path") != str(path)]
        self._files.insert(0, entry)
        self._files = self._files[: settings.recent_files_max]
        self._save()

    def remove(self, path: Path) -> None:
        self._files = [e for e in self._files if e.get("path") != str(path)]
        self._save()

    def clear(self) -> None:
        self._files.clear()
        self._save()

    def _load(self) -> None:
        if self._storage_path.exists():
            try:
                data = json.loads(self._storage_path.read_text())
                self._files = data[: settings.recent_files_max]
            except (json.JSONDecodeError, OSError):
                self._files = []

    def _save(self) -> None:
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._storage_path.write_text(
            json.dumps(self._files[: settings.recent_files_max], indent=2)
        )
