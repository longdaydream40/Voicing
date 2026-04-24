import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from device_identity import get_or_create_device_identity, get_device_file_path


class DeviceIdentityTests(unittest.TestCase):
    def test_creates_and_reuses_device_id(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir)
            first = get_or_create_device_identity(data_dir)
            second = get_or_create_device_identity(data_dir)

            self.assertEqual(first.device_id, second.device_id)
            self.assertEqual(len(first.device_id), 32)
            self.assertEqual(
                json.loads(get_device_file_path(data_dir).read_text(encoding="utf-8"))["device_id"],
                first.device_id,
            )

    def test_uses_configured_device_name(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir)
            get_device_file_path(data_dir).write_text(
                json.dumps({
                    "device_id": "ABCDEF1234567890",
                    "device_name": "Kevin Desktop",
                }),
                encoding="utf-8",
            )

            identity = get_or_create_device_identity(data_dir)

            self.assertEqual(identity.device_id, "abcdef1234567890")
            self.assertEqual(identity.name, "Kevin Desktop")

    def test_maps_darwin_to_macos(self):
        with tempfile.TemporaryDirectory() as temp_dir, patch(
            "device_identity.get_platform",
            return_value="darwin",
        ):
            identity = get_or_create_device_identity(Path(temp_dir))

            self.assertEqual(identity.os, "macos")


if __name__ == "__main__":
    unittest.main()
