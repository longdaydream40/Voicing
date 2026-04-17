import os
import subprocess
import sys
from pathlib import Path


APP_NAME = "Voicing"

WINDOWS_HOTSPOT_PREFIXES = ("192.168.137.",)
MACOS_HOTSPOT_PREFIXES = ("192.168.2.",)
LINUX_HOTSPOT_PREFIXES = ("10.42.0.",)


def get_platform() -> str:
    if sys.platform.startswith("win"):
        return "windows"
    if sys.platform == "darwin":
        return "darwin"
    if sys.platform.startswith("linux"):
        return "linux"
    raise RuntimeError(f"Unsupported platform: {sys.platform}")


def get_log_dir() -> Path:
    platform_name = get_platform()
    if platform_name == "windows":
        return Path(os.environ.get("APPDATA", Path.home())) / APP_NAME / "logs"
    if platform_name == "darwin":
        return Path.home() / "Library" / "Logs" / APP_NAME
    return Path.home() / ".local" / "share" / APP_NAME / "logs"


def get_data_dir() -> Path:
    platform_name = get_platform()
    if platform_name == "windows":
        return Path(os.environ.get("APPDATA", Path.home())) / APP_NAME
    if platform_name == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME
    return Path.home() / ".local" / "share" / APP_NAME


def open_file_in_default_app(path: Path) -> None:
    target = str(path)
    platform_name = get_platform()
    if platform_name == "windows":
        os.startfile(target)
        return
    if platform_name == "darwin":
        subprocess.Popen(["open", target])
        return
    subprocess.Popen(["xdg-open", target])


def open_file_in_text_editor(path: Path) -> None:
    target = str(path)
    platform_name = get_platform()
    if platform_name == "windows":
        subprocess.Popen(["notepad.exe", target])
        return
    if platform_name == "darwin":
        subprocess.Popen(["open", "-t", target])
        return
    subprocess.Popen(["xdg-open", target])


def get_native_font_family() -> str:
    platform_name = get_platform()
    if platform_name == "windows":
        return "'Segoe UI', 'Microsoft YaHei UI', sans-serif"
    if platform_name == "darwin":
        return "'-apple-system', 'SF Pro Text', 'PingFang SC', sans-serif"
    return "'Ubuntu', 'Cantarell', 'Noto Sans CJK SC', sans-serif"


def get_default_server_ip() -> str:
    platform_name = get_platform()
    if platform_name == "windows":
        return "192.168.137.1"
    if platform_name == "darwin":
        return "192.168.2.1"
    return "10.42.0.1"


def get_default_hotspot_ip() -> str:
    """Backward-compatible alias for the preferred local discovery address."""
    return get_default_server_ip()


def get_preferred_hotspot_prefixes() -> tuple[str, ...]:
    platform_name = get_platform()
    if platform_name == "windows":
        return WINDOWS_HOTSPOT_PREFIXES
    if platform_name == "darwin":
        return MACOS_HOTSPOT_PREFIXES
    return LINUX_HOTSPOT_PREFIXES


def get_known_hotspot_prefixes() -> tuple[str, ...]:
    return WINDOWS_HOTSPOT_PREFIXES + MACOS_HOTSPOT_PREFIXES + LINUX_HOTSPOT_PREFIXES


def is_wayland_session() -> bool:
    if get_platform() != "linux":
        return False
    session_type = os.environ.get("XDG_SESSION_TYPE", "").strip().lower()
    return session_type == "wayland" or bool(os.environ.get("WAYLAND_DISPLAY"))


def ensure_runtime_supported() -> None:
    if is_wayland_session():
        raise RuntimeError(
            "Voicing 的 Linux 桌面端当前仅支持 Ubuntu 22.04 GNOME on X11。"
            "当前检测到 Wayland 会话，请切换到 X11 后再启动。"
        )
