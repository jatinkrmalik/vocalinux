"""
Regression guards for the ponytail mega-cleanup.

These tests drive shipped modules on the real import path and assert that
dead APIs stay gone while kept product surface still works.
"""

import unittest
from pathlib import Path

from vocalinux.common_types import RecognitionState
from vocalinux.speech_recognition.command_processor import CommandProcessor
from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager
from vocalinux.ui.config_manager import ConfigManager
from vocalinux.ui.keyboard_backends import SHORTCUT_DISPLAY_NAMES, SUPPORTED_SHORTCUTS
from vocalinux.utils.resource_manager import ResourceManager
from vocalinux.utils.whispercpp_model_info import WHISPERCPP_MODEL_INFO, detect_cpu_info
from vocalinux.version import __version__


class TestPonytailCleanupSurface(unittest.TestCase):
    """Ensure cleanup removals stick and kept behavior still works."""

    def test_recognition_manager_dead_apis_removed(self):
        """Test-only buffer/level helpers must stay deleted."""
        self.assertTrue(hasattr(SpeechRecognitionManager, "_download_with_progress"))
        for dead in (
            "set_buffer_limit",
            "get_buffer_stats",
            "get_last_audio_level",
            "_process_final_buffer",
        ):
            self.assertFalse(
                hasattr(SpeechRecognitionManager, dead),
                f"dead API should remain removed: {dead}",
            )

    def test_about_dialog_only_gtk_standard(self):
        """Tray uses show_about_dialog; custom AboutDialog class is gone."""
        about_path = (
            Path(__file__).resolve().parents[1] / "src" / "vocalinux" / "ui" / "about_dialog.py"
        )
        source = about_path.read_text(encoding="utf-8")
        self.assertIn("def show_about_dialog(", source)
        self.assertIn("Gtk.AboutDialog()", source)
        self.assertNotIn("class AboutDialog(", source)

    def test_command_processor_generic_path(self):
        """process_text still returns (text, commands) on the real implementation."""
        processor = CommandProcessor()
        text, commands = processor.process_text("hello world period")
        self.assertIsInstance(text, str)
        self.assertTrue(text)
        self.assertIn(".", text)
        self.assertIsInstance(commands, list)

    def test_config_defaults_drop_dead_keys(self):
        """Unused notification/debug defaults removed; engines still configured."""
        manager = ConfigManager()
        config = manager.config
        engine = config["speech_recognition"]["engine"]
        self.assertIn(engine, ("vosk", "whisper", "whisper_cpp", "remote_api"))
        self.assertNotIn("show_notifications", config.get("ui", {}))
        self.assertNotIn("debug_logging", config.get("advanced", {}))
        self.assertNotIn("wayland_mode", config.get("advanced", {}))

    def test_resource_manager_package_icons(self):
        """Resources resolve from the package tree after ResourceManager simplification."""
        manager = ResourceManager()
        icon = manager.get_icon_path("vocalinux")
        self.assertTrue(icon)
        self.assertTrue(Path(icon).exists(), f"missing icon at {icon}")

    def test_model_info_and_keyboard_surface(self):
        """whisper.cpp catalog and keyboard shortcut tables remain available."""
        self.assertIn("tiny", WHISPERCPP_MODEL_INFO)
        cpu = detect_cpu_info()
        self.assertTrue(cpu)
        self.assertIn("ctrl+ctrl", SUPPORTED_SHORTCUTS)
        self.assertIn("ctrl+ctrl", SHORTCUT_DISPLAY_NAMES)
        self.assertEqual(RecognitionState.IDLE.name, "IDLE")
        self.assertTrue(__version__)
