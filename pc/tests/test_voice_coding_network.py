import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from voice_coding import extract_command_ips


class VoiceCodingNetworkTests(unittest.TestCase):
    def test_extract_command_ips_windows(self):
        output = "192.168.137.1\n127.0.0.1\n10.42.0.1\n"
        self.assertEqual(
            extract_command_ips("windows", output),
            ["192.168.137.1", "127.0.0.1", "10.42.0.1"],
        )

    def test_extract_command_ips_macos_ignores_broadcast_value(self):
        output = """
en0: flags=8863<UP,BROADCAST,SMART,RUNNING,SIMPLEX,MULTICAST> mtu 1500
    inet 192.168.2.1 netmask 0xffffff00 broadcast 192.168.2.255
"""
        self.assertEqual(extract_command_ips("darwin", output), ["192.168.2.1"])

    def test_extract_command_ips_linux_ignores_broadcast_value(self):
        output = """
2: wlan0    inet 10.42.0.1/24 brd 10.42.0.255 scope global wlan0
"""
        self.assertEqual(extract_command_ips("linux", output), ["10.42.0.1"])


if __name__ == "__main__":
    unittest.main()
