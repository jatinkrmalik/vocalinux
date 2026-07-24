"""
Final execution-based tests for FirstRunDialog.

These tests focus on actually exercising the code with proper mocking.
"""

import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Mock gi and Gtk before importing first_run_dialog (constants / show_* tests).
# Response-handler tests reinstall a real Dialog base and reload the module so
# they stay correct even when earlier tests left FirstRunDialog as a MagicMock.
mock_gi = MagicMock()
mock_gtk = MagicMock()
sys.modules["gi"] = mock_gi
sys.modules["gi.repository"] = MagicMock()
sys.modules["gi.repository.Gtk"] = mock_gtk


class _FakeGtkDialog:
    """Minimal Gtk.Dialog stand-in for unit tests."""

    def __init__(self, *args, **kwargs):
        self._connect_calls = []

    def set_default_size(self, *args, **kwargs):
        pass

    def connect(self, *args, **kwargs):
        self._connect_calls.append((args, kwargs))
        return 0

    def get_content_area(self):
        return MagicMock()

    def add_button(self, *args, **kwargs):
        return MagicMock()

    def get_action_area(self):
        return MagicMock()

    def show_all(self):
        pass


_ISOLATED_MODULE_NAME = "vocalinux_test_first_run_dialog_isolated"


def _load_first_run_dialog_with_fake_gtk():
    """Load first_run_dialog.py under an isolated module name with a real Dialog base.

    Other test modules often leave gi/Gtk/FirstRunDialog as MagicMocks. Loading
    the source file under a unique name (and restoring gi afterward) lets
    __init__ / _on_response run without clobbering the suite's import graph.
    Coverage still attributes execution to first_run_dialog.py by file path.
    """
    mock_gi_local = MagicMock()
    mock_gtk_local = MagicMock()
    mock_gtk_local.Dialog = _FakeGtkDialog
    mock_gtk_local.DialogFlags.MODAL = 1
    mock_gtk_local.ResponseType.DELETE_EVENT = -4
    mock_gtk_local.Justification.CENTER = 0
    mock_gtk_local.Justification.LEFT = 1
    mock_gtk_local.Orientation.HORIZONTAL = 0
    mock_gtk_local.Align.CENTER = 0
    mock_gtk_local.Label = MagicMock
    mock_gtk_local.Box = MagicMock
    mock_gtk_local.Window = MagicMock

    mock_repo = types.ModuleType("gi.repository")
    mock_repo.Gtk = mock_gtk_local

    gi_keys = ("gi", "gi.repository", "gi.repository.Gtk")
    saved = {key: sys.modules.get(key) for key in gi_keys}
    try:
        sys.modules["gi"] = mock_gi_local
        sys.modules["gi.repository"] = mock_repo
        sys.modules["gi.repository.Gtk"] = mock_gtk_local

        path = (
            Path(__file__).resolve().parents[1] / "src" / "vocalinux" / "ui" / "first_run_dialog.py"
        )
        spec = importlib.util.spec_from_file_location(_ISOLATED_MODULE_NAME, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[_ISOLATED_MODULE_NAME] = module
        assert spec.loader is not None
        spec.loader.exec_module(module)
        return module
    finally:
        for key, previous in saved.items():
            if previous is None:
                sys.modules.pop(key, None)
            else:
                sys.modules[key] = previous


class TestFirstRunDialogConstants(unittest.TestCase):
    """Tests for FirstRunDialog constants."""

    def test_response_yes_constant(self):
        """Test that RESPONSE_YES constant is defined."""
        from vocalinux.ui.first_run_dialog import RESPONSE_YES

        self.assertEqual(RESPONSE_YES, 1)

    def test_response_no_constant(self):
        """Test that RESPONSE_NO constant is defined."""
        from vocalinux.ui.first_run_dialog import RESPONSE_NO

        self.assertEqual(RESPONSE_NO, 2)

    def test_response_later_constant(self):
        """Test that RESPONSE_LATER constant is defined."""
        from vocalinux.ui.first_run_dialog import RESPONSE_LATER

        self.assertEqual(RESPONSE_LATER, 3)

    def test_response_constants_are_distinct(self):
        """Test that response constants have unique values."""
        from vocalinux.ui.first_run_dialog import RESPONSE_LATER, RESPONSE_NO, RESPONSE_YES

        constants = [RESPONSE_YES, RESPONSE_NO, RESPONSE_LATER]
        self.assertEqual(len(constants), len(set(constants)))


class TestFirstRunDialogResponseHandler(unittest.TestCase):
    """Tests for response signal wiring and _on_response mapping."""

    @classmethod
    def setUpClass(cls):
        cls.mod = _load_first_run_dialog_with_fake_gtk()
        cls.FirstRunDialog = cls.mod.FirstRunDialog
        cls.RESPONSE_YES = cls.mod.RESPONSE_YES
        cls.RESPONSE_NO = cls.mod.RESPONSE_NO
        cls.RESPONSE_LATER = cls.mod.RESPONSE_LATER

    @classmethod
    def tearDownClass(cls):
        sys.modules.pop(_ISOLATED_MODULE_NAME, None)

    def test_connects_response_signal_to_handler(self):
        """Constructor wires the response signal instead of do_response."""
        dialog = self.FirstRunDialog()

        self.assertTrue(dialog._connect_calls)
        signal_name, handler = dialog._connect_calls[0][0][:2]
        self.assertEqual(signal_name, "response")
        self.assertTrue(callable(handler))
        # Bound method of this instance (each attribute access makes a new object)
        self.assertIs(handler.__self__, dialog)
        self.assertIs(handler.__func__, self.FirstRunDialog._on_response)

    def test_on_response_maps_yes(self):
        """YES response maps to 'yes'."""
        dialog = self.FirstRunDialog()
        dialog._on_response(dialog, self.RESPONSE_YES)
        self.assertEqual(dialog.result, "yes")

    def test_on_response_maps_no(self):
        """NO response maps to 'no'."""
        dialog = self.FirstRunDialog()
        dialog._on_response(dialog, self.RESPONSE_NO)
        self.assertEqual(dialog.result, "no")

    def test_on_response_maps_later(self):
        """LATER response maps to 'later'."""
        dialog = self.FirstRunDialog()
        dialog._on_response(dialog, self.RESPONSE_LATER)
        self.assertEqual(dialog.result, "later")

    def test_on_response_maps_delete_event_to_none(self):
        """DELETE_EVENT maps to None (dialog closed without a choice)."""
        dialog = self.FirstRunDialog()
        dialog.result = "yes"  # ensure handler overwrites prior value
        dialog._on_response(dialog, self.mod.Gtk.ResponseType.DELETE_EVENT)
        self.assertIsNone(dialog.result)

    def test_on_response_unknown_id_is_none(self):
        """Unknown response IDs map to None via dict.get default."""
        dialog = self.FirstRunDialog()
        dialog.result = "yes"
        dialog._on_response(dialog, 99999)
        self.assertIsNone(dialog.result)

    def test_on_response_matches_response_map(self):
        """Each entry in _response_map is applied by _on_response."""
        dialog = self.FirstRunDialog()
        for response_id, expected in dialog._response_map.items():
            dialog._on_response(dialog, response_id)
            self.assertEqual(dialog.result, expected)


class TestShowFirstRunDialogFunction(unittest.TestCase):
    """Tests for show_first_run_dialog function."""

    def test_show_first_run_dialog_function_exists(self):
        """Test that show_first_run_dialog function exists."""
        from vocalinux.ui.first_run_dialog import show_first_run_dialog

        self.assertIsNotNone(show_first_run_dialog)
        self.assertTrue(callable(show_first_run_dialog))

    @patch("vocalinux.ui.first_run_dialog.FirstRunDialog")
    def test_show_first_run_dialog_creates_dialog(self, mock_dialog_class):
        """Test that show_first_run_dialog creates a FirstRunDialog."""
        from vocalinux.ui.first_run_dialog import show_first_run_dialog

        mock_dialog = MagicMock()
        mock_dialog.result = "yes"
        mock_dialog_class.return_value = mock_dialog

        show_first_run_dialog()

        mock_dialog_class.assert_called_once()

    @patch("vocalinux.ui.first_run_dialog.FirstRunDialog")
    def test_show_first_run_dialog_runs_dialog(self, mock_dialog_class):
        """Test that show_first_run_dialog calls run()."""
        from vocalinux.ui.first_run_dialog import show_first_run_dialog

        mock_dialog = MagicMock()
        mock_dialog.result = "yes"
        mock_dialog_class.return_value = mock_dialog

        show_first_run_dialog()

        mock_dialog.run.assert_called_once()

    @patch("vocalinux.ui.first_run_dialog.FirstRunDialog")
    def test_show_first_run_dialog_destroys_dialog(self, mock_dialog_class):
        """Test that show_first_run_dialog calls destroy()."""
        from vocalinux.ui.first_run_dialog import show_first_run_dialog

        mock_dialog = MagicMock()
        mock_dialog.result = "yes"
        mock_dialog_class.return_value = mock_dialog

        show_first_run_dialog()

        mock_dialog.destroy.assert_called_once()

    @patch("vocalinux.ui.first_run_dialog.FirstRunDialog")
    def test_show_first_run_dialog_returns_result_yes(self, mock_dialog_class):
        """Test that show_first_run_dialog returns 'yes'."""
        from vocalinux.ui.first_run_dialog import show_first_run_dialog

        mock_dialog = MagicMock()
        mock_dialog.result = "yes"
        mock_dialog_class.return_value = mock_dialog

        result = show_first_run_dialog()

        self.assertEqual(result, "yes")

    @patch("vocalinux.ui.first_run_dialog.FirstRunDialog")
    def test_show_first_run_dialog_returns_result_no(self, mock_dialog_class):
        """Test that show_first_run_dialog returns 'no'."""
        from vocalinux.ui.first_run_dialog import show_first_run_dialog

        mock_dialog = MagicMock()
        mock_dialog.result = "no"
        mock_dialog_class.return_value = mock_dialog

        result = show_first_run_dialog()

        self.assertEqual(result, "no")

    @patch("vocalinux.ui.first_run_dialog.FirstRunDialog")
    def test_show_first_run_dialog_returns_result_later(self, mock_dialog_class):
        """Test that show_first_run_dialog returns 'later'."""
        from vocalinux.ui.first_run_dialog import show_first_run_dialog

        mock_dialog = MagicMock()
        mock_dialog.result = "later"
        mock_dialog_class.return_value = mock_dialog

        result = show_first_run_dialog()

        self.assertEqual(result, "later")

    @patch("vocalinux.ui.first_run_dialog.FirstRunDialog")
    def test_show_first_run_dialog_returns_result_none(self, mock_dialog_class):
        """Test that show_first_run_dialog returns None."""
        from vocalinux.ui.first_run_dialog import show_first_run_dialog

        mock_dialog = MagicMock()
        mock_dialog.result = None
        mock_dialog_class.return_value = mock_dialog

        result = show_first_run_dialog()

        self.assertIsNone(result)

    @patch("vocalinux.ui.first_run_dialog.FirstRunDialog")
    def test_show_first_run_dialog_with_parent(self, mock_dialog_class):
        """Test that show_first_run_dialog accepts parent window."""
        from vocalinux.ui.first_run_dialog import show_first_run_dialog

        mock_dialog = MagicMock()
        mock_dialog.result = "yes"
        mock_dialog_class.return_value = mock_dialog
        mock_parent = MagicMock()

        result = show_first_run_dialog(parent=mock_parent)

        # Dialog class should be called with parent argument
        self.assertEqual(result, "yes")
        self.assertTrue(mock_dialog_class.called)


if __name__ == "__main__":
    unittest.main()
