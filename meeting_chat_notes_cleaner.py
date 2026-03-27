"""Command-line entry point for cleaning exported meeting chat notes."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from meeting_chat_notes_cleaner.cleaner import clean_notes_file
from meeting_chat_notes_cleaner.logging_utils import close_logging, configure_logging
from meeting_chat_notes_cleaner.paths import (
    get_default_input_path,
    get_default_output_path,
    get_log_path,
)
from meeting_chat_notes_cleaner.version import APP_VERSION


def build_argument_parser() -> argparse.ArgumentParser:
    """Create the CLI parser while keeping sensible local defaults."""

    parser = argparse.ArgumentParser(
        description="Clean exported chat notes and keep study-relevant content."
    )
    parser.add_argument(
        "--input",
        default=str(get_default_input_path()),
        help="Path to the source notes file. Default: notes.txt next to this script.",
    )
    parser.add_argument(
        "--output",
        default=str(get_default_output_path()),
        help="Path to the cleaned output file. Default: notes_clean.txt next to this script.",
    )
    parser.add_argument(
        "--log",
        default=str(get_log_path()),
        help="Path to the log file. Default: log.txt next to this script.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {APP_VERSION}",
    )
    return parser


def main() -> int:
    """Parse arguments, run the cleaner, and print a simple success message."""

    parser = build_argument_parser()
    args = parser.parse_args()

    input_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    log_path = Path(args.log).expanduser().resolve()

    logger = configure_logging(log_path)
    try:
        result = clean_notes_file(input_path, output_path, logger=logger)

        print(f'Archivo actualizado: "{result.output_path}"')
        print(
            f"Lineas originales: {result.source_line_count} | "
            f"Lineas limpias: {result.cleaned_line_count}"
        )
        return 0
    except FileNotFoundError:
        logger.error("Input file not found: %s", input_path)
        print(f'Error: input file not found: "{input_path}"', file=sys.stderr)
        return 1
    except Exception as exc:
        logger.exception("Unhandled CLI error")
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    finally:
        close_logging(logger)


if __name__ == "__main__":
    raise SystemExit(main())
