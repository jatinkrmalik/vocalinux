"""Regression tests for issue #474.

On Wayland, Vocalinux must not call ``setxkbmap``. It only reaches the XWayland
X11 server, so re-applying a layout there leaves XWayland (and XWayland/Electron
apps) on the wrong layout while native Wayland apps and ``localectl`` stay
correct — the "layout flips from de to us after dictation" symptom.
"""

import sys
import unittest
from unittest.mock import MagicMock, patch

# Mock GI so importing ibus_engine does not require a real IBus/GTK stack.
_mock_gi = MagicMock()
_mock_gi_repo = MagicMock()
_mock_gi_repo.IBus = MagicMock()
_mock_gi_repo.GLib = MagicMock()
_mock_gi_repo.GObject = MagicMock()
_mock_gi_repo.IBus.Engine = MagicMock
_mock_gi_repo.GLib.MainLoop = MagicMock
sys.modules["gi"] = _mock_gi
sys.modules["gi.repository"] = _mock_gi_repo

for _key in list(sys.modules.keys()):
    if "vocalinux" in _key and "ibus_engine" in _key:
        del sys.modules[_key]

from vocalinux.text_injection.ibus_engine import restore_xkb_layout  # noqa: E402


class TestRestoreXkbLayoutWayland(unittest.TestCase):
    """restore_xkb_layout must be a no-op on Wayland (issue #474)."""

    @patch("vocalinux.text_injection.ibus_engine.subprocess.run")
    @patch.dict("os.environ", {"XDG_SESSION_TYPE": "wayland"}, clear=True)
    def test_wayland_does_not_call_setxkbmap(self, mock_run):
        self.assertFalse(restore_xkb_layout("de"))
        mock_run.assert_not_called()

    @patch("vocalinux.text_injection.ibus_engine.subprocess.run")
    @patch.dict("os.environ", {"XDG_SESSION_TYPE": "x11"}, clear=True)
    def test_x11_still_restores_layout(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        self.assertTrue(restore_xkb_layout("de"))
        cmds = [c.args[0] for c in mock_run.call_args_list if c.args]
        self.assertTrue(
            any(c[:3] == ["setxkbmap", "-layout", "de"] for c in cmds),
            "X11 should still apply the captured layout",
        )

    @patch("vocalinux.text_injection.ibus_engine.subprocess.run")
    @patch.dict("os.environ", {"XDG_SESSION_TYPE": "x11"}, clear=True)
    def test_empty_layout_is_noop(self, mock_run):
        self.assertFalse(restore_xkb_layout(""))
        mock_run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
