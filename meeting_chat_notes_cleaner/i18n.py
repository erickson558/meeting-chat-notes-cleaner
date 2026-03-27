"""Tiny i18n layer with scalable dictionaries for future languages."""

from __future__ import annotations

from .version import APP_NAME, APP_VERSION, COPYRIGHT_YEAR, CREATED_BY


TRANSLATIONS = {
    "es": {
        "window_title": f"{APP_NAME} {APP_VERSION}",
        "header_title": APP_NAME,
        "header_subtitle": "Limpia chats exportados y conserva notas de estudio.",
        "version": f"Versión {APP_VERSION}",
        "run_summary": "Resumen de la última ejecución",
        "language": "Idioma",
        "input_file": "Archivo de entrada",
        "output_file": "Archivo de salida",
        "browse": "Buscar",
        "run": "Limpiar notas",
        "exit": "Salir",
        "auto_start": "Iniciar limpieza al abrir",
        "auto_close": "Autocerrar al terminar",
        "auto_close_seconds": "Segundos para autocierre",
        "status_ready": "Listo para limpiar notas.",
        "status_running": "Limpiando notas en segundo plano...",
        "status_success": "Limpieza completada correctamente.",
        "status_error": "Ocurrió un error durante la limpieza.",
        "input_missing": "No se encontró el archivo de entrada.",
        "summary_idle": "Aún no se ha ejecutado ninguna limpieza.",
        "summary_done": "Líneas originales: {source} | líneas limpias: {cleaned}",
        "countdown": "Cierre automático en {seconds}s",
        "select_input": "Selecciona el archivo de entrada",
        "select_output": "Selecciona el archivo de salida",
        "menu_file": "Archivo",
        "menu_help": "Ayuda",
        "menu_about": "About",
        "menu_language": "Idioma",
        "about_title": "About",
        "about_body": (
            f"{APP_NAME} {APP_VERSION}\n"
            f"Creado por {CREATED_BY}\n"
            f"{COPYRIGHT_YEAR} Derechos Reservados"
        ),
        "close": "Cerrar",
        "hint": "Atajos: Alt+L limpiar, Alt+S salir, Ctrl+E entrada, Ctrl+G salida.",
        "running_hint": "La interfaz sigue respondiendo mientras el proceso corre.",
        "last_saved": "Configuración autoguardada en config.json",
    },
    "en": {
        "window_title": f"{APP_NAME} {APP_VERSION}",
        "header_title": APP_NAME,
        "header_subtitle": "Clean exported chats and keep study-focused notes.",
        "version": f"Version {APP_VERSION}",
        "run_summary": "Last run summary",
        "language": "Language",
        "input_file": "Input file",
        "output_file": "Output file",
        "browse": "Browse",
        "run": "Clean notes",
        "exit": "Exit",
        "auto_start": "Auto-start cleaning on launch",
        "auto_close": "Auto-close when finished",
        "auto_close_seconds": "Auto-close seconds",
        "status_ready": "Ready to clean notes.",
        "status_running": "Cleaning notes in the background...",
        "status_success": "Cleaning completed successfully.",
        "status_error": "An error occurred during cleaning.",
        "input_missing": "Input file not found.",
        "summary_idle": "No cleaning run has been executed yet.",
        "summary_done": "Source lines: {source} | cleaned lines: {cleaned}",
        "countdown": "Auto-closing in {seconds}s",
        "select_input": "Select the input file",
        "select_output": "Select the output file",
        "menu_file": "File",
        "menu_help": "Help",
        "menu_about": "About",
        "menu_language": "Language",
        "about_title": "About",
        "about_body": (
            f"{APP_NAME} {APP_VERSION}\n"
            f"Created by {CREATED_BY}\n"
            f"{COPYRIGHT_YEAR} All Rights Reserved"
        ),
        "close": "Close",
        "hint": "Shortcuts: Alt+L clean, Alt+S exit, Ctrl+E input, Ctrl+G output.",
        "running_hint": "The interface stays responsive while the work runs.",
        "last_saved": "Settings auto-saved to config.json",
    },
}


def translate(language: str, key: str, **kwargs: object) -> str:
    """Return a translated UI string with optional formatting."""

    bundle = TRANSLATIONS.get(language, TRANSLATIONS["en"])
    template = bundle.get(key, key)
    if kwargs:
        return template.format(**kwargs)
    return template
