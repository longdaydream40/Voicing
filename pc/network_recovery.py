import json

from voicing_protocol import UDP_DISCOVERY_TYPE


def refresh_server_interfaces(
    previous: list[tuple[str, str]],
    current: list[tuple[str, str]],
) -> tuple[list[tuple[str, str]], bool]:
    """Return the current discovery interfaces and whether the effective set changed."""
    changed = set(current) != set(previous)
    return current, changed


def build_udp_broadcast_payload(
    hotspot_ip: str,
    port: int,
    hostname: str,
    device_id: str = "",
    os_name: str = "",
) -> bytes:
    """Build the UDP discovery payload with the latest hotspot address."""
    payload = {
        "type": UDP_DISCOVERY_TYPE,
        "ip": hotspot_ip,
        "port": port,
        "name": hostname,
    }
    if device_id:
        payload["device_id"] = device_id
    if os_name:
        payload["os"] = os_name
    return json.dumps(payload).encode("utf-8")
