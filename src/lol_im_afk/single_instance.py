from __future__ import annotations

import ctypes
import sys
from types import TracebackType


ERROR_ALREADY_EXISTS = 183


class SingleInstance:
    def __init__(self, name: str = "Local\\lol-im-afk") -> None:
        self.name = name
        self._handle: int | None = None
        self.acquired = True

    def __enter__(self) -> SingleInstance:
        if sys.platform != "win32":
            return self

        kernel32 = ctypes.windll.kernel32
        kernel32.CreateMutexW.argtypes = (ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p)
        kernel32.CreateMutexW.restype = ctypes.c_void_p
        kernel32.CloseHandle.argtypes = (ctypes.c_void_p,)
        kernel32.CloseHandle.restype = ctypes.c_bool
        self._handle = kernel32.CreateMutexW(None, False, self.name)
        self.acquired = bool(self._handle) and kernel32.GetLastError() != ERROR_ALREADY_EXISTS
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self._handle and sys.platform == "win32":
            ctypes.windll.kernel32.CloseHandle(self._handle)
            self._handle = None


def show_windows_message(title: str, message: str, error: bool = False) -> None:
    if sys.platform != "win32":
        print(f"{title}: {message}", file=sys.stderr if error else sys.stdout)
        return

    icon_flag = 0x10 if error else 0x40
    ctypes.windll.user32.MessageBoxW(None, message, title, icon_flag)
