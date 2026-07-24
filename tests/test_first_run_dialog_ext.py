"""
Final execution-based tests for FirstRunDialog.

These tests focus on actually exercising the code with proper mocking.
"""

import importlib
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

# Mock gi and Gtk before importing first_run_dialog.
# Gtk.Dialog must be a real type so FirstRunDialog is a real class (needed to
# call FirstRunDialog._on_response without constructing a dialog).
mock_gi = MagicMock()
mock_gtk = MagicMock()
mock_gtk.Dialog = type("GtkDialog", (), {})
mock_repo = MagicMock()
mock_repo.Gtk = mock_gtk
sys.modules["gi"] = mock_gi
sys.modules["gi.repository"] = mock_repo
sys.modules["gi.repository.Gtk"] = mock_gtk


def _install_gi_mocks():
    """Ensure Gtk.Dialog is a real base type for FirstRunDialog."""
    mock_gi_local = MagicMock()
    mock_gtk_local = MagicMock()
    mock_gtk_local.Dialog = type("GtkDialog", (), {})
    mock_repo_local = MagicMock()
    mock_repo_local.Gtk = mock_gtk_local
    sys.modules["gi"] = mock_gi_local
    sys.modules["gi.repository"] = mock_repo_local
    sys.modules["gi.repository.Gtk"] = mock_gtk_local


def _first_run_dialog_class():
    """Return FirstRunDialog as a real class (reload if suite left a MagicMock)."""
    import vocalinux.ui.first_run_dialog as mod

    if not isinstance(mod.FirstRunDialog, type):
        _install_gi_mocks()
        mod = importlib.reload(mod)
    return mod.FirstRunDialog


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
    """Tests for _on_response mapping without constructing Gtk.Dialog."""

    def _handler_target(self):
        from vocalinux.ui.first_run_dialog import RESPONSE_LATER, RESPONSE_NO, RESPONSE_YES

        return SimpleNamespace(
            _response_map={
                RESPONSE_YES: "yes",
                RESPONSE_NO: "no",
                RESPONSE_LATER: "later",
            },
            result=None,
        )

    def test_on_response_maps_yes(self):
        """YES response maps to 'yes'."""
        from vocalinux.ui.first_run_dialog import RESPONSE_YES

        obj = self._handler_target()
        _first_run_dialog_class()._on_response(obj, obj, RESPONSE_YES)
        self.assertEqual(obj.result, "yes")

    def test_on_response_maps_no(self):
        """NO response maps to 'no'."""
        from vocalinux.ui.first_run_dialog import RESPONSE_NO

        obj = self._handler_target()
        _first_run_dialog_class()._on_response(obj, obj, RESPONSE_NO)
        self.assertEqual(obj.result, "no")

    def test_on_response_maps_later(self):
        """LATER response maps to 'later'."""
        from vocalinux.ui.first_run_dialog import RESPONSE_LATER

        obj = self._handler_target()
        _first_run_dialog_class()._on_response(obj, obj, RESPONSE_LATER)
        self.assertEqual(obj.result, "later")

    def test_on_response_unknown_id_is_none(self):
        """Unknown response IDs map to None via dict.get default."""
        obj = self._handler_target()
        obj.result = "yes"
        _first_run_dialog_class()._on_response(obj, obj, 99999)
        self.assertIsNone(obj.result)


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
