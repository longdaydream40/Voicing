import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from voicing_protocol import (
    CLIENT_TO_SERVER_TYPES,
    DEFAULT_SERVER_IP,
    QR_SCAN_PING_SOURCE,
    QR_PAYLOAD_TYPE,
    QR_PAYLOAD_VERSION,
    SERVER_TO_CLIENT_TYPES,
    TEXT_SEND_MODE_SHADOW,
    TEXT_SEND_MODE_SUBMIT,
    UDP_BROADCAST_PORT,
    UDP_DISCOVERY_TYPE,
    WEBSOCKET_PORT,
    build_ack_message,
    build_connected_message,
    build_ping_message,
    build_pong_message,
    build_qr_payload,
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
        self.assertEqual(QR_SCAN_PING_SOURCE, "qr_scan")
        self.assertEqual(text_message["send_mode"], TEXT_SEND_MODE_SUBMIT)
        self.assertEqual(
            build_text_message("shadow", send_mode=TEXT_SEND_MODE_SHADOW)["send_mode"],
            TEXT_SEND_MODE_SHADOW,
        )

    def test_server_message_builders_match_contract(self):
        server_messages = self.contract["messages"]["server_to_client"]
        self.assertEqual(set(SERVER_TO_CLIENT_TYPES), set(server_messages.keys()))

        samples = {
            "connected": build_connected_message(
                sync_enabled=True,
                computer_name="DESKTOP",
                device_id="abc123def4567890",
                os_name="windows",
            ),
            "ack": build_ack_message(),
            "pong": build_pong_message(sync_enabled=True),
            "sync_state": build_sync_state_message(sync_enabled=False),
            "sync_disabled": build_sync_disabled_message(),
        }

        for message_type, sample in samples.items():
            with self.subTest(message_type=message_type):
                self.assertEqual(set(sample.keys()), set(server_messages[message_type]))

        self.assertTrue(build_ack_message()["clear_input"])
        self.assertFalse(build_ack_message(clear_input=False)["clear_input"])

    def test_qr_payload_builder_matches_contract(self):
        qr_contract = self.contract["qr_payload"]
        payload = build_qr_payload(
            device_id="abc123def4567890",
            ip="192.168.137.1",
            port=WEBSOCKET_PORT,
            name="DESKTOP",
            os_name="windows",
            ips=["192.168.137.1", "10.16.177.83"],
        )

        self.assertEqual(
            set(payload.keys()),
            set(qr_contract["required_fields"]) | set(qr_contract["optional_fields"]),
        )
        self.assertEqual(payload["v"], QR_PAYLOAD_VERSION)
        self.assertEqual(payload["type"], QR_PAYLOAD_TYPE)
        self.assertEqual(payload["device_id"], "abc123def4567890")
        self.assertEqual(payload["ips"], ["192.168.137.1", "10.16.177.83"])


if __name__ == "__main__":
    unittest.main()
