"""
Tests for auto-pause process matching, monitor pause/resume, and model unload.

Exercises the shipped matching helpers and AutoPauseMonitor against real
callbacks — not a parallel reimplementation of the match logic.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Heavy deps used transitively when importing recognition manager
mock_pywhispercpp = MagicMock()
mock_pywhispercpp.model = MagicMock()
mock_pywhispercpp.model.Model = MagicMock()

sys.modules.setdefault("vosk", MagicMock())
sys.modules.setdefault("whisper", MagicMock())
sys.modules.setdefault("pywhispercpp", mock_pywhispercpp)
sys.modules.setdefault("pywhispercpp.model", mock_pywhispercpp.model)
sys.modules.setdefault("requests", MagicMock())
sys.modules.setdefault("pyaudio", MagicMock())
sys.modules.setdefault("wave", MagicMock())
sys.modules.setdefault("tqdm", MagicMock())
sys.modules.setdefault("numpy", MagicMock())
sys.modules.setdefault("torch", MagicMock())
sys.modules.setdefault("psutil", MagicMock())

from vocalinux.auto_pause_monitor import (  # noqa: E402
    AutoPauseMonitor,
    any_configured_process_running,
    configured_names_set,
    normalize_process_name,
)
from vocalinux.common_types import RecognitionState  # noqa: E402
from vocalinux.ui.config_manager import DEFAULT_CONFIG  # noqa: E402


class TestNormalizeAndMatch(unittest.TestCase):
    """Pure matching helpers (no I/O)."""

    def test_normalize_basename_and_case(self):
        self.assertEqual(normalize_process_name("Overwatch"), "overwatch")
        self.assertEqual(normalize_process_name("/usr/bin/Steam"), "steam")
        self.assertEqual(normalize_process_name("game.EXE"), "game")
        self.assertEqual(normalize_process_name("  chrome  "), "chrome")
        self.assertEqual(normalize_process_name(""), "")

    def test_configured_names_set_drops_empty(self):
        self.assertEqual(
            configured_names_set(["Overwatch", "", "  ", "steam"]),
            {"overwatch", "steam"},
        )

    def test_match_when_process_running(self):
        self.assertTrue(
            any_configured_process_running(
                ["overwatch", "steam"],
                ["bash", "Overwatch.exe", "Xorg"],
            )
        )

    def test_no_match_when_absent(self):
        self.assertFalse(
            any_configured_process_running(
                ["overwatch"],
                ["bash", "chrome", "Xorg"],
            )
        )

    def test_empty_config_never_matches(self):
        self.assertFalse(any_configured_process_running([], ["overwatch", "steam"]))
        self.assertFalse(any_configured_process_running(["", "  "], ["overwatch"]))

    def test_match_via_exe_basename_path(self):
        self.assertTrue(
            any_configured_process_running(
                ["firefox"],
                ["/usr/lib/firefox/firefox"],
            )
        )


class TestAutoPauseMonitor(unittest.TestCase):
    """Poller state machine: pause once, resume once, no double-fire."""

    def _make_monitor(self, enabled=True, apps=None, snapshot=None):
        apps = apps if apps is not None else ["overwatch"]
        config = {"enabled": enabled, "apps": list(apps), "interval": 5.0}
        pause_cb = MagicMock()
        resume_cb = MagicMock()
        running = snapshot if snapshot is not None else (lambda: set())

        def get_config():
            return config["enabled"], config["apps"], config["interval"]

        monitor = AutoPauseMonitor(
            get_config=get_config,
            on_pause=pause_cb,
            on_resume=resume_cb,
            process_snapshot=running if callable(running) else (lambda: running),
            use_glib=False,
        )
        return monitor, pause_cb, resume_cb, config

    def test_pause_when_match_appears(self):
        running = {"bash", "overwatch"}
        monitor, pause_cb, resume_cb, _ = self._make_monitor(
            snapshot=lambda: running,
        )

        matched = monitor.check_once()

        self.assertTrue(matched)
        self.assertTrue(monitor.paused)
        pause_cb.assert_called_once()
        resume_cb.assert_not_called()

    def test_no_pause_when_disabled(self):
        monitor, pause_cb, resume_cb, _ = self._make_monitor(
            enabled=False,
            snapshot=lambda: {"overwatch"},
        )

        matched = monitor.check_once()

        self.assertFalse(matched)
        self.assertFalse(monitor.paused)
        pause_cb.assert_not_called()
        resume_cb.assert_not_called()

    def test_no_pause_when_no_match(self):
        monitor, pause_cb, resume_cb, _ = self._make_monitor(
            snapshot=lambda: {"bash", "chrome"},
        )

        matched = monitor.check_once()

        self.assertFalse(matched)
        pause_cb.assert_not_called()

    def test_resume_when_match_clears(self):
        state = {"running": {"overwatch"}}
        monitor, pause_cb, resume_cb, _ = self._make_monitor(
            snapshot=lambda: state["running"],
        )

        monitor.check_once()
        pause_cb.assert_called_once()

        state["running"] = {"bash"}
        matched = monitor.check_once()

        self.assertFalse(matched)
        self.assertFalse(monitor.paused)
        resume_cb.assert_called_once()

    def test_no_double_pause(self):
        monitor, pause_cb, resume_cb, _ = self._make_monitor(
            snapshot=lambda: {"overwatch"},
        )

        monitor.check_once()
        monitor.check_once()

        pause_cb.assert_called_once()
        resume_cb.assert_not_called()

    def test_no_double_resume(self):
        state = {"running": {"overwatch"}}
        monitor, pause_cb, resume_cb, _ = self._make_monitor(
            snapshot=lambda: state["running"],
        )
        monitor.check_once()
        state["running"] = set()
        monitor.check_once()
        monitor.check_once()

        resume_cb.assert_called_once()

    def test_disabling_while_paused_resumes(self):
        state = {"enabled": True, "running": {"overwatch"}}
        pause_cb = MagicMock()
        resume_cb = MagicMock()

        def get_config():
            return state["enabled"], ["overwatch"], 5.0

        monitor = AutoPauseMonitor(
            get_config=get_config,
            on_pause=pause_cb,
            on_resume=resume_cb,
            process_snapshot=lambda: state["running"],
            use_glib=False,
        )
        monitor.check_once()
        pause_cb.assert_called_once()

        state["enabled"] = False
        monitor.check_once()
        resume_cb.assert_called_once()
        self.assertFalse(monitor.paused)

    def test_pause_callback_exception_does_not_raise(self):
        pause_cb = MagicMock(side_effect=RuntimeError("boom"))
        monitor = AutoPauseMonitor(
            get_config=lambda: (True, ["x"], 5.0),
            on_pause=pause_cb,
            process_snapshot=lambda: {"x"},
            use_glib=False,
        )
        # Should not raise
        monitor.check_once()
        self.assertTrue(monitor.paused)

    def test_start_stop_without_glib(self):
        monitor, _, _, _ = self._make_monitor()
        monitor.start()
        self.assertTrue(monitor.active)
        monitor.stop()
        self.assertFalse(monitor.active)
        monitor.shutdown()
        self.assertFalse(monitor.active)


class TestUnloadModelAndAutoPauseBlock(unittest.TestCase):
    """SpeechRecognitionManager.unload_model and start_recognition guard."""

    def _make_manager(self):
        from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager

        with patch.object(SpeechRecognitionManager, "__init__", lambda self: None):
            mgr = SpeechRecognitionManager()

        mgr.engine = "vosk"
        mgr.state = RecognitionState.IDLE
        mgr.model = MagicMock(name="model")
        mgr.recognizer = MagicMock(name="recognizer")
        mgr._model_initialized = True
        mgr._auto_paused = False
        mgr._model_lock = MagicMock()
        mgr._model_lock.__enter__ = MagicMock(return_value=None)
        mgr._model_lock.__exit__ = MagicMock(return_value=False)
        mgr._http_session = None
        mgr._reconnection_attempts = 0
        mgr._update_state = MagicMock()
        mgr._init_vosk = MagicMock()
        mgr._init_whisper = MagicMock()
        mgr._init_whispercpp = MagicMock()
        mgr._init_remote_api = MagicMock()
        mgr.stop_recognition = MagicMock()
        return mgr

    def test_unload_model_clears_resources_and_sets_flag(self):
        mgr = self._make_manager()

        mgr.unload_model()

        self.assertIsNone(mgr.model)
        self.assertIsNone(mgr.recognizer)
        self.assertFalse(mgr._model_initialized)
        self.assertTrue(mgr.is_auto_paused)
        mgr.stop_recognition.assert_not_called()  # already IDLE

    def test_unload_stops_active_recognition_first(self):
        mgr = self._make_manager()
        mgr.state = RecognitionState.LISTENING

        mgr.unload_model()

        mgr.stop_recognition.assert_called_once()
        self.assertTrue(mgr.is_auto_paused)

    def test_unload_closes_http_session(self):
        mgr = self._make_manager()
        session = MagicMock()
        mgr._http_session = session

        mgr.unload_model()

        session.close.assert_called_once()
        self.assertIsNone(mgr._http_session)

    def test_start_recognition_blocked_when_auto_paused(self):
        mgr = self._make_manager()
        mgr._auto_paused = True
        # model not ready either; auto-pause should win first
        with (
            patch("vocalinux.speech_recognition.recognition_manager.play_error_sound"),
            patch("vocalinux.speech_recognition.recognition_manager._show_notification"),
        ):
            mgr.start_recognition()

        self.assertEqual(mgr.state, RecognitionState.IDLE)
        # Should not have transitioned to listening
        mgr._update_state.assert_not_called()

    def test_reinitialize_clears_auto_pause_and_reloads(self):
        mgr = self._make_manager()
        mgr._auto_paused = True
        mgr.model = None
        mgr._model_initialized = False

        # Simulate successful reinit setting model ready
        def init_vosk():
            mgr.model = MagicMock()
            mgr._model_initialized = True

        mgr._init_vosk.side_effect = init_vosk

        mgr.reinitialize_after_resume()

        mgr._init_vosk.assert_called_once()
        self.assertFalse(mgr.is_auto_paused)
        self.assertIsNotNone(mgr.model)

    def test_pause_then_resume_via_monitor_and_engine(self):
        """End-to-end of the shipped path: match → unload → clear → reinit."""
        mgr = self._make_manager()
        state = {"running": {"overwatch"}}

        def on_pause():
            mgr.unload_model()

        def on_resume():
            def init_vosk():
                mgr.model = MagicMock()
                mgr._model_initialized = True

            mgr._init_vosk.side_effect = init_vosk
            mgr.reinitialize_after_resume()

        monitor = AutoPauseMonitor(
            get_config=lambda: (True, ["overwatch"], 5.0),
            on_pause=on_pause,
            on_resume=on_resume,
            process_snapshot=lambda: state["running"],
            use_glib=False,
        )

        monitor.check_once()
        self.assertTrue(mgr.is_auto_paused)
        self.assertIsNone(mgr.model)

        state["running"] = set()
        monitor.check_once()
        self.assertFalse(mgr.is_auto_paused)
        self.assertIsNotNone(mgr.model)
        self.assertTrue(mgr._model_initialized)


class TestAutoPauseConfigDefaults(unittest.TestCase):
    """DEFAULT_CONFIG schema for auto_pause section."""

    def test_default_config_has_auto_pause_section(self):
        self.assertIn("auto_pause", DEFAULT_CONFIG)
        section = DEFAULT_CONFIG["auto_pause"]
        self.assertFalse(section["enabled"])
        self.assertEqual(section["apps"], [])
        self.assertIn("poll_interval_seconds", section)

    def test_config_manager_round_trip_auto_pause(self):
        import json
        import tempfile
        from unittest.mock import patch

        from vocalinux.ui.config_manager import ConfigManager

        with tempfile.TemporaryDirectory() as tmp:
            config_dir = os.path.join(tmp, "vocalinux")
            config_file = os.path.join(config_dir, "config.json")
            os.makedirs(config_dir, exist_ok=True)

            with (
                patch("vocalinux.ui.config_manager.CONFIG_DIR", config_dir),
                patch("vocalinux.ui.config_manager.CONFIG_FILE", config_file),
            ):
                cm = ConfigManager()
                self.assertFalse(cm.get_bool("auto_pause", "enabled", True))
                self.assertEqual(cm.get("auto_pause", "apps", None), [])

                cm.set("auto_pause", "enabled", True)
                cm.set("auto_pause", "apps", ["Overwatch", "steam"])
                self.assertTrue(cm.save_config())

                cm2 = ConfigManager()
                self.assertTrue(cm2.get_bool("auto_pause", "enabled", False))
                self.assertEqual(cm2.get("auto_pause", "apps"), ["Overwatch", "steam"])

                with open(config_file) as f:
                    raw = json.load(f)
                self.assertIn("auto_pause", raw)
                self.assertEqual(raw["auto_pause"]["apps"], ["Overwatch", "steam"])


# Tray wiring tests live in test_suspend_handler.py (TestTrayAutoPauseWiring)
# so this module never imports tray_indicator and cannot pin a stale gi/GLib
# mock for later suite files.


if __name__ == "__main__":
    unittest.main()
