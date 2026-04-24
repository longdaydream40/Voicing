import json
import socket
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from platform_utils import get_data_dir, get_platform


DEVICE_FILE_NAME = "device.json"


@dataclass(frozen=True)
class DeviceIdentity:
    device_id: str
    name: str
    os: str


def get_device_file_path(data_dir: Optional[Path] = None) -> Path:
    return (data_dir or get_data_dir()) / DEVICE_FILE_NAME


def get_or_create_device_identity(data_dir: Optional[Path] = None) -> DeviceIdentity:
    path = get_device_file_path(data_dir)
    data = _read_device_file(path)

    device_id = _normalize_device_id(data.get("device_id"))
    if device_id is None:
        device_id = uuid.uuid4().hex
        data["device_id"] = device_id
        _write_device_file(path, data)

    return DeviceIdentity(
        device_id=device_id,
        name=get_device_name(data),
        os=get_os_name(),
    )


def get_or_create_device_id(data_dir: Optional[Path] = None) -> str:
    return get_or_create_device_identity(data_dir).device_id


def get_device_name(data: Optional[dict] = None) -> str:
    configured_name = None
    if data:
        configured_name = data.get("device_name") or data.get("name")
    if isinstance(configured_name, str) and configured_name.strip():
        return configured_name.strip()

    hostname = socket.gethostname().strip()
    return hostname or "Voicing PC"


def get_os_name() -> str:
    platform_name = get_platform()
    if platform_name == "darwin":
        return "macos"
    return platform_name


def _read_device_file(path: Path) -> dict:
    try:
        if not path.exists():
            return {}
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _write_device_file(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    tmp_path.replace(path)


def _normalize_device_id(value) -> Optional[str]:
    if not isinstance(value, str):
        return None
    normalized = value.strip().replace("-", "").lower()
    if len(normalized) < 16:
        return None
    if not all(ch in "0123456789abcdef" for ch in normalized):
        return None
    return normalized
