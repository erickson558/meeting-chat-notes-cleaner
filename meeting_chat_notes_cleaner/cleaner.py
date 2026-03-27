"""Backend note-cleaning logic shared by the CLI and the GUI."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class CleaningResult:
    """Small immutable summary used by the GUI and CLI after each run."""

    input_path: Path
    output_path: Path
    source_line_count: int
    cleaned_line_count: int


class MeetingChatNotesCleaner:
    """Stateful cleaner that removes chat metadata while keeping note content."""

    SPEAKER_HEADER_PATTERN = re.compile(
        r"^(?P<name>[\wÀ-ÿ][\wÀ-ÿ .'-]*?)\s+\d{1,2}:\d{2}\s?[AP]M(?:\s+\(Edited\))?\s*$",
        re.UNICODE,
    )
    DATE_HEADER_PATTERN = re.compile(
        r"^(Today|Yesterday|Hoy|Ayer|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2}|[A-Za-z]{3,9}\s+\d{1,2},\s+\d{4})\s*$"
    )
    TIME_ONLY_PATTERN = re.compile(r"^\d{1,2}:\d{2}\s?[AP]M\s*$")
    SYSTEM_MESSAGE_PATTERN = re.compile(
        r'^Messages addressed to "meeting group chat".*$'
    )
    SEPARATOR_PATTERN = re.compile(r"^\s*[-*]{3,}\s*$")
    NOISE_PATTERN = re.compile(r"^\s*(\d{5,}|-\d+)\s*$")
    INLINE_NOISE_PATTERNS = (
        re.compile(r"^(coach you got frozen)\s*$", re.IGNORECASE),
    )

    def __init__(self) -> None:
        self.current_speaker_type = "standalone"

    def clean_lines(self, lines: Iterable[str]) -> list[str]:
        """Run the cleanup rules and return the cleaned content."""

        cleaned: list[str] = []

        for raw_line in lines:
            trimmed = raw_line.strip()

            header_match = self.SPEAKER_HEADER_PATTERN.match(trimmed)
            if header_match:
                speaker_name = header_match.group("name").strip()
                if re.match(r"^coach\b", speaker_name, re.IGNORECASE):
                    self.current_speaker_type = "coach"
                else:
                    self.current_speaker_type = "other"
                continue

            if self._is_global_noise(trimmed):
                continue

            if not trimmed:
                self.current_speaker_type = "standalone"
                if cleaned and cleaned[-1] != "":
                    cleaned.append("")
                continue

            if self.current_speaker_type == "other":
                continue

            if self._is_inline_noise(trimmed):
                continue

            cleaned.append(raw_line.rstrip())

        return self._trim_blank_edges(cleaned)

    def _is_global_noise(self, line: str) -> bool:
        """Check if the line is a chat artifact instead of a useful note."""

        return any(
            (
                self.DATE_HEADER_PATTERN.match(line),
                self.TIME_ONLY_PATTERN.match(line),
                self.SYSTEM_MESSAGE_PATTERN.match(line),
                self.SEPARATOR_PATTERN.match(line),
                self.NOISE_PATTERN.match(line),
            )
        )

    def _is_inline_noise(self, line: str) -> bool:
        """Apply narrow rules for leftover one-off noisy lines."""

        return any(pattern.match(line) for pattern in self.INLINE_NOISE_PATTERNS)

    @staticmethod
    def _trim_blank_edges(lines: list[str]) -> list[str]:
        """Remove leading and trailing blank lines from the cleaned result."""

        start = 0
        end = len(lines)

        while start < end and lines[start] == "":
            start += 1

        while end > start and lines[end - 1] == "":
            end -= 1

        return lines[start:end]


def read_text_lines(file_path: Path, logger: logging.Logger | None = None) -> list[str]:
    """Read text with a UTF-8 first strategy and a legacy fallback."""

    try:
        return file_path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        if logger:
            logger.warning("UTF-8 decode failed, falling back to latin-1: %s", file_path)
        return file_path.read_text(encoding="latin-1").splitlines()


def write_text_lines(file_path: Path, lines: Iterable[str]) -> None:
    """Write cleaned lines in UTF-8 and end the file with a newline."""

    file_path.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join(lines)
    if content:
        content += "\n"
    file_path.write_text(content, encoding="utf-8")


def clean_notes_file(
    input_path: Path,
    output_path: Path,
    logger: logging.Logger | None = None,
) -> CleaningResult:
    """Clean one source file and persist the resulting output file."""

    if logger:
        logger.info("Cleaning started. Input=%s Output=%s", input_path, output_path)

    source_lines = read_text_lines(input_path, logger=logger)
    cleaner = MeetingChatNotesCleaner()
    cleaned_lines = cleaner.clean_lines(source_lines)
    write_text_lines(output_path, cleaned_lines)

    result = CleaningResult(
        input_path=input_path,
        output_path=output_path,
        source_line_count=len(source_lines),
        cleaned_line_count=len(cleaned_lines),
    )

    if logger:
        logger.info(
            "Cleaning completed. Source lines=%s Cleaned lines=%s",
            result.source_line_count,
            result.cleaned_line_count,
        )

    return result
