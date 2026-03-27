"""Regression tests for stability fixes in config, logging and GUI parsing."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from meeting_chat_notes_cleaner.config import ConfigManager
from meeting_chat_notes_cleaner.gui import sanitize_auto_close_seconds
from meeting_chat_notes_cleaner.logging_utils import close_logging, configure_logging


class ConfigManagerTests(unittest.TestCase):
    """Verify config loading stays resilient with edited JSON files."""

    def test_load_ignores_unknown_keys(self) -> None:
        """Unexpected keys should not crash application startup."""

        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            config_path.write_text(
                '{"language":"es","unexpected":123,"auto_close_seconds":"0"}',
                encoding="utf-8",
            )

            config = ConfigManager(config_path).load()

            self.assertEqual(config.language, "es")
            self.assertEqual(config.auto_close_seconds, 60)

    def test_load_handles_non_mapping_json(self) -> None:
        """A non-dict JSON payload should safely fall back to defaults."""

        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            config_path.write_text('["invalid"]', encoding="utf-8")

            config = ConfigManager(config_path).load()

            self.assertEqual(config.language, "es")
            self.assertEqual(config.auto_close_seconds, 60)


class LoggingTests(unittest.TestCase):
    """Verify logger reconfiguration honors the requested file path."""

    def test_configure_logging_switches_destination_file(self) -> None:
        """A second logger configuration should write to the new target file."""

        with tempfile.TemporaryDirectory() as temp_dir:
            log_one = Path(temp_dir) / "one.log"
            log_two = Path(temp_dir) / "two.log"

            logger_one = configure_logging(log_one)
            logger_one.info("first message")

            logger_two = configure_logging(log_two)
            logger_two.info("second message")
            close_logging(logger_two)

            self.assertTrue(log_one.exists())
            self.assertTrue(log_two.exists())
            self.assertIn("first message", log_one.read_text(encoding="utf-8"))
            self.assertNotIn("second message", log_one.read_text(encoding="utf-8"))
            self.assertIn("second message", log_two.read_text(encoding="utf-8"))


class GuiParsingTests(unittest.TestCase):
    """Verify GUI countdown parsing never raises on user-edited values."""

    def test_sanitize_auto_close_seconds_accepts_valid_values(self) -> None:
        """Valid numeric strings should keep their value."""

        self.assertEqual(sanitize_auto_close_seconds("75", fallback=60), 75)

    def test_sanitize_auto_close_seconds_rejects_invalid_values(self) -> None:
        """Blank or non-numeric strings should fall back safely."""

        self.assertEqual(sanitize_auto_close_seconds("", fallback=60), 60)
        self.assertEqual(sanitize_auto_close_seconds("abc", fallback=60), 60)
        self.assertEqual(sanitize_auto_close_seconds("-5", fallback=60), 60)


if __name__ == "__main__":
    unittest.main()
