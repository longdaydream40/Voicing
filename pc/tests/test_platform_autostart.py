import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import platform_autostart


class PlatformAutostartTests(unittest.TestCase):
    def test_get_launch_command_in_dev_mode_uses_python_and_script(self):
        with patch.object(platform_autostart.sys, "frozen", False, create=True):
            command = platform_autostart.get_launch_command()

        self.assertEqual(command[0], sys.executable)
        self.assertTrue(command[1].endswith("voice_coding.py"))

    def test_format_desktop_exec_quotes_paths_with_spaces(self):
        command = platform_autostart._format_desktop_exec(
            ["/home/tester/My App/voicing", "--flag"]
        )
        self.assertIn('"/home/tester/My App/voicing"', command)

    def test_linux_autostart_file_can_be_written_and_removed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            desktop_path = Path(temp_dir) / "voicing.desktop"
            with patch("platform_autostart.get_platform", return_value="linux"):
                with patch("platform_autostart._get_linux_autostart_path", return_value=desktop_path):
                    self.assertTrue(platform_autostart.set_startup_enabled(True))
                    content = desktop_path.read_text(encoding="utf-8")
                    self.assertIn("OnlyShowIn=GNOME;", content)
                    self.assertIn("X-GNOME-Autostart-enabled=true", content)
                    self.assertTrue(platform_autostart.is_startup_enabled())

                    self.assertTrue(platform_autostart.set_startup_enabled(False))
                    self.assertFalse(desktop_path.exists())
                    self.assertFalse(platform_autostart.is_startup_enabled())


if __name__ == "__main__":
    unittest.main()
