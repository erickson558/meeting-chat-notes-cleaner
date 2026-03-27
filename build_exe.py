"""Build a Windows .exe for the desktop application using PyInstaller."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from meeting_chat_notes_cleaner.version import (
    APP_EXECUTABLE_NAME,
    APP_NAME,
    APP_VERSION,
    ICON_FILENAME,
)


def get_project_dir() -> Path:
    """Return the root folder of the local project."""

    return Path(__file__).resolve().parent


def get_entry_script() -> Path:
    """Return the GUI entry point used to build the desktop executable."""

    return get_project_dir() / "meeting_chat_notes_cleaner_app.py"


def get_output_executable_path() -> Path:
    """Return the final .exe path created next to the source files."""

    return get_project_dir() / f"{APP_EXECUTABLE_NAME}.exe"


def resolve_icon_path() -> Path:
    """Use the configured icon first, then fall back to any local .ico file."""

    project_dir = get_project_dir()
    preferred_icon = project_dir / ICON_FILENAME
    if preferred_icon.exists():
        return preferred_icon

    discovered_icons = sorted(project_dir.glob("*.ico"))
    if discovered_icons:
        return discovered_icons[0]

    raise FileNotFoundError("No .ico file was found in the project directory.")


def build_executable() -> Path:
    """Run PyInstaller and place the final .exe in the project root."""

    project_dir = get_project_dir()
    entry_script = get_entry_script()
    icon_path = resolve_icon_path()
    output_path = get_output_executable_path()
    build_root = project_dir / "build"
    work_path = build_root / "work"
    spec_path = build_root / "spec"

    if not entry_script.exists():
        raise FileNotFoundError(f"Entry script not found: {entry_script}")

    # Remove the previous artifact so the build result is unambiguous.
    if output_path.exists():
        output_path.unlink()

    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",
        "--name",
        APP_EXECUTABLE_NAME,
        "--icon",
        str(icon_path),
        "--distpath",
        str(project_dir),
        "--workpath",
        str(work_path),
        "--specpath",
        str(spec_path),
        str(entry_script),
    ]

    subprocess.run(command, check=True)
    if not output_path.exists():
        raise FileNotFoundError(f"Expected build artifact was not created: {output_path}")

    print(f"{APP_NAME} {APP_VERSION} built successfully.")
    print(f"Executable: {output_path}")
    return output_path


def build_argument_parser() -> argparse.ArgumentParser:
    """Expose a small CLI for build automation and GitHub Actions."""

    parser = argparse.ArgumentParser(description="Build the project .exe with PyInstaller.")
    parser.add_argument(
        "--print-output-path",
        action="store_true",
        help="Print the expected .exe path without building it.",
    )
    parser.add_argument(
        "--print-version",
        action="store_true",
        help="Print the current application version.",
    )
    return parser


def main() -> int:
    """Handle build commands used manually and by automation."""

    parser = build_argument_parser()
    args = parser.parse_args()

    if args.print_version:
        print(APP_VERSION)
        return 0

    if args.print_output_path:
        print(get_output_executable_path())
        return 0

    build_executable()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
