import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from vocalinux.ui import autostart_manager


class TestAutostartManager(unittest.TestCase):
    def test_get_autostart_dir_uses_xdg_config_home(self):
        with patch.dict("os.environ", {"XDG_CONFIG_HOME": "/tmp/vlx-config"}, clear=False):
            autostart_dir = autostart_manager.get_autostart_dir()
        self.assertEqual(autostart_dir, Path("/tmp/vlx-config") / "autostart")

    def test_get_exec_command_prefers_installed_command(self):
        with patch(
            "vocalinux.ui.autostart_manager.shutil.which",
            return_value="/usr/bin/vocalinux",
        ):
            command = autostart_manager.get_exec_command()
        self.assertEqual(command, "/usr/bin/vocalinux --start-minimized")

    def test_get_exec_command_falls_back_to_python_module(self):
        with patch("vocalinux.ui.autostart_manager.shutil.which", return_value=None), patch(
            "vocalinux.ui.autostart_manager.sys.executable", "/usr/bin/python3"
        ), patch("vocalinux.ui.autostart_manager.sys.frozen", new=False, create=True):
            command = autostart_manager.get_exec_command()
        self.assertEqual(command, "/usr/bin/python3 -m vocalinux.main --start-minimized")

    def test_enable_disable_autostart_creates_and_removes_entry(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            with patch.dict("os.environ", {"XDG_CONFIG_HOME": tmp_dir}, clear=False), patch(
                "vocalinux.ui.autostart_manager.shutil.which",
                return_value="/usr/bin/vocalinux",
            ):
                enabled = autostart_manager.enable_autostart()
                self.assertTrue(enabled)

                desktop_file = Path(tmp_dir) / "autostart" / "vocalinux.desktop"
                self.assertTrue(desktop_file.exists())
                content = desktop_file.read_text(encoding="utf-8")
                self.assertIn("Exec=/usr/bin/vocalinux --start-minimized", content)

                disabled = autostart_manager.disable_autostart()
                self.assertTrue(disabled)
                self.assertFalse(desktop_file.exists())
