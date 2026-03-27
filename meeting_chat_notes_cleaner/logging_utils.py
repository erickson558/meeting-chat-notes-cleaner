"""Central logging setup shared by the CLI and desktop app."""

from __future__ import annotations

import logging
from pathlib import Path

from .paths import get_log_path
from .version import APP_NAME


def configure_logging(log_path: Path | None = None) -> logging.Logger:
    """Return a configured logger that writes to log.txt once."""

    target_path = log_path or get_log_path()
    target_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(APP_NAME)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not logger.handlers:
        file_handler = logging.FileHandler(target_path, encoding="utf-8")
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
        )
        logger.addHandler(file_handler)

    return logger
