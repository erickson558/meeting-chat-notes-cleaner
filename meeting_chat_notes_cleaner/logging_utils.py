"""Central logging setup shared by the CLI and desktop app."""

from __future__ import annotations

import logging
from pathlib import Path

from .paths import get_log_path
from .version import APP_NAME


def configure_logging(log_path: Path | None = None) -> logging.Logger:
    """Return a configured logger that writes to the requested log file.

    Reconfiguring the logger with a new path replaces old file handlers so the
    caller always gets logs in the requested destination.
    """

    target_path = log_path or get_log_path()
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path = target_path.resolve()

    logger = logging.getLogger(APP_NAME)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    active_handler: logging.FileHandler | None = None
    for handler in list(logger.handlers):
        if not isinstance(handler, logging.FileHandler):
            logger.removeHandler(handler)
            handler.close()
            continue

        current_path = Path(handler.baseFilename).resolve()
        if current_path == target_path:
            active_handler = handler
            continue

        logger.removeHandler(handler)
        handler.close()

    if active_handler is None:
        file_handler = logging.FileHandler(target_path, encoding="utf-8")
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
        )
        logger.addHandler(file_handler)

    return logger


def close_logging(logger: logging.Logger | None = None) -> None:
    """Close and detach handlers so files are released cleanly on Windows."""

    active_logger = logger or logging.getLogger(APP_NAME)
    for handler in list(active_logger.handlers):
        active_logger.removeHandler(handler)
        handler.close()
