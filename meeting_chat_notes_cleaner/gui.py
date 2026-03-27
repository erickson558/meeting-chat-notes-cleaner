"""Tkinter desktop app for cleaning exported meeting chat notes."""

from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from queue import Empty, Queue
from tkinter import filedialog, ttk

from .cleaner import CleaningResult, clean_notes_file
from .config import AppConfig, ConfigManager
from .i18n import TRANSLATIONS, translate
from .logging_utils import close_logging, configure_logging
from .version import APP_NAME, APP_VERSION


def sanitize_auto_close_seconds(raw_value: str, fallback: int = 60) -> int:
    """Return a safe positive integer for the auto-close countdown.

    The GUI allows transient editing states, so blank or non-numeric values
    must not raise exceptions inside Tk callbacks.
    """

    try:
        parsed = int(str(raw_value).strip())
    except (TypeError, ValueError):
        return fallback
    return parsed if parsed > 0 else fallback


class MeetingChatNotesCleanerApp(tk.Tk):
    """Desktop application with persistent settings and a responsive UI."""

    def __init__(self) -> None:
        super().__init__()

        self.config_manager = ConfigManager()
        self.app_config = self.config_manager.load()
        self.config_manager.save(self.app_config)
        self.logger = configure_logging()
        self.logger.info("Desktop UI started. Version=%s", APP_VERSION)

        # Queue-based communication keeps Tk updates on the main thread.
        self.worker_queue: Queue[tuple[str, object]] = Queue()
        self.worker_thread: threading.Thread | None = None
        self.geometry_after_id: str | None = None
        self.auto_close_after_id: str | None = None
        self.auto_close_remaining = 0

        # Tk variables make autosave and live UI updates straightforward.
        self.language_var = tk.StringVar(value=self.app_config.language)
        self.input_var = tk.StringVar(value=self.app_config.input_path)
        self.output_var = tk.StringVar(value=self.app_config.output_path)
        self.auto_start_var = tk.BooleanVar(value=self.app_config.auto_start)
        self.auto_close_var = tk.BooleanVar(value=self.app_config.auto_close)
        self.auto_close_seconds_var = tk.StringVar(
            value=str(self.app_config.auto_close_seconds)
        )
        self.status_var = tk.StringVar()
        self.summary_var = tk.StringVar()
        self.countdown_var = tk.StringVar(value="")

        self._configure_window()
        self._build_styles()
        self._build_ui()
        self._bind_shortcuts()
        self._bind_autosave()
        self._refresh_texts()

        self.after(120, self._poll_worker_queue)
        self.protocol("WM_DELETE_WINDOW", self._handle_exit)

        if self.auto_start_var.get():
            self.after(500, self.run_cleaner)

    def _configure_window(self) -> None:
        """Apply the initial window layout and saved geometry."""

        self.title(f"{APP_NAME} {APP_VERSION}")
        self.geometry(self.app_config.geometry())
        self.minsize(940, 620)
        self.configure(bg="#F4EFE8")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.bind("<Configure>", self._on_window_configure)

    def _build_styles(self) -> None:
        """Configure a less-generic visual language using ttk styles."""

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("App.TFrame", background="#F4EFE8")
        style.configure("Card.TFrame", background="#FFFDFC")
        style.configure("Panel.TFrame", background="#16324F")
        style.configure("Muted.TLabel", background="#FFFDFC", foreground="#52606D")
        style.configure("CardTitle.TLabel", background="#FFFDFC", foreground="#102A43")
        style.configure(
            "Primary.TButton",
            background="#D97706",
            foreground="#FFFFFF",
            padding=(16, 10),
            borderwidth=0,
        )
        style.map(
            "Primary.TButton",
            background=[("active", "#B45309"), ("pressed", "#92400E")],
            foreground=[("disabled", "#F3F4F6")],
        )
        style.configure(
            "Secondary.TButton",
            background="#E5E7EB",
            foreground="#102A43",
            padding=(16, 10),
        )
        style.map(
            "Secondary.TButton",
            background=[("active", "#D1D5DB"), ("pressed", "#CBD5E1")],
        )
        style.configure("TCheckbutton", background="#FFFDFC")
        style.configure("TLabel", background="#FFFDFC", foreground="#102A43")

    def _build_ui(self) -> None:
        """Compose the full interface with header, content and status bar."""

        self._build_menu()
        self._build_header()
        self._build_main_area()
        self._build_status_bar()

    def _build_menu(self) -> None:
        """Create menu bar entries for file, language and about."""

        self.menu_bar = tk.Menu(self)
        self.file_menu = tk.Menu(self.menu_bar, tearoff=False)
        self.file_menu.add_command(
            label=self._t("exit"),
            command=self._handle_exit,
            accelerator="Alt+S",
        )
        self.menu_bar.add_cascade(label=self._t("menu_file"), menu=self.file_menu)

        self.language_menu = tk.Menu(self.menu_bar, tearoff=False)
        self.language_menu.add_radiobutton(
            label="Español",
            value="es",
            variable=self.language_var,
            command=self._language_changed,
        )
        self.language_menu.add_radiobutton(
            label="English",
            value="en",
            variable=self.language_var,
            command=self._language_changed,
        )
        self.menu_bar.add_cascade(label=self._t("menu_language"), menu=self.language_menu)

        self.help_menu = tk.Menu(self.menu_bar, tearoff=False)
        self.help_menu.add_command(
            label=self._t("menu_about"),
            command=self._open_about_dialog,
        )
        self.menu_bar.add_cascade(label=self._t("menu_help"), menu=self.help_menu)

        self.config(menu=self.menu_bar)

    def _build_header(self) -> None:
        """Create the branded top strip with version and context."""

        header = tk.Frame(self, bg="#16324F", padx=24, pady=18)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        self.header_title_label = tk.Label(
            header,
            bg="#16324F",
            fg="#FFF7ED",
            font=("Segoe UI Semibold", 22),
        )
        self.header_title_label.grid(row=0, column=0, sticky="w")

        self.header_subtitle_label = tk.Label(
            header,
            bg="#16324F",
            fg="#D9E2EC",
            font=("Segoe UI", 10),
        )
        self.header_subtitle_label.grid(row=1, column=0, sticky="w", pady=(4, 0))

        self.header_version_label = tk.Label(
            header,
            bg="#16324F",
            fg="#F0B429",
            font=("Segoe UI Semibold", 10),
        )
        self.header_version_label.grid(row=0, column=1, sticky="e")

    def _build_main_area(self) -> None:
        """Build the two-column content area with an info rail and form card."""

        main = ttk.Frame(self, style="App.TFrame", padding=20)
        main.grid(row=1, column=0, sticky="nsew")
        main.grid_columnconfigure(0, weight=0)
        main.grid_columnconfigure(1, weight=1)
        main.grid_rowconfigure(0, weight=1)

        info_panel = tk.Frame(main, bg="#1F4A6A", width=260, padx=18, pady=22)
        info_panel.grid(row=0, column=0, sticky="nsw", padx=(0, 18))
        info_panel.grid_propagate(False)

        self.info_title_label = tk.Label(
            info_panel,
            bg="#1F4A6A",
            fg="#FFF7ED",
            font=("Segoe UI Semibold", 16),
            anchor="w",
            justify="left",
        )
        self.info_title_label.pack(fill="x")

        self.info_hint_label = tk.Label(
            info_panel,
            bg="#1F4A6A",
            fg="#D9E2EC",
            font=("Segoe UI", 10),
            wraplength=220,
            justify="left",
            anchor="nw",
        )
        self.info_hint_label.pack(fill="x", pady=(14, 8))

        self.info_running_label = tk.Label(
            info_panel,
            bg="#1F4A6A",
            fg="#9FB3C8",
            font=("Segoe UI", 10),
            wraplength=220,
            justify="left",
            anchor="nw",
        )
        self.info_running_label.pack(fill="x")

        card = ttk.Frame(main, style="Card.TFrame", padding=22)
        card.grid(row=0, column=1, sticky="nsew")
        card.grid_columnconfigure(1, weight=1)

        self.language_label = ttk.Label(card, style="CardTitle.TLabel")
        self.language_label.grid(row=0, column=0, sticky="w", pady=(0, 8))

        self.language_combo = ttk.Combobox(
            card,
            state="readonly",
            values=[f"Español (es)", f"English (en)"],
            width=24,
        )
        self.language_combo.grid(row=0, column=1, sticky="w", pady=(0, 8))
        self.language_combo.bind("<<ComboboxSelected>>", self._on_language_combo_change)

        self.input_label = ttk.Label(card)
        self.input_label.grid(row=1, column=0, sticky="w", pady=(8, 8))

        self.input_entry = ttk.Entry(card, textvariable=self.input_var)
        self.input_entry.grid(row=1, column=1, sticky="ew", padx=(0, 10), pady=(8, 8))

        self.input_button = ttk.Button(card, command=self._browse_input)
        self.input_button.grid(row=1, column=2, sticky="ew", pady=(8, 8))

        self.output_label = ttk.Label(card)
        self.output_label.grid(row=2, column=0, sticky="w", pady=(8, 8))

        self.output_entry = ttk.Entry(card, textvariable=self.output_var)
        self.output_entry.grid(row=2, column=1, sticky="ew", padx=(0, 10), pady=(8, 8))

        self.output_button = ttk.Button(card, command=self._browse_output)
        self.output_button.grid(row=2, column=2, sticky="ew", pady=(8, 8))

        options_frame = ttk.Frame(card, style="Card.TFrame")
        options_frame.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(14, 12))
        options_frame.grid_columnconfigure(1, weight=1)

        self.auto_start_check = ttk.Checkbutton(
            options_frame,
            variable=self.auto_start_var,
        )
        self.auto_start_check.grid(row=0, column=0, sticky="w", padx=(0, 18))

        self.auto_close_check = ttk.Checkbutton(
            options_frame,
            variable=self.auto_close_var,
        )
        self.auto_close_check.grid(row=0, column=1, sticky="w", padx=(0, 18))

        self.auto_close_seconds_label = ttk.Label(options_frame)
        self.auto_close_seconds_label.grid(row=1, column=0, sticky="w", pady=(14, 0))

        self.auto_close_seconds_spin = ttk.Spinbox(
            options_frame,
            from_=1,
            to=3600,
            width=10,
            textvariable=self.auto_close_seconds_var,
            validate="key",
            validatecommand=(self.register(self._validate_auto_close_seconds), "%P"),
        )
        self.auto_close_seconds_spin.grid(row=1, column=1, sticky="w", pady=(14, 0))
        self.auto_close_seconds_spin.bind(
            "<FocusOut>",
            lambda _event: self._normalize_auto_close_seconds_field(),
        )

        actions_frame = ttk.Frame(card, style="Card.TFrame")
        actions_frame.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(20, 8))
        actions_frame.grid_columnconfigure(0, weight=0)
        actions_frame.grid_columnconfigure(1, weight=0)
        actions_frame.grid_columnconfigure(2, weight=1)

        self.run_button = ttk.Button(
            actions_frame,
            command=self.run_cleaner,
            style="Primary.TButton",
        )
        self.run_button.grid(row=0, column=0, sticky="w", padx=(0, 10))

        self.exit_button = ttk.Button(
            actions_frame,
            command=self._handle_exit,
            style="Secondary.TButton",
        )
        self.exit_button.grid(row=0, column=1, sticky="w")

        self.summary_title_label = ttk.Label(card, style="CardTitle.TLabel")
        self.summary_title_label.grid(row=5, column=0, columnspan=3, sticky="w", pady=(18, 6))

        self.summary_value_label = ttk.Label(
            card,
            textvariable=self.summary_var,
            style="Muted.TLabel",
            wraplength=640,
            justify="left",
        )
        self.summary_value_label.grid(row=6, column=0, columnspan=3, sticky="ew")

    def _build_status_bar(self) -> None:
        """Create the persistent bottom status bar and countdown area."""

        status_bar = tk.Frame(self, bg="#102A43", padx=16, pady=10)
        status_bar.grid(row=2, column=0, sticky="ew")
        status_bar.grid_columnconfigure(0, weight=1)

        self.status_label = tk.Label(
            status_bar,
            textvariable=self.status_var,
            bg="#102A43",
            fg="#F0F4F8",
            anchor="w",
            font=("Segoe UI", 10),
        )
        self.status_label.grid(row=0, column=0, sticky="w")

        self.countdown_label = tk.Label(
            status_bar,
            textvariable=self.countdown_var,
            bg="#102A43",
            fg="#F0B429",
            anchor="e",
            font=("Segoe UI Semibold", 10),
        )
        self.countdown_label.grid(row=0, column=1, sticky="e")

    def _bind_shortcuts(self) -> None:
        """Register keyboard shortcuts aligned with common Windows patterns."""

        self.bind_all("<Alt-l>", lambda _event: self.run_cleaner())
        self.bind_all("<Alt-s>", lambda _event: self._handle_exit())
        self.bind_all("<Control-e>", lambda _event: self._browse_input())
        self.bind_all("<Control-g>", lambda _event: self._browse_output())

    def _bind_autosave(self) -> None:
        """Persist settings whenever the user changes a tracked field."""

        self.language_var.trace_add("write", lambda *_: self._language_changed())
        self.input_var.trace_add("write", lambda *_: self._sync_config_from_vars())
        self.output_var.trace_add("write", lambda *_: self._sync_config_from_vars())
        self.auto_start_var.trace_add("write", lambda *_: self._sync_config_from_vars())
        self.auto_close_var.trace_add("write", lambda *_: self._sync_config_from_vars())
        self.auto_close_seconds_var.trace_add(
            "write", lambda *_: self._sync_config_from_vars()
        )

    def _refresh_texts(self) -> None:
        """Update every visible label based on the selected language."""

        language = self.language_var.get()
        self.title(self._t("window_title"))

        self.header_title_label.config(text=self._t("header_title"))
        self.header_subtitle_label.config(text=self._t("header_subtitle"))
        self.header_version_label.config(text=self._t("version"))

        self.info_title_label.config(text=self._t("header_title"))
        self.info_hint_label.config(text=self._t("hint"))
        self.info_running_label.config(text=self._t("running_hint"))

        self.language_label.config(text=self._t("language"))
        self.input_label.config(text=self._t("input_file"))
        self.output_label.config(text=self._t("output_file"))
        self.input_button.config(text=self._t("browse"))
        self.output_button.config(text=self._t("browse"))
        self.auto_start_check.config(text=self._t("auto_start"))
        self.auto_close_check.config(text=self._t("auto_close"))
        self.auto_close_seconds_label.config(text=self._t("auto_close_seconds"))
        self.run_button.config(text=self._t("run"))
        self.exit_button.config(text=self._t("exit"))
        self.summary_title_label.config(text=self._t("run_summary"))

        if not self.status_var.get():
            self.status_var.set(self._t("status_ready"))
        if self.app_config.last_run_summary:
            self.summary_var.set(self.app_config.last_run_summary)
        elif not self.summary_var.get():
            self.summary_var.set(self._t("summary_idle"))

        self._build_menu()

        if language == "es":
            self.language_combo.set("Español (es)")
        else:
            self.language_combo.set("English (en)")

    def _t(self, key: str, **kwargs: object) -> str:
        """Read translated text for the current language."""

        return translate(self.language_var.get(), key, **kwargs)

    def _on_language_combo_change(self, _event: object) -> None:
        """Map combobox labels back to language codes."""

        selected = self.language_combo.get()
        if selected.endswith("(es)"):
            self.language_var.set("es")
        else:
            self.language_var.set("en")

    def _language_changed(self) -> None:
        """Refresh the UI after a language change and save it immediately."""

        if self.language_var.get() not in TRANSLATIONS:
            self.language_var.set("en")
        self._sync_config_from_vars()
        self._refresh_texts()

    def _sync_config_from_vars(self) -> None:
        """Push the current Tk variable values into the in-memory config."""

        seconds = sanitize_auto_close_seconds(
            self.auto_close_seconds_var.get(),
            fallback=self.app_config.auto_close_seconds,
        )

        self.app_config.language = self.language_var.get()
        self.app_config.input_path = self.input_var.get().strip()
        self.app_config.output_path = self.output_var.get().strip()
        self.app_config.auto_start = bool(self.auto_start_var.get())
        self.app_config.auto_close = bool(self.auto_close_var.get())
        self.app_config.auto_close_seconds = seconds
        self.config_manager.save(self.app_config)
        self.logger.info("Settings saved to config.json")

    def _validate_auto_close_seconds(self, proposed_value: str) -> bool:
        """Allow only digits or a temporary blank value while editing."""

        return proposed_value == "" or proposed_value.isdigit()

    def _normalize_auto_close_seconds_field(self) -> None:
        """Rewrite the field with a safe value after user editing finishes."""

        normalized = sanitize_auto_close_seconds(
            self.auto_close_seconds_var.get(),
            fallback=self.app_config.auto_close_seconds,
        )
        self.auto_close_seconds_var.set(str(normalized))

    def _browse_input(self) -> None:
        """Open a file picker for the source notes file."""

        initial_path = Path(self.input_var.get()).expanduser()
        filename = filedialog.askopenfilename(
            title=self._t("select_input"),
            initialdir=str(initial_path.parent if initial_path.parent.exists() else Path.cwd()),
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if filename:
            self.input_var.set(filename)

    def _browse_output(self) -> None:
        """Open a save dialog for the cleaned notes destination."""

        initial_path = Path(self.output_var.get()).expanduser()
        filename = filedialog.asksaveasfilename(
            title=self._t("select_output"),
            initialdir=str(initial_path.parent if initial_path.parent.exists() else Path.cwd()),
            initialfile=initial_path.name or "notes_clean.txt",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if filename:
            self.output_var.set(filename)

    def run_cleaner(self) -> None:
        """Start the cleaner in a worker thread so the UI stays responsive."""

        if self.worker_thread and self.worker_thread.is_alive():
            return

        self._normalize_auto_close_seconds_field()
        input_path = Path(self.input_var.get().strip()).expanduser()
        output_path = Path(self.output_var.get().strip()).expanduser()

        if not input_path.exists():
            self.status_var.set(self._t("status_error"))
            self.summary_var.set(f"{self._t('input_missing')} {input_path}")
            self.logger.warning("Input file not found: %s", input_path)
            return

        self._cancel_auto_close()
        self.countdown_var.set("")
        self.status_var.set(self._t("status_running"))
        self.summary_var.set(self._t("running_hint"))
        self.run_button.state(["disabled"])

        self.worker_thread = threading.Thread(
            target=self._run_cleaner_worker,
            args=(input_path, output_path),
            daemon=True,
        )
        self.worker_thread.start()

    def _run_cleaner_worker(self, input_path: Path, output_path: Path) -> None:
        """Execute the file cleaning off the Tk main loop."""

        try:
            result = clean_notes_file(input_path, output_path, logger=self.logger)
            self.worker_queue.put(("success", result))
        except Exception as exc:  # pragma: no cover - defensive UI path
            self.logger.exception("Cleaning failed")
            self.worker_queue.put(("error", exc))

    def _poll_worker_queue(self) -> None:
        """Receive worker results and safely update Tk widgets."""

        try:
            while True:
                state, payload = self.worker_queue.get_nowait()
                if state == "success":
                    self._handle_clean_success(payload)  # type: ignore[arg-type]
                else:
                    self._handle_clean_error(payload)  # type: ignore[arg-type]
        except Empty:
            pass
        finally:
            self.after(120, self._poll_worker_queue)

    def _handle_clean_success(self, result: CleaningResult) -> None:
        """Render a successful run in the GUI and optionally auto-close."""

        self.run_button.state(["!disabled"])
        self.status_var.set(self._t("status_success"))
        self.summary_var.set(
            self._t(
                "summary_done",
                source=result.source_line_count,
                cleaned=result.cleaned_line_count,
            )
        )

        self.app_config.last_status = self.status_var.get()
        self.app_config.last_run_summary = self.summary_var.get()
        self.config_manager.save(self.app_config)

        if self.auto_close_var.get():
            self._start_auto_close_countdown()

    def _handle_clean_error(self, error: Exception) -> None:
        """Render a failed run without interruptive message boxes."""

        self.run_button.state(["!disabled"])
        self.status_var.set(self._t("status_error"))
        self.summary_var.set(str(error))
        self.app_config.last_status = self.status_var.get()
        self.app_config.last_run_summary = self.summary_var.get()
        self.config_manager.save(self.app_config)

    def _start_auto_close_countdown(self) -> None:
        """Start a visible countdown in the status bar before closing."""

        self._normalize_auto_close_seconds_field()
        self.auto_close_remaining = sanitize_auto_close_seconds(
            self.auto_close_seconds_var.get(),
            fallback=self.app_config.auto_close_seconds,
        )
        self._tick_auto_close()

    def _tick_auto_close(self) -> None:
        """Update the countdown once per second and exit when it reaches zero."""

        self.countdown_var.set(
            self._t("countdown", seconds=self.auto_close_remaining)
        )
        if self.auto_close_remaining <= 0:
            self.destroy()
            return

        self.auto_close_remaining -= 1
        self.auto_close_after_id = self.after(1000, self._tick_auto_close)

    def _cancel_auto_close(self) -> None:
        """Cancel any pending auto-close countdown before a new run."""

        if self.auto_close_after_id:
            self.after_cancel(self.auto_close_after_id)
            self.auto_close_after_id = None
        self.countdown_var.set("")

    def _on_window_configure(self, event: tk.Event[tk.Misc]) -> None:
        """Debounce geometry writes so config autosave stays cheap."""

        if event.widget is not self:
            return
        if self.geometry_after_id:
            self.after_cancel(self.geometry_after_id)
        self.geometry_after_id = self.after(250, self._save_geometry)

    def _save_geometry(self) -> None:
        """Persist window size and position to config.json."""

        self.app_config.window_width = self.winfo_width()
        self.app_config.window_height = self.winfo_height()
        self.app_config.window_x = self.winfo_x()
        self.app_config.window_y = self.winfo_y()
        self.config_manager.save(self.app_config)

    def _open_about_dialog(self) -> None:
        """Show a lightweight About dialog without using messagebox."""

        dialog = tk.Toplevel(self)
        dialog.title(self._t("about_title"))
        dialog.transient(self)
        dialog.resizable(False, False)
        dialog.configure(bg="#FFFDFC")
        dialog.geometry(f"360x180+{self.winfo_x() + 80}+{self.winfo_y() + 80}")

        body = tk.Label(
            dialog,
            text=self._t("about_body"),
            bg="#FFFDFC",
            fg="#102A43",
            justify="center",
            font=("Segoe UI", 11),
            padx=24,
            pady=28,
        )
        body.pack(fill="both", expand=True)

        close_button = ttk.Button(dialog, text=self._t("close"), command=dialog.destroy)
        close_button.pack(pady=(0, 18))

        dialog.grab_set()

    def _handle_exit(self) -> None:
        """Save final geometry and close the application cleanly."""

        self._cancel_auto_close()
        self._save_geometry()
        close_logging(self.logger)
        self.destroy()


def run_desktop_app() -> int:
    """Launch the desktop application main loop."""

    app = MeetingChatNotesCleanerApp()
    app.mainloop()
    return 0
