from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from src.config import Theme, settings

logger = logging.getLogger(__name__)


class SettingsManager:
    def __init__(self, config_path: Path | None = None) -> None:
        self._config_path = config_path or settings.data_dir / "settings.json"
        self._cache: dict[str, Any] = {}

    def get(self, key: str, default: Any = None) -> Any:
        return self._cache.get(key, getattr(settings, key, default))

    def set(self, key: str, value: Any) -> None:
        self._cache[key] = value

    def save(self) -> None:
        merged = {**settings.model_dump(), **self._cache}
        self._config_path.write_text(json.dumps(merged, indent=2, default=str))
        logger.info("Settings saved to %s", self._config_path)

    def load(self) -> None:
        if self._config_path.exists():
            data = json.loads(self._config_path.read_text())
            self._cache.update(data)
            logger.info("Settings loaded from %s", self._config_path)

    @property
    def theme(self) -> Theme:
        val = self.get("theme", "dark")
        return "dark" if val == "dark" else "light"

    @theme.setter
    def theme(self, value: Theme) -> None:
        self.set("theme", value)
