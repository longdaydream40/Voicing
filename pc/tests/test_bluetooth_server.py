import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bluetooth_server import (
    BLUETOOTH_MESSAGE_DELIMITER_BYTES,
    BluetoothClientAdapter,
    BluetoothClientInfo,
    _mac_to_bth_addr,
    split_bluetooth_messages,
)


class _FakeSocket:
    def __init__(self):
        self.payloads = []

    def sendall(self, payload: bytes):
        self.payloads.append(payload)

    def close(self):
        return None


class BluetoothServerTests(unittest.TestCase):
    def test_split_bluetooth_messages_handles_partial_chunks(self):
        buffer = bytearray()
        part1 = split_bluetooth_messages(
            buffer,
            b'{"type":"ping"}\n{"type":"text"',
        )
        part2 = split_bluetooth_messages(
            buffer,
            b',"content":"hello"}\n',
        )

        self.assertEqual(part1, ['{"type":"ping"}'])
        self.assertEqual(part2, ['{"type":"text","content":"hello"}'])
        self.assertEqual(buffer, bytearray())

    def test_send_message_appends_json_delimiter(self):
        fake_socket = _FakeSocket()
        client = BluetoothClientAdapter(
            fake_socket,
            BluetoothClientInfo(label="DEVICE"),
        )

        client.send_message({"type": "pong", "sync_enabled": True})

        self.assertEqual(len(fake_socket.payloads), 1)
        payload = fake_socket.payloads[0]
        self.assertTrue(payload.endswith(BLUETOOTH_MESSAGE_DELIMITER_BYTES))
        self.assertEqual(
            json.loads(payload[:-1].decode("utf-8")),
            {"type": "pong", "sync_enabled": True},
        )

    def test_mac_to_bth_addr_parses_common_mac_formats(self):
        self.assertEqual(_mac_to_bth_addr("12:34:56:78:9A:BC"), 0x123456789ABC)
        self.assertEqual(_mac_to_bth_addr("12-34-56-78-9A-BC"), 0x123456789ABC)


if __name__ == "__main__":
    unittest.main()
