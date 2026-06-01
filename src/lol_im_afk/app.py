from __future__ import annotations

import argparse
import logging
import sys
import time
from collections.abc import Sequence

from lol_im_afk.config import AppConfig, lockfile_paths_from_setting
from lol_im_afk.desktop_ui import DesktopUi
from lol_im_afk.lcu_client import LcuClient
from lol_im_afk.status import StatusStore
from lol_im_afk.user_settings import SettingsStore
from lol_im_afk.worker import AutoAcceptWorker


def configure_logging(config: AppConfig, console: bool = False) -> None:
    config.log_file.parent.mkdir(parents=True, exist_ok=True)
    handlers: list[logging.Handler] = [logging.FileHandler(config.log_file, encoding="utf-8")]
    if console:
        handlers.append(logging.StreamHandler())

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=handlers,
    )


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    settings_store = SettingsStore()
    settings = settings_store.settings
    config = AppConfig(
        delay_min_seconds=settings.delay_min_seconds,
        delay_max_seconds=settings.delay_max_seconds,
        lockfile_paths=lockfile_paths_from_setting(settings.lockfile_path),
    )
    config.validate()
    configure_logging(config, console=args.cli)

    status_store = StatusStore()
    lcu_client = LcuClient(
        lockfile_paths=config.lockfile_paths,
        request_timeout_seconds=config.request_timeout_seconds,
    )
    event_callback = print if args.cli else None
    worker = AutoAcceptWorker(
        config=config,
        lcu_client=lcu_client,
        status_store=status_store,
        event_callback=event_callback,
    )
    worker.start()

    try:
        if args.cli:
            run_cli(worker=worker, config=config)
        else:
            run_tray_app(
                worker=worker,
                status_store=status_store,
                config=config,
                settings_store=settings_store,
            )
    finally:
        worker.stop()


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="League ready-check auto-accept helper")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--cli",
        action="store_true",
        help="run in the foreground and print match timing events",
    )
    mode.add_argument(
        "--tray",
        action="store_true",
        help="run the tray app; this is the default",
    )
    return parser.parse_args(argv)


def run_cli(worker: AutoAcceptWorker, config: AppConfig) -> None:
    print("lol-im-afk CLI mode running. Press Ctrl+C to quit.")
    print(f"Log file: {config.log_file}")
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("Stopping lol-im-afk")


def run_tray_app(
    worker: AutoAcceptWorker,
    status_store: StatusStore,
    config: AppConfig,
    settings_store: SettingsStore,
) -> None:
    from lol_im_afk.tray import run_tray

    desktop_ui = DesktopUi(
        config=config,
        settings_store=settings_store,
        worker=worker,
        status_store=status_store,
    )
    try:
        run_tray(
            worker=worker,
            status_store=status_store,
            desktop_ui=desktop_ui,
            settings_store=settings_store,
        )
    finally:
        desktop_ui.stop()
