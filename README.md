# Meeting Chat Notes Cleaner

Meeting Chat Notes Cleaner is a desktop and command-line Python application that removes chat metadata from exported class or meeting transcripts and keeps the useful study notes.

Current version: `V0.0.2`

## Features

- Desktop GUI with responsive background processing
- Command-line mode for direct automation
- Automatic `config.json` persistence next to the `.py` or `.exe`
- `log.txt` logging with timestamps and readable messages
- Configurable auto-start and auto-close workflow
- Visible status bar and auto-close countdown
- Multi-language UI support: Spanish and English
- About dialog with project version and author credits
- Windows batch launcher for quick execution
- Build automation for generating a local `.exe`
- GitHub Actions workflow for build + release automation

## Requirements

- Windows 10 or later recommended
- Python `3.12`
- Git
- GitHub CLI (`gh`) authenticated

## Installation

1. Clone the repository.
2. Create and activate a virtual environment if desired.
3. Install dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Usage

### Desktop app

```powershell
python meeting_chat_notes_cleaner_app.py
```

### Command line

```powershell
python meeting_chat_notes_cleaner.py --input notes.txt --output notes_clean.txt
```

### Batch launcher

```powershell
.\clean_notes.bat
```

## Configuration

The application stores settings automatically in `config.json` in the same folder as the running `.py` or `.exe`.

Saved settings include:

- Selected language
- Input and output file paths
- Auto-start option
- Auto-close option
- Auto-close countdown seconds
- Window size and position
- Last status and last run summary

## Logging

The application writes runtime logs to `log.txt` in the same folder as the running `.py` or `.exe`.

The log includes:

- Timestamp
- Log level
- Human-readable execution messages

The application avoids logging the note content itself.

## Build The Windows Executable

The project uses the local icon file:

`server_green_clean_energy_eco_ecology_icon_185999.ico`

Build the `.exe` with:

```powershell
python -m pip install -r requirements.txt
python build_exe.py
```

Expected result:

- A file named `MeetingChatNotesCleaner-V0.0.2.exe`
- The executable is created in the same folder as the Python source files
- The executable runs without opening an extra console window

## Versioning

This project uses the format `Vx.x.x`.

- `major`: breaking changes
- `minor`: new backward-compatible features
- `patch`: fixes, documentation improvements, workflow corrections, or safe refactors

For release consistency, the same version must be updated in:

- `meeting_chat_notes_cleaner/version.py`
- GUI title and About dialog
- `README.md`
- Git tag
- GitHub release

## GitHub Release Automation

The repository includes:

`.github/workflows/release.yml`

On every push to `main`, the workflow:

1. Installs dependencies
2. Validates the Python source
3. Builds the Windows executable
4. Reads the current app version
5. Creates the Git tag if missing
6. Creates or updates the GitHub release
7. Uploads the generated `.exe` as both a release asset and a workflow artifact

Important:

- If you push code without changing the version, the workflow updates the existing release asset for that version.
- If the commit is release-worthy, bump the version before pushing.

## Suggested Commit Convention

Use Conventional Commits:

- `feat:`
- `fix:`
- `docs:`
- `refactor:`
- `build:`
- `ci:`
- `chore:`

Example:

```text
feat: add desktop UI and automated GitHub release pipeline
```

## Project Structure

```text
.
|-- .github/
|   `-- workflows/
|       `-- release.yml
|-- meeting_chat_notes_cleaner/
|   |-- __init__.py
|   |-- cleaner.py
|   |-- config.py
|   |-- gui.py
|   |-- i18n.py
|   |-- logging_utils.py
|   |-- paths.py
|   `-- version.py
|-- build_exe.py
|-- clean_notes.bat
|-- meeting_chat_notes_cleaner.py
|-- meeting_chat_notes_cleaner_app.py
|-- requirements.txt
|-- CHANGELOG.md
|-- LICENSE
`-- README.md
```

## License

This project is distributed under the Apache License 2.0. See `LICENSE`.
