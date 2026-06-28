from __future__ import annotations

import json
from pathlib import Path

from src.models.project import Project


class FileProjectRepository:
    def save(self, project: Project) -> None:
        path = Path(project.path)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = project.to_dict()
        data["signals"] = []
        path.write_text(json.dumps(data, indent=2, default=str))

    def load(self, path: Path) -> Project:
        if not path.exists():
            raise FileNotFoundError(f"Project file not found: {path}")
        data = json.loads(path.read_text())
        return Project(
            name=data.get("name", "Untitled"),
            path=str(path),
            id=data.get("id", ""),
            settings=data.get("settings", {}),
            version=data.get("version", "1.0"),
        )

    def list_recent(self) -> list[Path]:
        return []

    def delete(self, path: Path) -> None:
        if path.exists():
            path.unlink()
