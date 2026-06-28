from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

Theme = Literal["dark", "light"]


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="SPT_",
        env_file_encoding="utf-8",
    )

    app_name: str = "Signal Processing Toolkit"
    version: str = "1.0.0"
    debug: bool = False

    theme: Theme = "dark"
    language: str = "en"
    auto_save_interval: int = 300

    default_sampling_rate: float = 44100.0
    default_duration: float = 1.0
    fft_size: int = 4096

    data_dir: Path = Path.home() / ".spt" / "data"
    export_dir: Path = Path.home() / ".spt" / "exports"
    plugins_dir: Path = Path.home() / ".spt" / "plugins"
    logs_dir: Path = Path.home() / ".spt" / "logs"

    recent_files_max: int = 10
    undo_limit: int = 50
    autosave_enabled: bool = True


settings = AppSettings()
