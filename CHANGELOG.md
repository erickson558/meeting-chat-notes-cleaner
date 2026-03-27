# Changelog

All notable changes to this project will be documented in this file.

## V0.0.3 - 2026-03-27

- Fixed CLI error handling so missing input files return a clean user-facing message instead of a Python traceback
- Fixed GUI language switching so persisted status and successful summary text are re-rendered in the active language
- Added compatibility logic for legacy configs that only stored localized summary text
- Added regression coverage for CLI failure handling and localized summary parsing

## V0.0.2 - 2026-03-27

- Fixed GUI countdown field validation so invalid edits no longer trigger Tkinter callback errors
- Fixed config loading so unknown or malformed JSON fields do not crash startup
- Fixed logger reconfiguration so custom log destinations are respected correctly
- Added regression tests for config parsing, GUI countdown parsing and logger destination handling

## V0.0.1 - 2026-03-27

- Added reusable backend cleaning logic
- Added desktop GUI with persistent configuration
- Added Spanish and English interface support
- Added local logging to `log.txt`
- Added batch launcher and CLI mode
- Added PyInstaller build script for `.exe` generation
- Added GitHub Actions workflow for automated releases
- Added repository documentation and release metadata
