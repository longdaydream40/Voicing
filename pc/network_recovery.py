import json


def refresh_hotspot_ip(previous_ip: str, current_ip: str) -> tuple[str, bool]:
    """Return the current hotspot IP and whether it changed."""
    changed = current_ip != previous_ip
    return current_ip, changed


def build_udp_broadcast_payload(hotspot_ip: str, port: int, hostname: str) -> bytes:
    """Build the UDP discovery payload with the latest hotspot address."""
    return json.dumps({
        "type": "voice_coding_server",
        "ip": hotspot_ip,
        "port": port,
        "name": hostname,
    }).encode("utf-8")
