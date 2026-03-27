"""
Additional coverage tests for autostart_manager.py module.

Tests for uncovered error cases and edge cases in autostart enable/disable.
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# Autouse fixture to prevent sys.modules pollution
@pytest.fixture(autouse=True)
def _restore_sys_modules():
    saved = dict(sys.modules)
    yield
    added = set(sys.modules.keys()) - set(saved.keys())
    for k in added:
        del sys.modules[k]
    for k, v in saved.items():
        if k not in sys.modules or sys.modules[k] is not v:
            sys.modules[k] = v


class TestAutostartManagerExtra:
    """Additional tests for autostart_manager edge cases."""

    def test_is_autostart_enabled_file_exists(self):
        """Test is_autostart_enabled returns True when file exists."""
        from vocalinux.ui import autostart_manager

        with tempfile.TemporaryDirectory() as tmp_dir:
            autostart_file = Path(tmp_dir) / "vocalinux.desktop"
            autostart_file.write_text("[Desktop Entry]\nName=Vocalinux")

            with patch.object(autostart_manager, "get_autostart_file", return_value=autostart_file):
                assert autostart_manager.is_autostart_enabled() is True

    def test_is_autostart_enabled_file_not_exists(self):
        """Test is_autostart_enabled returns False when file does not exist."""
        from vocalinux.ui import autostart_manager

        with tempfile.TemporaryDirectory() as tmp_dir:
            autostart_file = Path(tmp_dir) / "vocalinux.desktop"

            with patch.object(autostart_manager, "get_autostart_file", return_value=autostart_file):
                assert autostart_manager.is_autostart_enabled() is False

    def test_enable_autostart_permission_error(self):
        """Test enable_autostart handles permission errors gracefully."""
        from vocalinux.ui import autostart_manager

        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create a read-only directory
            readonly_dir = Path(tmp_dir) / "readonly"
            readonly_dir.mkdir()

            autostart_file = readonly_dir / "vocalinux.desktop"
            readonly_dir.chmod(0o444)  # Remove write permission

            try:
                with patch.object(
                    autostart_manager, "get_autostart_dir", return_value=readonly_dir
                ):
                    with patch.object(
                        autostart_manager, "get_autostart_file", return_value=autostart_file
                    ):
                        with patch.object(
                            autostart_manager,
                            "get_exec_command",
                            return_value="vocalinux --start-minimized",
                        ):
                            result = autostart_manager.enable_autostart()
                            assert result is False
            finally:
                # Restore permissions for cleanup
                readonly_dir.chmod(0o755)

    def test_enable_autostart_creates_parent_directories(self):
        """Test enable_autostart creates parent directories if they don't exist."""
        from vocalinux.ui import autostart_manager

        with tempfile.TemporaryDirectory() as tmp_dir:
            with patch.dict(os.environ, {"XDG_CONFIG_HOME": tmp_dir}, clear=False):
                with patch(
                    "vocalinux.ui.autostart_manager.shutil.which", return_value="/usr/bin/vocalinux"
                ):
                    result = autostart_manager.enable_autostart()
                    assert result is True

                    autostart_file = Path(tmp_dir) / "autostart" / "vocalinux.desktop"
                    assert autostart_file.exists()
                    content = autostart_file.read_text(encoding="utf-8")
                    assert "[Desktop Entry]" in content
                    assert "vocalinux" in content

    def test_disable_autostart_file_not_found(self):
        """Test disable_autostart succeeds even if file doesn't exist."""
        from vocalinux.ui import autostart_manager

        with tempfile.TemporaryDirectory() as tmp_dir:
            autostart_file = Path(tmp_dir) / "vocalinux.desktop"

            with patch.object(autostart_manager, "get_autostart_file", return_value=autostart_file):
                result = autostart_manager.disable_autostart()
                assert result is True

    def test_disable_autostart_permission_error(self):
        """Test disable_autostart handles permission errors gracefully."""
        from vocalinux.ui import autostart_manager

        with tempfile.TemporaryDirectory() as tmp_dir:
            autostart_file = Path(tmp_dir) / "vocalinux.desktop"
            autostart_file.write_text("[Desktop Entry]\nName=Vocalinux")

            # Create a mock that will raise a permission error on unlink()
            mock_file = MagicMock()
            mock_file.exists.return_value = True
            mock_file.unlink.side_effect = PermissionError("Permission denied")

            with patch.object(autostart_manager, "get_autostart_file", return_value=mock_file):
                result = autostart_manager.disable_autostart()
                assert result is False

    def test_set_autostart_enabled_true(self):
        """Test set_autostart with enabled=True calls enable_autostart."""
        from vocalinux.ui import autostart_manager

        with tempfile.TemporaryDirectory() as tmp_dir:
            with patch.dict(os.environ, {"XDG_CONFIG_HOME": tmp_dir}, clear=False):
                with patch(
                    "vocalinux.ui.autostart_manager.shutil.which", return_value="/usr/bin/vocalinux"
                ):
                    result = autostart_manager.set_autostart(True)
                    assert result is True

                    autostart_file = Path(tmp_dir) / "autostart" / "vocalinux.desktop"
                    assert autostart_file.exists()

    def test_set_autostart_enabled_false(self):
        """Test set_autostart with enabled=False calls disable_autostart."""
        from vocalinux.ui import autostart_manager

        with tempfile.TemporaryDirectory() as tmp_dir:
            # First create the file
            autostart_dir = Path(tmp_dir) / "autostart"
            autostart_dir.mkdir(parents=True)
            autostart_file = autostart_dir / "vocalinux.desktop"
            autostart_file.write_text("[Desktop Entry]\nName=Vocalinux")

            with patch.dict(os.environ, {"XDG_CONFIG_HOME": tmp_dir}, clear=False):
                result = autostart_manager.set_autostart(False)
                assert result is True
                assert not autostart_file.exists()

    def test_get_exec_command_frozen_executable(self):
        """Test get_exec_command when sys.frozen is True."""
        from vocalinux.ui import autostart_manager

        with patch("vocalinux.ui.autostart_manager.shutil.which", return_value=None):
            with patch("vocalinux.ui.autostart_manager.sys.frozen", True, create=True):
                with patch(
                    "vocalinux.ui.autostart_manager.sys.executable", "/usr/local/bin/vocalinux-bin"
                ):
                    command = autostart_manager.get_exec_command()
                    assert "/usr/local/bin/vocalinux-bin --start-minimized" in command

    def test_get_autostart_dir_without_xdg_config_home(self):
        """Test get_autostart_dir uses default location when XDG_CONFIG_HOME is not set."""
        from vocalinux.ui import autostart_manager

        # Clear XDG_CONFIG_HOME if it exists
        with patch.dict(os.environ, {}, clear=True):
            autostart_dir = autostart_manager.get_autostart_dir()
            expected = Path.home() / ".config" / "autostart"
            assert autostart_dir == expected

    def test_get_autostart_file(self):
        """Test get_autostart_file returns correct path."""
        from vocalinux.ui import autostart_manager

        with tempfile.TemporaryDirectory() as tmp_dir:
            with patch.dict(os.environ, {"XDG_CONFIG_HOME": tmp_dir}, clear=False):
                autostart_file = autostart_manager.get_autostart_file()
                expected = Path(tmp_dir) / "autostart" / "vocalinux.desktop"
                assert autostart_file == expected
