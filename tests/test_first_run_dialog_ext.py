"""
Final execution-based tests for FirstRunDialog.

These tests focus on actually exercising the code with proper mocking.
"""

import sys
import unittest
from unittest.mock import MagicMock, patch

# Mock gi and Gtk before importing first_run_dialog
mock_gi = MagicMock()
mock_gtk = MagicMock()
sys.modules["gi"] = mock_gi
sys.modules["gi.repository"] = MagicMock()
sys.modules["gi.repository.Gtk"] = mock_gtk


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
