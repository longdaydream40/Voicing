import json

from voicing_protocol import UDP_DISCOVERY_TYPE


def refresh_server_interfaces(
    previous: list[tuple[str, str]],
    current: list[tuple[str, str]],
) -> tuple[list[tuple[str, str]], bool]:
    """Return the current discovery interfaces and whether the effective set changed."""
    changed = set(current) != set(previous)
    return current, changed


def build_udp_broadcast_payload(hotspot_ip: str, port: int, hostname: str) -> bytes:
    """Build the UDP discovery payload with the latest hotspot address."""
    return json.dumps({
        "type": UDP_DISCOVERY_TYPE,
        "ip": hotspot_ip,
        "port": port,
        "name": hostname,
    }).encode("utf-8")
