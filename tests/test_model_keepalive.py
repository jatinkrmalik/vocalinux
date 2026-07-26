"""Tests for model keep-alive idle unload helper."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from vocalinux.model_keepalive import (
    DEFAULT_IDLE_TIMEOUT_SECONDS,
    ModelKeepAlive,
    clamp_idle_timeout,
)
from vocalinux.ui.config_manager import DEFAULT_CONFIG


class TestClampIdleTimeout(unittest.TestCase):
    def test_clamps_low_and_high(self):
        self.assertEqual(clamp_idle_timeout(10), 60)
        self.assertEqual(clamp_idle_timeout(99999), 3600)
        self.assertEqual(clamp_idle_timeout(300), 300)

    def test_invalid_falls_back_to_default(self):
        self.assertEqual(clamp_idle_timeout("nope"), float(DEFAULT_IDLE_TIMEOUT_SECONDS))
        self.assertEqual(clamp_idle_timeout(None), float(DEFAULT_IDLE_TIMEOUT_SECONDS))


class TestModelKeepAlive(unittest.TestCase):
    def test_bump_when_disabled_cancels(self):
        fired = []
        ka = ModelKeepAlive(
            get_config=lambda: (False, 300),
            on_idle_unload=lambda: fired.append(1),
            use_glib=False,
        )
        ka.start()
        ka.bump()
        self.assertFalse(ka.armed)
        self.assertFalse(ka.fire_if_due())
        self.assertEqual(fired, [])

    def test_bump_arms_and_fire_unloads(self):
        fired = []
        ka = ModelKeepAlive(
            get_config=lambda: (True, 300),
            on_idle_unload=lambda: fired.append(1),
            is_safe_to_unload=lambda: True,
            use_glib=False,
        )
        ka.start()
        ka.bump()
        self.assertTrue(ka.armed)
        self.assertTrue(ka.fire_if_due())
        self.assertEqual(fired, [1])
        self.assertFalse(ka.armed)
        # Second fire without re-arm is a no-op
        self.assertFalse(ka.fire_if_due())

    def test_cancel_prevents_fire(self):
        fired = []
        ka = ModelKeepAlive(
            get_config=lambda: (True, 120),
            on_idle_unload=lambda: fired.append(1),
            use_glib=False,
        )
        ka.start()
        ka.bump()
        ka.cancel()
        self.assertFalse(ka.armed)
        self.assertFalse(ka.fire_if_due())
        self.assertEqual(fired, [])

    def test_unsafe_predicate_skips_unload(self):
        fired = []
        ka = ModelKeepAlive(
            get_config=lambda: (True, 120),
            on_idle_unload=lambda: fired.append(1),
            is_safe_to_unload=lambda: False,
            use_glib=False,
        )
        ka.start()
        ka.bump()
        self.assertFalse(ka.fire_if_due())
        self.assertEqual(fired, [])

    def test_callback_error_is_swallowed(self):
        def boom():
            raise RuntimeError("unload failed")

        ka = ModelKeepAlive(
            get_config=lambda: (True, 120),
            on_idle_unload=boom,
            is_safe_to_unload=lambda: True,
            use_glib=False,
        )
        ka.start()
        ka.bump()
        self.assertFalse(ka.fire_if_due())

    def test_config_error_disables(self):
        def bad_config():
            raise RuntimeError("config boom")

        ka = ModelKeepAlive(get_config=bad_config, use_glib=False)
        ka.start()
        ka.bump()
        self.assertFalse(ka.armed)

    def test_stop_and_shutdown(self):
        ka = ModelKeepAlive(get_config=lambda: (True, 120), use_glib=False)
        ka.start()
        ka.bump()
        ka.shutdown()
        self.assertFalse(ka.active)
        self.assertFalse(ka.armed)

    def test_start_idempotent(self):
        ka = ModelKeepAlive(get_config=lambda: (True, 120), use_glib=False)
        ka.start()
        ka.start()
        self.assertTrue(ka.active)

    @patch("gi.repository.GLib")
    def test_glib_schedule_and_timeout(self, mock_glib):
        mock_glib.timeout_add_seconds.return_value = 42
        fired = []
        ka = ModelKeepAlive(
            get_config=lambda: (True, 90),
            on_idle_unload=lambda: fired.append(1),
            is_safe_to_unload=lambda: True,
            use_glib=True,
        )
        ka.start()
        ka.bump()
        mock_glib.timeout_add_seconds.assert_called()
        # Invoke the scheduled callback
        cb = mock_glib.timeout_add_seconds.call_args[0][1]
        self.assertFalse(cb())
        self.assertEqual(fired, [1])

    def test_default_config_section(self):
        self.assertIn("model_keepalive", DEFAULT_CONFIG)
        self.assertFalse(DEFAULT_CONFIG["model_keepalive"]["enabled"])


if __name__ == "__main__":
    unittest.main()
