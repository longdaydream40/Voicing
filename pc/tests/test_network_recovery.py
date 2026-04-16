import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from network_recovery import build_udp_broadcast_payload, refresh_hotspot_ip


class NetworkRecoveryTests(unittest.TestCase):
    def test_refresh_hotspot_ip_detects_changes(self):
        current_ip, changed = refresh_hotspot_ip("192.168.137.1", "192.168.137.42")

        self.assertEqual(current_ip, "192.168.137.42")
        self.assertTrue(changed)

    def test_refresh_hotspot_ip_keeps_same_address_without_false_change(self):
        current_ip, changed = refresh_hotspot_ip("192.168.137.1", "192.168.137.1")

        self.assertEqual(current_ip, "192.168.137.1")
        self.assertFalse(changed)

    def test_build_udp_broadcast_payload_uses_latest_ip(self):
        payload = build_udp_broadcast_payload("192.168.137.42", 9527, "DESKTOP-TEST")
        data = json.loads(payload.decode("utf-8"))

        self.assertEqual(data["type"], "voice_coding_server")
        self.assertEqual(data["ip"], "192.168.137.42")
        self.assertEqual(data["port"], 9527)
        self.assertEqual(data["name"], "DESKTOP-TEST")


if __name__ == "__main__":
    unittest.main()
