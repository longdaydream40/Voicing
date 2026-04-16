from __future__ import annotations

import os
import plistlib
import sys
from pathlib import Path

from platform_utils import get_platform


APP_NAME = "Voicing"
STARTUP_REGISTRY_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
MACOS_LAUNCH_AGENT_LABEL = "com.kevinlasnh.voicing"


def get_executable_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve()
    return Path(__file__).resolve().with_name("voice_coding.py")


def get_launch_command() -> list[str]:
    if getattr(sys, "frozen", False):
        return [str(get_executable_path())]
    return [sys.executable, str(get_executable_path())]


def is_startup_enabled() -> bool:
    platform_name = get_platform()
    try:
        if platform_name == "windows":
            import winreg

            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                STARTUP_REGISTRY_KEY,
                0,
                winreg.KEY_READ,
            ) as key:
                winreg.QueryValueEx(key, APP_NAME)
                return True

        if platform_name == "darwin":
            return _get_launch_agent_path().exists()

        return _get_linux_autostart_path().exists()
    except FileNotFoundError:
        return False
    except Exception:
        return False


def set_startup_enabled(enabled: bool) -> bool:
    platform_name = get_platform()
    try:
        if platform_name == "windows":
            import winreg

            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, STARTUP_REGISTRY_KEY) as key:
                if enabled:
                    winreg.SetValueEx(
                        key,
                        APP_NAME,
                        0,
                        winreg.REG_SZ,
                        _format_windows_command(get_launch_command()),
                    )
                else:
                    try:
                        winreg.DeleteValue(key, APP_NAME)
                    except FileNotFoundError:
                        pass
            return True

        if platform_name == "darwin":
            path = _get_launch_agent_path()
            if enabled:
                path.parent.mkdir(parents=True, exist_ok=True)
                payload = {
                    "Label": MACOS_LAUNCH_AGENT_LABEL,
                    "ProgramArguments": get_launch_command(),
                    "RunAtLoad": True,
                }
                with path.open("wb") as handle:
                    plistlib.dump(payload, handle)
            else:
                path.unlink(missing_ok=True)
            return True

        path = _get_linux_autostart_path()
        if enabled:
            path.parent.mkdir(parents=True, exist_ok=True)
            command = get_launch_command()
            path.write_text(
                "\n".join(
                    [
                        "[Desktop Entry]",
                        "Type=Application",
                        "Name=Voicing",
                        f"Exec={_format_desktop_exec(command)}",
                        f"TryExec={_escape_desktop_arg(command[0])}",
                        "OnlyShowIn=GNOME;",
                        "X-GNOME-Autostart-enabled=true",
                        "Terminal=false",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
        else:
            path.unlink(missing_ok=True)
        return True
    except Exception:
        return False


def _get_launch_agent_path() -> Path:
    return Path.home() / "Library" / "LaunchAgents" / f"{MACOS_LAUNCH_AGENT_LABEL}.plist"


def _get_linux_autostart_path() -> Path:
    return Path.home() / ".config" / "autostart" / "voicing.desktop"


def _format_windows_command(parts: list[str]) -> str:
    return " ".join(f'"{part}"' for part in parts)


def _format_desktop_exec(parts: list[str]) -> str:
    return " ".join(_escape_desktop_arg(part) for part in parts)


def _escape_desktop_arg(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    if any(char.isspace() for char in escaped):
        return f'"{escaped}"'
    return escaped
