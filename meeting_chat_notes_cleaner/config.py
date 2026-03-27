"""Config model and persistence helpers for the desktop application."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from threading import Lock
from typing import Any

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
    last_status_key: str = ""
    last_status: str = ""
    last_source_line_count: int | None = None
    last_cleaned_line_count: int | None = None
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

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "AppConfig":
        """Build config safely from external JSON content.

        Unknown keys are ignored so old or future config files do not crash the
        application on startup.
        """

        allowed_keys = {item.name for item in fields(cls)}
        filtered_payload = {
            key: value for key, value in payload.items() if key in allowed_keys
        }
        config = cls(**filtered_payload)

        # Normalize numeric fields defensively in case the JSON was edited by hand.
        config.auto_close_seconds = _coerce_positive_int(
            filtered_payload.get("auto_close_seconds"),
            default=config.auto_close_seconds,
        )
        config.window_width = _coerce_positive_int(
            filtered_payload.get("window_width"),
            default=config.window_width,
        )
        config.window_height = _coerce_positive_int(
            filtered_payload.get("window_height"),
            default=config.window_height,
        )
        config.window_x = _coerce_optional_int(filtered_payload.get("window_x"))
        config.window_y = _coerce_optional_int(filtered_payload.get("window_y"))
        config.last_source_line_count = _coerce_optional_non_negative_int(
            filtered_payload.get("last_source_line_count")
        )
        config.last_cleaned_line_count = _coerce_optional_non_negative_int(
            filtered_payload.get("last_cleaned_line_count")
        )

        return config.apply_defaults()

    def geometry(self) -> str:
        """Return a Tk-compatible geometry string based on saved settings."""

        geometry = f"{self.window_width}x{self.window_height}"
        if self.window_x is not None and self.window_y is not None:
            geometry += f"+{self.window_x}+{self.window_y}"
        return geometry


def _coerce_positive_int(value: Any, default: int) -> int:
    """Return a positive integer or a safe default when parsing fails."""

    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _coerce_optional_int(value: Any) -> int | None:
    """Return an integer value or None when parsing is not possible."""

    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _coerce_optional_non_negative_int(value: Any) -> int | None:
    """Return a non-negative integer or None for invalid data."""

    if value in (None, ""):
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None


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

        if not isinstance(payload, dict):
            return AppConfig().apply_defaults()

        try:
            return AppConfig.from_dict(payload)
        except (TypeError, ValueError):
            return AppConfig().apply_defaults()

    def save(self, config: AppConfig) -> None:
        """Persist config atomically enough for local desktop usage."""

        config.apply_defaults()
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            self.config_path.write_text(
                json.dumps(asdict(config), indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
