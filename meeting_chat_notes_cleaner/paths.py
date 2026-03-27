"""Helpers to resolve runtime paths consistently for .py and .exe usage."""

from __future__ import annotations

import sys
from pathlib import Path


def get_runtime_dir() -> Path:
    """Return the directory where config/log/data files should live."""

    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    entrypoint = Path(sys.argv[0])
    if sys.argv[0] in {"", "-", "-c"}:
        return Path(__file__).resolve().parent.parent

    return entrypoint.resolve().parent


def get_config_path() -> Path:
    """Return the config file path next to the running app."""

    return get_runtime_dir() / "config.json"


def get_log_path() -> Path:
    """Return the log file path next to the running app."""

    return get_runtime_dir() / "log.txt"


def get_default_input_path() -> Path:
    """Return the default source notes path."""

    return get_runtime_dir() / "notes.txt"


def get_default_output_path() -> Path:
    """Return the default cleaned notes path."""

    return get_runtime_dir() / "notes_clean.txt"
