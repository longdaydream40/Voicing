from __future__ import annotations

import ctypes
from pathlib import Path

from PyQt5.QtWidgets import QApplication, QMessageBox

from platform_utils import get_data_dir, get_platform


MUTEX_NAME = "Voicing_SingleInstance_Mutex"
_windows_mutex_handle = None
_lock_handle = None


def check_single_instance() -> bool:
    global _windows_mutex_handle, _lock_handle

    if get_platform() == "windows":
        kernel32 = ctypes.windll.kernel32
        mutex = kernel32.CreateMutexW(None, False, MUTEX_NAME)
        last_error = kernel32.GetLastError()
        if last_error == 183:
            kernel32.CloseHandle(mutex)
            return False
        _windows_mutex_handle = mutex
        return True

    import fcntl

    data_dir = get_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    lock_path = Path(data_dir) / "voicing.lock"
    lock_handle = lock_path.open("w", encoding="utf-8")
    try:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        lock_handle.close()
        return False

    _lock_handle = lock_handle
    return True


def show_already_running_message() -> None:
    if get_platform() == "windows":
        ctypes.windll.user32.MessageBoxW(
            0,
            "Voicing 已经在运行中！\n\n请查看系统托盘图标。\n\nVoicing is already running!\nPlease check the system tray.",
            "Voicing",
            0x40,
        )
        return

    owns_app = QApplication.instance() is None
    app = QApplication.instance() if not owns_app else QApplication([])
    QMessageBox.information(
        None,
        "Voicing",
        "Voicing 已经在运行中！\n\n请查看系统托盘图标。\n\nVoicing is already running!\nPlease check the system tray.",
    )
    if owns_app:
        app.quit()
