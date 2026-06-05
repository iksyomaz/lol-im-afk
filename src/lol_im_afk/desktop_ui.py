from __future__ import annotations

import os
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk
from typing import Callable

import sv_ttk

from lol_im_afk.config import AppConfig, lockfile_paths_from_setting
from lol_im_afk.events import AppEvent, EventKind
from lol_im_afk.icon_theme import ICON_THEMES, icon_theme_key_from_label, icon_theme_label_from_key
from lol_im_afk.sound import SOUND_CUES, SoundPlayer
from lol_im_afk.status import StatusStore
from lol_im_afk.user_settings import SettingsStore
from lol_im_afk.windows_startup import set_start_with_windows
from lol_im_afk.worker import AutoAcceptWorker


class DesktopUi:
    def __init__(
        self,
        config: AppConfig,
        settings_store: SettingsStore,
        worker: AutoAcceptWorker,
        status_store: StatusStore,
    ) -> None:
        self._config = config
        self._settings_store = settings_store
        self._worker = worker
        self._status_store = status_store
        self._tasks: queue.Queue[Callable[[], None]] = queue.Queue()
        self._ready = threading.Event()
        self._thread = threading.Thread(target=self._run, name="lol-im-afk-ui", daemon=True)
        self._root: tk.Tk | None = None
        self._settings_window: tk.Toplevel | None = None
        self._popups: list[tk.Toplevel] = []
        self._icon_theme_changed_callback: Callable[[], None] | None = None
        self._sound_player = SoundPlayer(
            sound_dir=self._config.log_file.parent / "sounds",
            enabled=self._settings_store.settings.sound_enabled,
            volume_percent=self._settings_store.settings.sound_volume_percent,
        )
        self._thread.start()
        self._ready.wait(timeout=5)

    def notify(self, event: AppEvent) -> None:
        self._post(lambda: self._show_popup(event))

    def open_settings(self) -> None:
        self._post(self._open_settings)

    def set_icon_theme_changed_callback(self, callback: Callable[[], None]) -> None:
        self._icon_theme_changed_callback = callback

    def stop(self) -> None:
        self._post(self._stop)
        self._thread.join(timeout=3)

    def _post(self, task: Callable[[], None]) -> None:
        self._tasks.put(task)

    def _run(self) -> None:
        root = tk.Tk()
        sv_ttk.set_theme(self._settings_store.settings.ui_theme)
        root.withdraw()
        self._root = root
        self._ready.set()
        root.after(50, self._drain_tasks)
        root.mainloop()

    def _drain_tasks(self) -> None:
        while True:
            try:
                task = self._tasks.get_nowait()
            except queue.Empty:
                break
            task()

        if self._root is not None:
            self._root.after(50, self._drain_tasks)

    def _stop(self) -> None:
        if self._root is not None:
            root = self._root
            self._root = None
            root.destroy()

    def _show_popup(self, event: AppEvent) -> None:
        if self._root is None:
            return

        self._sound_player.play_for_event(event)

        popup = tk.Toplevel(self._root)
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)
        popup.attributes("-toolwindow", True)
        popup.resizable(False, False)
        popup.configure(bg="#111827")

        frame = tk.Frame(popup, bg="#111827", padx=14, pady=10)
        frame.grid(row=0, column=0, sticky="nsew")
        tk.Label(
            frame,
            text="lol-im-afk",
            font=("Segoe UI", 10, "bold"),
            bg="#111827",
            fg="#ffffff",
        ).grid(row=0, column=0, sticky="w")
        tk.Label(
            frame,
            text=event.display_text,
            wraplength=280,
            justify="left",
            bg="#111827",
            fg="#dbeafe",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(4, 0))
        tk.Button(
            frame,
            text="x",
            command=lambda: self._close_popup(popup),
            bg="#111827",
            fg="#9ca3af",
            activebackground="#1f2937",
            activeforeground="#ffffff",
            bd=0,
            padx=4,
            pady=0,
        ).grid(row=0, column=1, sticky="ne")
        frame.columnconfigure(0, weight=1)

        popup.update_idletasks()
        width = max(320, popup.winfo_width())
        height = max(86, popup.winfo_height())
        x = popup.winfo_screenwidth() - width - 20
        y = popup.winfo_screenheight() - height - 52 - (len(self._popups) * (height + 8))
        popup.geometry(f"{width}x{height}+{x}+{max(20, y)}")
        popup.grid_columnconfigure(0, weight=1)
        frame.configure(width=width - 2)
        popup.lift()

        self._popups.append(popup)
        popup.after(5000, lambda: self._close_popup(popup))

    def _close_popup(self, popup: tk.Toplevel) -> None:
        if popup in self._popups:
            self._popups.remove(popup)
        try:
            popup.destroy()
        except tk.TclError:
            pass

    def _open_settings(self) -> None:
        if self._root is None:
            return

        if self._settings_window is not None and self._settings_window.winfo_exists():
            self._settings_window.lift()
            self._settings_window.focus_force()
            return

        window = tk.Toplevel(self._root)
        self._settings_window = window
        window.title("lol-im-afk settings")
        window.geometry("780x640")
        window.minsize(700, 560)

        settings = self._settings_store.settings
        lockfile_var = tk.StringVar(value=settings.lockfile_path or "")
        delay_min_var = tk.StringVar(value=str(settings.delay_min_seconds))
        delay_max_var = tk.StringVar(value=str(settings.delay_max_seconds))
        sound_enabled_var = tk.BooleanVar(value=settings.sound_enabled)
        sound_volume_var = tk.IntVar(value=settings.sound_volume_percent)
        preview_cue_var = tk.StringVar(value=SOUND_CUES[0].label)
        icon_theme_var = tk.StringVar(value=icon_theme_label_from_key(settings.icon_theme))
        ui_theme_var = tk.StringVar(value=settings.ui_theme.title())
        start_with_windows_var = tk.BooleanVar(value=settings.start_with_windows)
        status_var = tk.StringVar(value=self._status_store.snapshot().text)

        main = ttk.Frame(window, padding=16)
        main.pack(fill="both", expand=True)

        header = ttk.Frame(main)
        header.grid(row=0, column=0, sticky="ew")
        ttk.Label(header, text="lol-im-afk", font=("Segoe UI", 16, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(header, textvariable=status_var).grid(row=1, column=0, sticky="w", pady=(2, 0))
        ttk.Button(header, text="Test connection", command=self._test_connection).grid(row=0, column=1, rowspan=2, sticky="e")
        header.columnconfigure(0, weight=1)

        def refresh_status() -> None:
            if not window.winfo_exists():
                return
            status_var.set(self._status_store.snapshot().text)
            window.after(1000, refresh_status)

        window.after(1000, refresh_status)

        notebook = ttk.Notebook(main)
        notebook.grid(row=1, column=0, sticky="nsew", pady=(14, 0))

        general_tab = ttk.Frame(notebook, padding=14)
        appearance_tab = ttk.Frame(notebook, padding=14)
        sounds_tab = ttk.Frame(notebook, padding=14)
        logs_tab = ttk.Frame(notebook, padding=14)
        notebook.add(general_tab, text="General")
        notebook.add(appearance_tab, text="Appearance")
        notebook.add(sounds_tab, text="Sounds")
        notebook.add(logs_tab, text="Logs")

        timing_frame = ttk.LabelFrame(general_tab, text="Auto-accept timing", padding=12)
        timing_frame.grid(row=0, column=0, sticky="ew")
        ttk.Label(timing_frame, text="Delay min").grid(row=0, column=0, sticky="w")
        ttk.Entry(timing_frame, textvariable=delay_min_var, width=10).grid(row=0, column=1, sticky="w", padx=(10, 24))
        ttk.Label(timing_frame, text="Delay max").grid(row=0, column=2, sticky="w")
        ttk.Entry(timing_frame, textvariable=delay_max_var, width=10).grid(row=0, column=3, sticky="w", padx=(10, 0))

        lockfile_frame = ttk.LabelFrame(general_tab, text="League client", padding=12)
        lockfile_frame.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        ttk.Label(lockfile_frame, text="Lockfile").grid(row=0, column=0, sticky="w")
        ttk.Entry(lockfile_frame, textvariable=lockfile_var).grid(row=0, column=1, sticky="ew", padx=(10, 8))
        ttk.Button(lockfile_frame, text="Browse file", command=lambda: self._browse_lockfile(lockfile_var)).grid(row=0, column=2)
        ttk.Button(lockfile_frame, text="Browse folder", command=lambda: self._browse_lockfile_dir(lockfile_var)).grid(row=0, column=3, padx=(8, 0))
        lockfile_frame.columnconfigure(1, weight=1)

        startup_frame = ttk.LabelFrame(general_tab, text="Startup", padding=12)
        startup_frame.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        ttk.Checkbutton(
            startup_frame,
            text="Start with Windows",
            variable=start_with_windows_var,
        ).grid(row=0, column=0, sticky="w")

        general_tab.columnconfigure(0, weight=1)

        theme_frame = ttk.LabelFrame(appearance_tab, text="Theme", padding=12)
        theme_frame.grid(row=0, column=0, sticky="ew")
        ttk.Label(theme_frame, text="Settings UI").grid(row=0, column=0, sticky="w")
        ttk.Combobox(
            theme_frame,
            textvariable=ui_theme_var,
            values=("Dark", "Light"),
            state="readonly",
            width=14,
        ).grid(row=0, column=1, sticky="w", padx=(10, 0))

        icon_frame = ttk.LabelFrame(appearance_tab, text="Tray icon", padding=12)
        icon_frame.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        ttk.Label(icon_frame, text="Icon set").grid(row=0, column=0, sticky="w")
        icon_theme_combo = ttk.Combobox(
            icon_frame,
            textvariable=icon_theme_var,
            values=[theme.label for theme in ICON_THEMES],
            state="readonly",
        )
        icon_theme_combo.grid(row=0, column=1, sticky="ew", padx=(10, 0))
        icon_frame.columnconfigure(1, weight=1)
        appearance_tab.columnconfigure(0, weight=1)

        ttk.Label(sounds_tab, text="Sound volume").grid(row=0, column=0, sticky="w")
        sound_volume = ttk.Scale(sounds_tab, from_=0, to=100, variable=sound_volume_var, orient="horizontal")
        sound_volume.grid(row=0, column=1, sticky="ew", padx=(10, 8))
        volume_label = ttk.Label(sounds_tab, text=f"{sound_volume_var.get()}%")
        volume_label.grid(row=0, column=2, sticky="w")
        sound_volume.configure(command=lambda _: volume_label.configure(text=f"{sound_volume_var.get()}%"))

        ttk.Checkbutton(sounds_tab, text="Play sound", variable=sound_enabled_var).grid(row=1, column=1, sticky="w", pady=(12, 0))
        ttk.Label(sounds_tab, text="Preview cue").grid(row=2, column=0, sticky="w", pady=(12, 0))
        cue_labels = [cue.label for cue in SOUND_CUES]
        cue_combo = ttk.Combobox(sounds_tab, textvariable=preview_cue_var, values=cue_labels, state="readonly")
        cue_combo.grid(row=2, column=1, sticky="ew", padx=(10, 8), pady=(12, 0))
        ttk.Button(
            sounds_tab,
            text="Preview",
            command=lambda: self._preview_sound(preview_cue_var.get(), sound_volume_var.get()),
        ).grid(row=2, column=2, sticky="w", pady=(12, 0))
        sounds_tab.columnconfigure(1, weight=1)

        log_toolbar = ttk.Frame(logs_tab)
        log_toolbar.grid(row=0, column=0, sticky="ew")
        ttk.Button(log_toolbar, text="Test notification", command=self._test_notification).pack(side="left")
        ttk.Button(log_toolbar, text="Open log file", command=self._open_log_file).pack(side="left", padx=(8, 0))
        ttk.Button(log_toolbar, text="Refresh logs", command=lambda: self._load_logs(log_text)).pack(side="left", padx=(8, 0))
        log_text = scrolledtext.ScrolledText(logs_tab, height=16, wrap="word", borderwidth=0, relief="flat")
        log_text.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        self._style_log_text(log_text)
        self._load_logs(log_text)
        logs_tab.columnconfigure(0, weight=1)
        logs_tab.rowconfigure(1, weight=1)

        button_row = ttk.Frame(main)
        button_row.grid(row=2, column=0, sticky="ew", pady=(14, 0))
        ttk.Button(
            button_row,
            text="Apply",
            command=lambda: self._apply_settings(
                lockfile_var.get(),
                delay_min_var.get(),
                delay_max_var.get(),
                sound_enabled_var.get(),
                sound_volume_var.get(),
                icon_theme_var.get(),
                ui_theme_var.get(),
                start_with_windows_var.get(),
            ),
        ).pack(side="left")
        ttk.Button(button_row, text="Close", command=window.destroy).pack(side="right")

        main.columnconfigure(0, weight=1)
        main.rowconfigure(1, weight=1)
        window.columnconfigure(0, weight=1)
        window.rowconfigure(0, weight=1)

    def _browse_lockfile(self, lockfile_var: tk.StringVar) -> None:
        initial_dir = Path(lockfile_var.get() or "C:/Riot Games/League of Legends")
        file_path = filedialog.askopenfilename(
            title="Select League lockfile",
            initialdir=str(initial_dir if initial_dir.is_dir() else initial_dir.parent),
            filetypes=(("League lockfile", "lockfile"), ("All files", "*.*")),
        )
        if file_path:
            lockfile_var.set(file_path)

    def _browse_lockfile_dir(self, lockfile_var: tk.StringVar) -> None:
        dir_path = filedialog.askdirectory(
            title="Select League install folder",
            initialdir=lockfile_var.get() or "C:/Riot Games/League of Legends",
        )
        if dir_path:
            lockfile_var.set(dir_path)

    def _preview_sound(self, label: str, volume_percent: int) -> None:
        self._sound_player.preview(self._cue_key_from_label(label), volume_percent=volume_percent)

    def _test_notification(self) -> None:
        self._show_popup(AppEvent(EventKind.TEST_NOTIFICATION, "Test notification"))

    def _test_connection(self) -> None:
        try:
            phase = self._worker.test_connection()
        except Exception as exc:
            messagebox.showerror("League connection failed", str(exc))
            return
        messagebox.showinfo("League connection works", f"Current gameflow phase: {phase}")

    def _apply_settings(
        self,
        lockfile_path: str,
        delay_min_raw: str,
        delay_max_raw: str,
        sound_enabled: bool,
        sound_volume_percent: int,
        icon_theme_label: str,
        ui_theme_label: str,
        start_with_windows: bool,
    ) -> None:
        try:
            delay_min = float(delay_min_raw)
            delay_max = float(delay_max_raw)
            if delay_min < 0 or delay_max < delay_min:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid timing", "Delay min must be >= 0 and delay max must be >= delay min.")
            return

        settings = self._settings_store.settings
        settings.lockfile_path = lockfile_path.strip() or None
        settings.delay_min_seconds = delay_min
        settings.delay_max_seconds = delay_max
        settings.sound_enabled = sound_enabled
        settings.sound_volume_percent = max(0, min(100, int(sound_volume_percent)))
        settings.icon_theme = icon_theme_key_from_label(icon_theme_label)
        settings.ui_theme = ui_theme_label.strip().lower()
        settings.start_with_windows = start_with_windows
        try:
            set_start_with_windows(start_with_windows)
        except OSError as exc:
            messagebox.showerror("Startup setting failed", str(exc))
            return
        self._settings_store.save()
        settings = self._settings_store.settings

        lockfile_paths = lockfile_paths_from_setting(settings.lockfile_path)
        self._worker.update_timing(settings.delay_min_seconds, settings.delay_max_seconds)
        self._worker.update_lockfile_paths(lockfile_paths)
        self._sound_player.set_sound(settings.sound_enabled, settings.sound_volume_percent)
        sv_ttk.set_theme(settings.ui_theme)
        if self._icon_theme_changed_callback is not None:
            self._icon_theme_changed_callback()
        messagebox.showinfo("Settings saved", "Settings applied.")

    def _load_logs(self, log_text: scrolledtext.ScrolledText) -> None:
        log_text.configure(state="normal")
        log_text.delete("1.0", "end")
        if self._config.log_file.is_file():
            lines = self._config.log_file.read_text(encoding="utf-8", errors="replace").splitlines()
            log_text.insert("1.0", "\n".join(lines[-300:]))
        else:
            log_text.insert("1.0", "No log file yet.")
        log_text.configure(state="disabled")
        log_text.see("end")

    def _style_log_text(self, log_text: scrolledtext.ScrolledText) -> None:
        if self._settings_store.settings.ui_theme == "light":
            log_text.configure(bg="#fafafa", fg="#202020", insertbackground="#202020")
            return

        log_text.configure(bg="#1c1c1c", fg="#f5f5f5", insertbackground="#f5f5f5")

    def _open_log_file(self) -> None:
        self._config.log_file.parent.mkdir(parents=True, exist_ok=True)
        self._config.log_file.touch(exist_ok=True)
        os.startfile(str(self._config.log_file))

    def _cue_key_from_label(self, label: str) -> str:
        return next((cue.key for cue in SOUND_CUES if cue.label == label), SOUND_CUES[0].key)
