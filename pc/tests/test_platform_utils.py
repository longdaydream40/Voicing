import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import platform_utils


class PlatformUtilsTests(unittest.TestCase):
    def test_get_platform_returns_supported_value(self):
        self.assertIn(platform_utils.get_platform(), {"windows", "darwin", "linux"})

    def test_get_log_dir_windows(self):
        with patch.object(platform_utils.sys, "platform", "win32"):
            with patch.dict(os.environ, {"APPDATA": r"C:\Users\tester\AppData\Roaming"}, clear=False):
                self.assertEqual(
                    platform_utils.get_log_dir(),
                    Path(r"C:\Users\tester\AppData\Roaming") / "Voicing" / "logs",
                )

    def test_get_data_dir_macos(self):
        fake_home = Path("/Users/tester")
        with patch.object(platform_utils.sys, "platform", "darwin"):
            with patch.object(platform_utils.Path, "home", return_value=fake_home):
                self.assertEqual(
                    platform_utils.get_data_dir(),
                    fake_home / "Library" / "Application Support" / "Voicing",
                )

    def test_get_data_dir_linux(self):
        fake_home = Path("/home/tester")
        with patch.object(platform_utils.sys, "platform", "linux"):
            with patch.object(platform_utils.Path, "home", return_value=fake_home):
                self.assertEqual(
                    platform_utils.get_data_dir(),
                    fake_home / ".local" / "share" / "Voicing",
                )

    def test_wayland_runtime_is_blocked(self):
        with patch.object(platform_utils.sys, "platform", "linux"):
            with patch.dict(os.environ, {"XDG_SESSION_TYPE": "wayland"}, clear=False):
                with self.assertRaises(RuntimeError):
                    platform_utils.ensure_runtime_supported()

    def test_known_hotspot_prefixes_cover_all_platforms(self):
        self.assertEqual(
            platform_utils.get_known_hotspot_prefixes(),
            ("192.168.137.", "192.168.2.", "10.42.0."),
        )


if __name__ == "__main__":
    unittest.main()
