import json
import unittest
from pathlib import Path

from voicing_protocol import (
    CLIENT_TO_SERVER_TYPES,
    DEFAULT_SERVER_IP,
    SERVER_TO_CLIENT_TYPES,
    UDP_BROADCAST_PORT,
    UDP_DISCOVERY_TYPE,
    WEBSOCKET_PORT,
    build_ack_message,
    build_connected_message,
    build_ping_message,
    build_pong_message,
    build_sync_disabled_message,
    build_sync_state_message,
    build_text_message,
)


def load_contract() -> dict:
    contract_path = Path(__file__).resolve().parents[2] / "protocol" / "voicing_protocol_contract.json"
    return json.loads(contract_path.read_text(encoding="utf-8"))


class ProtocolContractTests(unittest.TestCase):
    def setUp(self):
        self.contract = load_contract()

    def test_ports_match_contract(self):
        ports = self.contract["ports"]
        self.assertEqual(WEBSOCKET_PORT, ports["websocket"])
        self.assertEqual(UDP_BROADCAST_PORT, ports["udp_broadcast"])
        self.assertEqual(DEFAULT_SERVER_IP, "192.168.137.1")

    def test_udp_discovery_type_matches_contract(self):
        self.assertEqual(UDP_DISCOVERY_TYPE, self.contract["udp_discovery"]["type"])

    def test_client_message_builders_match_contract(self):
        client_messages = self.contract["messages"]["client_to_server"]
        self.assertEqual(set(CLIENT_TO_SERVER_TYPES), set(client_messages.keys()))

        text_message = build_text_message("hello")
        ping_message = build_ping_message()

        self.assertEqual(set(text_message.keys()), set(client_messages["text"]))
        self.assertEqual(set(ping_message.keys()), set(client_messages["ping"]))

    def test_server_message_builders_match_contract(self):
        server_messages = self.contract["messages"]["server_to_client"]
        self.assertEqual(set(SERVER_TO_CLIENT_TYPES), set(server_messages.keys()))

        samples = {
            "connected": build_connected_message(sync_enabled=True, computer_name="DESKTOP"),
            "ack": build_ack_message(),
            "pong": build_pong_message(sync_enabled=True),
            "sync_state": build_sync_state_message(sync_enabled=False),
            "sync_disabled": build_sync_disabled_message(),
        }

        for message_type, sample in samples.items():
            with self.subTest(message_type=message_type):
                self.assertEqual(set(sample.keys()), set(server_messages[message_type]))


if __name__ == "__main__":
    unittest.main()
