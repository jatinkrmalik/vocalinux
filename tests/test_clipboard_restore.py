"""Tests for _read_clipboard() and clipboard restore in _inject_via_clipboard_paste.

Covers the behaviour introduced in PR #588: before injecting text via the
ydotool clipboard-paste path, the existing clipboard content is saved and
restored ~300 ms after the Ctrl+V keystroke is sent.
"""

import os
import subprocess
import threading
import time
import unittest
from typing import Any, cast
from unittest.mock import MagicMock, patch


def _make_injector() -> Any:
    from vocalinux.text_injection.text_injector import DesktopEnvironment, TextInjector

    obj = cast(Any, TextInjector.__new__(TextInjector))
    obj._ibus_injector = None
    obj.environment = DesktopEnvironment.WAYLAND
    obj._session_environment = DesktopEnvironment.WAYLAND
    obj._ibus_ready = False
    obj._ibus_init_failed = False
    obj._ibus_init_thread = None
    obj._state_lock = threading.Lock()
    obj._clipboard_tool_health = {}
    obj._clipboard_timeout = 0.35
    return obj


class TestReadClipboard(unittest.TestCase):
    """Unit tests for the _read_clipboard() helper.

    subprocess.run is called with text=True so stdout is always a str.
    """

    def test_wl_paste_used_first_on_wayland(self):
        """On Wayland, wl-paste is the first candidate and its output is returned."""
        obj = _make_injector()
        with patch.dict(os.environ, {"WAYLAND_DISPLAY": "wayland-0"}):
            with patch("vocalinux.text_injection.text_injector.shutil.which") as mock_which:
                mock_which.side_effect = lambda cmd: (
                    "/usr/bin/wl-paste" if cmd == "wl-paste" else None
                )
                with patch("vocalinux.text_injection.text_injector.subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock(returncode=0, stdout="copied text")
                    result = obj._read_clipboard()
        self.assertEqual(result, "copied text")

    def test_xclip_fallback_when_wl_paste_unavailable(self):
        """Falls back to xclip when wl-paste is not installed."""
        obj = _make_injector()
        with patch("vocalinux.text_injection.text_injector.shutil.which") as mock_which:
            mock_which.side_effect = lambda cmd: ("/usr/bin/xclip" if cmd == "xclip" else None)
            with patch("vocalinux.text_injection.text_injector.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0, stdout="xclip text")
                result = obj._read_clipboard()
        self.assertEqual(result, "xclip text")

    def test_xsel_fallback_when_wl_paste_and_xclip_unavailable(self):
        """Falls back to xsel when wl-paste and xclip are both not installed."""
        obj = _make_injector()
        with patch("vocalinux.text_injection.text_injector.shutil.which") as mock_which:
            mock_which.side_effect = lambda cmd: ("/usr/bin/xsel" if cmd == "xsel" else None)
            with patch("vocalinux.text_injection.text_injector.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0, stdout="xsel text")
                result = obj._read_clipboard()
        self.assertEqual(result, "xsel text")

    def test_returns_none_when_no_tool_installed(self):
        """Returns None when no clipboard read tool is available."""
        obj = _make_injector()
        with patch("vocalinux.text_injection.text_injector.shutil.which", return_value=None):
            result = obj._read_clipboard()
        self.assertIsNone(result)

    def test_returns_none_when_tool_exits_nonzero(self):
        """Returns None when the tool exits with a non-zero code (e.g. clipboard empty)."""
        obj = _make_injector()
        with patch.dict(os.environ, {"WAYLAND_DISPLAY": "wayland-0"}):
            with patch(
                "vocalinux.text_injection.text_injector.shutil.which",
                return_value="/usr/bin/wl-paste",
            ):
                with patch("vocalinux.text_injection.text_injector.subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock(returncode=1, stdout="")
                    result = obj._read_clipboard()
        self.assertIsNone(result)

    def test_returns_none_and_does_not_raise_on_timeout(self):
        """Returns None without raising when the clipboard tool times out."""
        obj = _make_injector()
        with patch.dict(os.environ, {"WAYLAND_DISPLAY": "wayland-0"}):
            with patch(
                "vocalinux.text_injection.text_injector.shutil.which",
                return_value="/usr/bin/wl-paste",
            ):
                with patch(
                    "vocalinux.text_injection.text_injector.subprocess.run",
                    side_effect=subprocess.TimeoutExpired("wl-paste", 1.0),
                ):
                    result = obj._read_clipboard()
        self.assertIsNone(result)

    def test_returns_none_and_does_not_raise_on_oserror(self):
        """Returns None without raising when subprocess raises OSError."""
        obj = _make_injector()
        with patch.dict(os.environ, {"WAYLAND_DISPLAY": "wayland-0"}):
            with patch(
                "vocalinux.text_injection.text_injector.shutil.which",
                return_value="/usr/bin/wl-paste",
            ):
                with patch(
                    "vocalinux.text_injection.text_injector.subprocess.run",
                    side_effect=OSError("not found"),
                ):
                    result = obj._read_clipboard()
        self.assertIsNone(result)

    def test_tries_next_tool_after_failure(self):
        """When the first tool fails, the next candidate is tried."""
        obj = _make_injector()
        with patch("vocalinux.text_injection.text_injector.shutil.which") as mock_which:
            mock_which.side_effect = lambda cmd: (
                "/usr/bin/" + cmd if cmd in ("wl-paste", "xclip") else None
            )
            with patch("vocalinux.text_injection.text_injector.subprocess.run") as mock_run:
                mock_run.side_effect = [
                    MagicMock(returncode=1, stdout=""),  # wl-paste fails
                    MagicMock(returncode=0, stdout="via xclip"),  # xclip succeeds
                ]
                result = obj._read_clipboard()
        self.assertEqual(result, "via xclip")

    def test_returns_arabic_text(self):
        """Correctly returns multi-byte UTF-8 content such as Arabic text."""
        obj = _make_injector()
        arabic = "مرحبا بالعالم"
        with patch.dict(os.environ, {"WAYLAND_DISPLAY": "wayland-0"}):
            with patch(
                "vocalinux.text_injection.text_injector.shutil.which",
                return_value="/usr/bin/wl-paste",
            ):
                with patch("vocalinux.text_injection.text_injector.subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock(returncode=0, stdout=arabic)
                    result = obj._read_clipboard()
        self.assertEqual(result, arabic)


class TestClipboardRestoreAfterInjection(unittest.TestCase):
    """Behavioural tests for the save/restore logic in _inject_via_clipboard_paste."""

    def test_clipboard_restored_to_previous_content(self):
        """Previous clipboard content is written back ~300ms after injection."""
        obj = _make_injector()
        obj.wayland_tool = "ydotool"
        copy_calls: list[str] = []

        with patch.object(obj, "_read_clipboard", return_value="original clipboard"):
            with patch.object(
                obj, "_copy_to_clipboard", side_effect=lambda t: copy_calls.append(t) or True
            ):
                with patch.object(
                    obj,
                    "_ydotool_ctrl_v_command",
                    return_value=["ydotool", "key", "ctrl+v"],
                ):
                    with patch.object(obj, "_should_copy_to_clipboard", return_value=False):
                        with patch(
                            "vocalinux.text_injection.text_injector.subprocess.run",
                            return_value=MagicMock(returncode=0),
                        ):
                            result = obj._inject_via_clipboard_paste("injected text")
                            time.sleep(0.5)  # wait for the 300ms restore thread

        self.assertTrue(result)
        self.assertEqual(copy_calls[0], "injected text")
        self.assertEqual(copy_calls[-1], "original clipboard")

    def test_read_clipboard_is_called_before_overwriting(self):
        """_read_clipboard must be called first, before _copy_to_clipboard."""
        obj = _make_injector()
        obj.wayland_tool = "ydotool"
        call_order: list[str] = []

        with patch.object(
            obj,
            "_read_clipboard",
            side_effect=lambda: call_order.append("read") or "prev",
        ):
            with patch.object(
                obj,
                "_copy_to_clipboard",
                side_effect=lambda t: call_order.append(f"copy:{t}") or True,
            ):
                with patch.object(
                    obj,
                    "_ydotool_ctrl_v_command",
                    return_value=["ydotool", "key", "ctrl+v"],
                ):
                    with patch.object(obj, "_should_copy_to_clipboard", return_value=False):
                        with patch(
                            "vocalinux.text_injection.text_injector.subprocess.run",
                            return_value=MagicMock(returncode=0),
                        ):
                            obj._inject_via_clipboard_paste("text")
                            time.sleep(0.5)

        self.assertEqual(call_order[0], "read", "read must happen before any copy")
        self.assertIn("copy:text", call_order)

    def test_no_restore_when_clipboard_was_empty(self):
        """No restore is attempted when _read_clipboard() returns None (clipboard empty)."""
        obj = _make_injector()
        obj.wayland_tool = "ydotool"
        copy_calls: list[str] = []

        with patch.object(obj, "_read_clipboard", return_value=None):
            with patch.object(
                obj,
                "_copy_to_clipboard",
                side_effect=lambda t: copy_calls.append(t) or True,
            ):
                with patch.object(
                    obj,
                    "_ydotool_ctrl_v_command",
                    return_value=["ydotool", "key", "ctrl+v"],
                ):
                    with patch.object(obj, "_should_copy_to_clipboard", return_value=False):
                        with patch(
                            "vocalinux.text_injection.text_injector.subprocess.run",
                            return_value=MagicMock(returncode=0),
                        ):
                            result = obj._inject_via_clipboard_paste("text")
                            time.sleep(0.5)

        self.assertTrue(result)
        # Only one call: the injection. No second call for restore.
        self.assertEqual(copy_calls, ["text"])

    def test_no_restore_when_copy_to_clipboard_setting_enabled(self):
        """No restore when the user has opted-in to keeping dictated text in clipboard.

        When copy_to_clipboard=true, the user explicitly wants the dictated text
        to stay in the clipboard after injection. Restoring the old content would
        silently undo that preference.
        """
        obj = _make_injector()
        obj.wayland_tool = "ydotool"
        copy_calls: list[str] = []

        with patch.object(obj, "_read_clipboard", return_value="old clipboard"):
            with patch.object(
                obj,
                "_copy_to_clipboard",
                side_effect=lambda t: copy_calls.append(t) or True,
            ):
                with patch.object(
                    obj,
                    "_ydotool_ctrl_v_command",
                    return_value=["ydotool", "key", "ctrl+v"],
                ):
                    with patch.object(obj, "_should_copy_to_clipboard", return_value=True):
                        with patch(
                            "vocalinux.text_injection.text_injector.subprocess.run",
                            return_value=MagicMock(returncode=0),
                        ):
                            result = obj._inject_via_clipboard_paste("dictated text")
                            time.sleep(0.5)

        self.assertTrue(result)
        # Only one copy call — the injection. The old content must NOT be restored.
        self.assertEqual(copy_calls, ["dictated text"])

    def test_no_restore_when_ctrl_v_fails(self):
        """No restore thread is started when the Ctrl+V simulation itself fails."""
        obj = _make_injector()
        obj.wayland_tool = "ydotool"
        copy_calls: list[str] = []

        with patch.object(obj, "_read_clipboard", return_value="prev"):
            with patch.object(
                obj,
                "_copy_to_clipboard",
                side_effect=lambda t: copy_calls.append(t) or True,
            ):
                with patch.object(
                    obj,
                    "_ydotool_ctrl_v_command",
                    return_value=["ydotool", "key", "ctrl+v"],
                ):
                    with patch(
                        "vocalinux.text_injection.text_injector.subprocess.run",
                        side_effect=subprocess.CalledProcessError(1, ["ydotool", "key"]),
                    ):
                        result = obj._inject_via_clipboard_paste("text")
                        time.sleep(0.5)

        self.assertFalse(result)
        # Text was copied to clipboard but restore must NOT happen: paste failed.
        self.assertEqual(copy_calls, ["text"])

    def test_restore_thread_is_a_daemon(self):
        """The restore thread is a daemon so it never blocks interpreter shutdown."""
        obj = _make_injector()
        obj.wayland_tool = "ydotool"
        started: list[threading.Thread] = []
        original_start = threading.Thread.start

        def capture_start(self_t: threading.Thread) -> None:
            started.append(self_t)
            original_start(self_t)

        with patch.object(obj, "_read_clipboard", return_value="prev"):
            with patch.object(obj, "_copy_to_clipboard", return_value=True):
                with patch.object(
                    obj,
                    "_ydotool_ctrl_v_command",
                    return_value=["ydotool", "key", "ctrl+v"],
                ):
                    with patch.object(obj, "_should_copy_to_clipboard", return_value=False):
                        with patch(
                            "vocalinux.text_injection.text_injector.subprocess.run",
                            return_value=MagicMock(returncode=0),
                        ):
                            with patch.object(threading.Thread, "start", capture_start):
                                obj._inject_via_clipboard_paste("text")

        self.assertEqual(len(started), 1, "exactly one restore thread should start")
        self.assertTrue(started[0].daemon, "restore thread must be a daemon")

    def test_arabic_content_is_preserved(self):
        """Clipboard content containing Arabic text is correctly restored."""
        obj = _make_injector()
        obj.wayland_tool = "ydotool"
        copy_calls: list[str] = []
        arabic_previous = "نص عربي سابق"

        with patch.object(obj, "_read_clipboard", return_value=arabic_previous):
            with patch.object(
                obj,
                "_copy_to_clipboard",
                side_effect=lambda t: copy_calls.append(t) or True,
            ):
                with patch.object(
                    obj,
                    "_ydotool_ctrl_v_command",
                    return_value=["ydotool", "key", "ctrl+v"],
                ):
                    with patch.object(obj, "_should_copy_to_clipboard", return_value=False):
                        with patch(
                            "vocalinux.text_injection.text_injector.subprocess.run",
                            return_value=MagicMock(returncode=0),
                        ):
                            obj._inject_via_clipboard_paste("مرحبا")
                            time.sleep(0.5)

        self.assertEqual(copy_calls[-1], arabic_previous)


if __name__ == "__main__":
    unittest.main()
