"""Config model and persistence helpers for the desktop application."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from threading import Lock

from .paths import get_config_path, get_default_input_path, get_default_output_path


@dataclass
class AppConfig:
    """Serializable GUI and runtime settings persisted to config.json."""

    language: str = "es"
    input_path: str = ""
    output_path: str = ""
    auto_start: bool = False
    auto_close: bool = False
    auto_close_seconds: int = 60
    window_width: int = 1080
    window_height: int = 720
    window_x: int | None = None
    window_y: int | None = None
    last_status: str = ""
    last_run_summary: str = ""

    def apply_defaults(self) -> "AppConfig":
        """Fill runtime paths if the user has not customized them yet."""

        if not self.input_path:
            self.input_path = str(get_default_input_path())
        if not self.output_path:
            self.output_path = str(get_default_output_path())
        if self.auto_close_seconds < 1:
            self.auto_close_seconds = 60
        return self

    def geometry(self) -> str:
        """Return a Tk-compatible geometry string based on saved settings."""

        geometry = f"{self.window_width}x{self.window_height}"
        if self.window_x is not None and self.window_y is not None:
            geometry += f"+{self.window_x}+{self.window_y}"
        return geometry


class ConfigManager:
    """Load and save JSON config safely from the app runtime directory."""

    def __init__(self, config_path: Path | None = None) -> None:
        self.config_path = config_path or get_config_path()
        self._lock = Lock()

    def load(self) -> AppConfig:
        """Load config from disk or return defaults when missing/invalid."""

        if not self.config_path.exists():
            return AppConfig().apply_defaults()

        try:
            payload = json.loads(self.config_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            return AppConfig().apply_defaults()

        return AppConfig(**payload).apply_defaults()

    def save(self, config: AppConfig) -> None:
        """Persist config atomically enough for local desktop usage."""

        config.apply_defaults()
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            self.config_path.write_text(
                json.dumps(asdict(config), indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
