import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from voice_coding import (
    calculate_broadcast_addresses,
    extract_command_interface_candidates,
    extract_command_interfaces,
)


class NetworkInterfaceParsingTests(unittest.TestCase):
    def test_extract_command_interfaces_windows_filters_tentative_link_local_and_slash_32(self):
        output = """
[
  {"IPAddress":"169.254.42.11","PrefixLength":16,"InterfaceAlias":"Bluetooth","AddressState":1,"SkipAsSource":false},
  {"IPAddress":"192.168.1.23","PrefixLength":24,"InterfaceAlias":"Ethernet","AddressState":4,"SkipAsSource":false},
  {"IPAddress":"192.168.137.1","PrefixLength":24,"InterfaceAlias":"Local Area Connection* 10","AddressState":4,"SkipAsSource":false},
  {"IPAddress":"10.16.177.83","PrefixLength":18,"InterfaceAlias":"WLAN","AddressState":4,"SkipAsSource":false},
  {"IPAddress":"10.99.0.2","PrefixLength":24,"InterfaceAlias":"WireGuard Tunnel","AddressState":4,"SkipAsSource":false},
  {"IPAddress":"100.97.45.87","PrefixLength":32,"InterfaceAlias":"Tailscale","AddressState":4,"SkipAsSource":false}
]
"""
        self.assertEqual(
            extract_command_interfaces("windows", output),
            [("192.168.137.1", 24), ("192.168.1.23", 24), ("10.16.177.83", 18)],
        )
        candidates = extract_command_interface_candidates("windows", output)
        self.assertEqual(candidates[0].ip, "192.168.137.1")

    def test_extract_command_interfaces_linux_requires_global_ipv4_with_broadcast(self):
        output = """
[
  {
    "ifname": "eth0",
    "addr_info": [
      {"family":"inet","local":"192.168.1.23","prefixlen":24,"broadcast":"192.168.1.255","scope":"global"}
    ]
  },
  {
    "ifname": "wlan0",
    "addr_info": [
      {"family":"inet","local":"10.42.0.1","prefixlen":24,"broadcast":"10.42.0.255","scope":"global"}
    ]
  },
  {
    "ifname": "wg0",
    "addr_info": [
      {"family":"inet","local":"10.99.0.2","prefixlen":24,"broadcast":"10.99.0.255","scope":"global"}
    ]
  },
  {
    "ifname": "tailscale0",
    "addr_info": [
      {"family":"inet","local":"100.97.45.87","prefixlen":32,"scope":"global"}
    ]
  }
]
"""
        self.assertEqual(
            extract_command_interfaces("linux", output),
            [("192.168.1.23", 24), ("10.42.0.1", 24)],
        )

    def test_extract_command_interfaces_macos_parses_hex_netmask_and_skips_point_to_point(self):
        output = """
en0: flags=8863<UP,BROADCAST,SMART,RUNNING,SIMPLEX,MULTICAST> mtu 1500
    inet 192.168.2.1 netmask 0xffffff00 broadcast 192.168.2.255
en5: flags=8863<UP,BROADCAST,SMART,RUNNING,SIMPLEX,MULTICAST> mtu 1500
    inet 10.0.0.5 netmask 0xffffff00 broadcast 10.0.0.255
lo0: flags=8049<UP,LOOPBACK,RUNNING,MULTICAST> mtu 16384
    inet 127.0.0.1 netmask 0xff000000
utun4: flags=8051<UP,POINTOPOINT,RUNNING,MULTICAST> mtu 1380
    inet 100.97.45.87 --> 100.97.45.87 netmask 0xffffffff
"""
        self.assertEqual(
            extract_command_interfaces("darwin", output),
            [("10.0.0.5", 24), ("192.168.2.1", 24)],
        )

    def test_extract_command_interfaces_empty_output_returns_empty_list(self):
        self.assertEqual(extract_command_interfaces("linux", ""), [])

    def test_calculate_broadcast_addresses_skips_invalid_values(self):
        self.assertEqual(
            calculate_broadcast_addresses(
                [
                    ("192.168.1.100", 24),
                    ("192.168.137.1", 24),
                    ("10.42.0.1", 24),
                    ("10.0.0.5", 16),
                    ("invalid", 24),
                ]
            ),
            [
                ("192.168.1.100", "192.168.1.255"),
                ("192.168.137.1", "192.168.137.255"),
                ("10.42.0.1", "10.42.0.255"),
                ("10.0.0.5", "10.0.255.255"),
            ],
        )


if __name__ == "__main__":
    unittest.main()
