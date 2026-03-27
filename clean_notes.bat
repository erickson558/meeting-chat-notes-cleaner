@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "INPUT_FILE=%SCRIPT_DIR%notes.txt"
set "OUTPUT_FILE=%SCRIPT_DIR%notes_clean.txt"
set "PYTHON_SCRIPT=%SCRIPT_DIR%meeting_chat_notes_cleaner.py"

if not exist "%PYTHON_SCRIPT%" (
    echo No se encontro "%PYTHON_SCRIPT%"
    exit /b 1
)

if not exist "%INPUT_FILE%" (
    echo No se encontro "%INPUT_FILE%"
    exit /b 1
)

where py >nul 2>nul
if not errorlevel 1 (
    py -3 "%PYTHON_SCRIPT%" --input "%INPUT_FILE%" --output "%OUTPUT_FILE%"
    if not errorlevel 1 exit /b 0
)

where python >nul 2>nul
if not errorlevel 1 (
    python "%PYTHON_SCRIPT%" --input "%INPUT_FILE%" --output "%OUTPUT_FILE%"
    if not errorlevel 1 exit /b 0
)

echo Error al ejecutar el limpiador de notas con Python
exit /b 1
