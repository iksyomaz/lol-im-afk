from __future__ import annotations

import os
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk
from typing import Callable

from lol_im_afk.config import AppConfig, lockfile_paths_from_setting
from lol_im_afk.icon_theme import ICON_THEMES, icon_theme_key_from_label, icon_theme_label_from_key
from lol_im_afk.sound import SOUND_CUES, SoundPlayer
from lol_im_afk.status import StatusStore
from lol_im_afk.user_settings import SettingsStore
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

    def notify(self, event: str) -> None:
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

    def _show_popup(self, message: str) -> None:
        if self._root is None:
            return

        self._sound_player.play_for_event(message)

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
            text=message,
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
        window.geometry("720x560")
        window.minsize(620, 480)

        settings = self._settings_store.settings
        lockfile_var = tk.StringVar(value=settings.lockfile_path or "")
        delay_min_var = tk.StringVar(value=str(settings.delay_min_seconds))
        delay_max_var = tk.StringVar(value=str(settings.delay_max_seconds))
        sound_enabled_var = tk.BooleanVar(value=settings.sound_enabled)
        sound_volume_var = tk.IntVar(value=settings.sound_volume_percent)
        preview_cue_var = tk.StringVar(value=SOUND_CUES[0].label)
        icon_theme_var = tk.StringVar(value=icon_theme_label_from_key(settings.icon_theme))
        status_var = tk.StringVar(value=self._status_store.snapshot().text)

        main = ttk.Frame(window, padding=12)
        main.pack(fill="both", expand=True)

        ttk.Label(main, text="Service").grid(row=0, column=0, sticky="w")
        ttk.Label(main, textvariable=status_var).grid(row=0, column=1, columnspan=3, sticky="ew", padx=(8, 0))

        ttk.Label(main, text="Lockfile").grid(row=1, column=0, sticky="w", pady=(10, 0))
        ttk.Entry(main, textvariable=lockfile_var).grid(row=1, column=1, sticky="ew", padx=(8, 8), pady=(10, 0))
        ttk.Button(main, text="Browse file", command=lambda: self._browse_lockfile(lockfile_var)).grid(row=1, column=2, pady=(10, 0))
        ttk.Button(main, text="Browse folder", command=lambda: self._browse_lockfile_dir(lockfile_var)).grid(row=1, column=3, padx=(8, 0), pady=(10, 0))

        ttk.Label(main, text="Delay min").grid(row=2, column=0, sticky="w", pady=(10, 0))
        ttk.Entry(main, textvariable=delay_min_var, width=8).grid(row=2, column=1, sticky="w", padx=(8, 0), pady=(10, 0))
        ttk.Label(main, text="Delay max").grid(row=2, column=2, sticky="e", pady=(10, 0))
        ttk.Entry(main, textvariable=delay_max_var, width=8).grid(row=2, column=3, sticky="w", padx=(8, 0), pady=(10, 0))

        ttk.Label(main, text="Tray icon").grid(row=3, column=0, sticky="w", pady=(10, 0))
        icon_theme_combo = ttk.Combobox(
            main,
            textvariable=icon_theme_var,
            values=[theme.label for theme in ICON_THEMES],
            state="readonly",
        )
        icon_theme_combo.grid(row=3, column=1, sticky="ew", padx=(8, 8), pady=(10, 0))

        ttk.Label(main, text="Sound volume").grid(row=4, column=0, sticky="w", pady=(10, 0))
        sound_volume = ttk.Scale(main, from_=0, to=100, variable=sound_volume_var, orient="horizontal")
        sound_volume.grid(row=4, column=1, sticky="ew", padx=(8, 8), pady=(10, 0))
        volume_label = ttk.Label(main, text=f"{sound_volume_var.get()}%")
        volume_label.grid(row=4, column=2, sticky="w", pady=(10, 0))
        sound_volume.configure(command=lambda _: volume_label.configure(text=f"{sound_volume_var.get()}%"))

        ttk.Label(main, text="Preview cue").grid(row=5, column=0, sticky="w", pady=(10, 0))
        cue_labels = [cue.label for cue in SOUND_CUES]
        cue_combo = ttk.Combobox(main, textvariable=preview_cue_var, values=cue_labels, state="readonly")
        cue_combo.grid(row=5, column=1, sticky="ew", padx=(8, 8), pady=(10, 0))
        ttk.Checkbutton(main, text="Play sound", variable=sound_enabled_var).grid(row=5, column=2, sticky="w", pady=(10, 0))
        ttk.Button(
            main,
            text="Preview",
            command=lambda: self._preview_sound(preview_cue_var.get(), sound_volume_var.get()),
        ).grid(row=5, column=3, sticky="w", padx=(8, 0), pady=(10, 0))

        button_row = ttk.Frame(main)
        button_row.grid(row=6, column=0, columnspan=4, sticky="ew", pady=(12, 8))
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
            ),
        ).pack(side="left")
        ttk.Button(button_row, text="Open log file", command=self._open_log_file).pack(side="left", padx=(8, 0))
        ttk.Button(button_row, text="Refresh logs", command=lambda: self._load_logs(log_text)).pack(side="left", padx=(8, 0))

        ttk.Label(main, text="Logs").grid(row=7, column=0, sticky="w", pady=(4, 0))
        log_text = scrolledtext.ScrolledText(main, height=16, wrap="word")
        log_text.grid(row=8, column=0, columnspan=4, sticky="nsew", pady=(4, 0))
        self._load_logs(log_text)

        main.columnconfigure(1, weight=1)
        main.rowconfigure(8, weight=1)
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

    def _apply_settings(
        self,
        lockfile_path: str,
        delay_min_raw: str,
        delay_max_raw: str,
        sound_enabled: bool,
        sound_volume_percent: int,
        icon_theme_label: str,
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
        self._settings_store.save()

        lockfile_paths = lockfile_paths_from_setting(settings.lockfile_path)
        self._worker.update_timing(delay_min, delay_max)
        self._worker.update_lockfile_paths(lockfile_paths)
        self._sound_player.set_sound(settings.sound_enabled, settings.sound_volume_percent)
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

    def _open_log_file(self) -> None:
        self._config.log_file.parent.mkdir(parents=True, exist_ok=True)
        self._config.log_file.touch(exist_ok=True)
        os.startfile(str(self._config.log_file))

    def _cue_key_from_label(self, label: str) -> str:
        return next((cue.key for cue in SOUND_CUES if cue.label == label), SOUND_CUES[0].key)
