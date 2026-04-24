import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from network_recovery import build_udp_broadcast_payload, refresh_server_interfaces


class NetworkRecoveryTests(unittest.TestCase):
    def test_refresh_server_interfaces_detects_added_interface(self):
        current_interfaces, changed = refresh_server_interfaces(
            [("192.168.137.1", "192.168.137.255")],
            [
                ("192.168.137.1", "192.168.137.255"),
                ("10.16.177.83", "10.16.179.255"),
            ],
        )

        self.assertEqual(
            current_interfaces,
            [
                ("192.168.137.1", "192.168.137.255"),
                ("10.16.177.83", "10.16.179.255"),
            ],
        )
        self.assertTrue(changed)

    def test_refresh_server_interfaces_keeps_same_set_without_false_change(self):
        current_interfaces, changed = refresh_server_interfaces(
            [
                ("192.168.137.1", "192.168.137.255"),
                ("10.16.177.83", "10.16.179.255"),
            ],
            [
                ("10.16.177.83", "10.16.179.255"),
                ("192.168.137.1", "192.168.137.255"),
            ],
        )

        self.assertEqual(
            current_interfaces,
            [
                ("10.16.177.83", "10.16.179.255"),
                ("192.168.137.1", "192.168.137.255"),
            ],
        )
        self.assertFalse(changed)

    def test_refresh_server_interfaces_detects_removed_interface(self):
        current_interfaces, changed = refresh_server_interfaces(
            [
                ("192.168.137.1", "192.168.137.255"),
                ("10.16.177.83", "10.16.179.255"),
            ],
            [("192.168.137.1", "192.168.137.255")],
        )

        self.assertEqual(current_interfaces, [("192.168.137.1", "192.168.137.255")])
        self.assertTrue(changed)

    def test_build_udp_broadcast_payload_uses_latest_ip(self):
        payload = build_udp_broadcast_payload(
            "192.168.137.42",
            9527,
            "DESKTOP-TEST",
            "abc123",
            "windows",
        )
        data = json.loads(payload.decode("utf-8"))

        self.assertEqual(data["type"], "voice_coding_server")
        self.assertEqual(data["ip"], "192.168.137.42")
        self.assertEqual(data["port"], 9527)
        self.assertEqual(data["name"], "DESKTOP-TEST")
        self.assertEqual(data["device_id"], "abc123")
        self.assertEqual(data["os"], "windows")


if __name__ == "__main__":
    unittest.main()
