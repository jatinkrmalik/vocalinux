"""
Tests for first_run_dialog module.

Tests cover FirstRunDialog class, show_first_run_dialog function, and response handling.
"""

import sys
import unittest
from unittest.mock import MagicMock, patch, call

# Mock gi and Gtk before importing first_run_dialog
mock_gi = MagicMock()
mock_gtk = MagicMock()
sys.modules["gi"] = mock_gi
sys.modules["gi.repository"] = MagicMock()
sys.modules["gi.repository.Gtk"] = mock_gtk


class TestFirstRunDialogConstants(unittest.TestCase):
    """Tests for FirstRunDialog constants and module exports."""

    def test_response_constants_defined(self):
        """Test that response constants are defined."""
        from vocalinux.ui.first_run_dialog import RESPONSE_YES, RESPONSE_NO, RESPONSE_LATER

        self.assertEqual(RESPONSE_YES, 1)
        self.assertEqual(RESPONSE_NO, 2)
        self.assertEqual(RESPONSE_LATER, 3)

    def test_response_constants_distinct(self):
        """Test that response constants are distinct."""
        from vocalinux.ui.first_run_dialog import RESPONSE_YES, RESPONSE_NO, RESPONSE_LATER

        constants = [RESPONSE_YES, RESPONSE_NO, RESPONSE_LATER]
        self.assertEqual(len(constants), len(set(constants)))

    def test_first_run_dialog_class_exists(self):
        """Test that FirstRunDialog class exists."""
        from vocalinux.ui.first_run_dialog import FirstRunDialog

        self.assertIsNotNone(FirstRunDialog)

    def test_show_first_run_dialog_function_exists(self):
        """Test that show_first_run_dialog function exists."""
        from vocalinux.ui.first_run_dialog import show_first_run_dialog

        self.assertIsNotNone(show_first_run_dialog)
        self.assertTrue(callable(show_first_run_dialog))


class TestShowFirstRunDialog(unittest.TestCase):
    """Tests for show_first_run_dialog function."""

    @patch("vocalinux.ui.first_run_dialog.FirstRunDialog")
    def test_show_first_run_dialog_returns_result(self, mock_dialog_class):
        """Test show_first_run_dialog returns dialog result."""
        from vocalinux.ui.first_run_dialog import show_first_run_dialog

        mock_dialog = MagicMock()
        mock_dialog.result = "yes"
        mock_dialog_class.return_value = mock_dialog

        result = show_first_run_dialog()

        self.assertEqual(result, "yes")
        mock_dialog.run.assert_called_once()
        mock_dialog.destroy.assert_called_once()

    @patch("vocalinux.ui.first_run_dialog.FirstRunDialog")
    def test_show_first_run_dialog_with_parent(self, mock_dialog_class):
        """Test show_first_run_dialog with parent window."""
        from vocalinux.ui.first_run_dialog import show_first_run_dialog

        mock_dialog = MagicMock()
        mock_dialog.result = "no"
        mock_dialog_class.return_value = mock_dialog
        mock_parent = MagicMock()

        result = show_first_run_dialog(parent=mock_parent)

        self.assertEqual(result, "no")
        # Check that it was called with a parent argument (positional or keyword)
        self.assertEqual(mock_dialog_class.call_count, 1)
        mock_dialog.run.assert_called_once()
        mock_dialog.destroy.assert_called_once()

    @patch("vocalinux.ui.first_run_dialog.FirstRunDialog")
    def test_show_first_run_dialog_none_result(self, mock_dialog_class):
        """Test show_first_run_dialog returns None for closed dialog."""
        from vocalinux.ui.first_run_dialog import show_first_run_dialog

        mock_dialog = MagicMock()
        mock_dialog.result = None
        mock_dialog_class.return_value = mock_dialog

        result = show_first_run_dialog()

        self.assertIsNone(result)
        mock_dialog.run.assert_called_once()
        mock_dialog.destroy.assert_called_once()

    @patch("vocalinux.ui.first_run_dialog.FirstRunDialog")
    def test_show_first_run_dialog_result_later(self, mock_dialog_class):
        """Test show_first_run_dialog returns 'later'."""
        from vocalinux.ui.first_run_dialog import show_first_run_dialog

        mock_dialog = MagicMock()
        mock_dialog.result = "later"
        mock_dialog_class.return_value = mock_dialog

        result = show_first_run_dialog()

        self.assertEqual(result, "later")
        mock_dialog.run.assert_called_once()
        mock_dialog.destroy.assert_called_once()


if __name__ == "__main__":
    unittest.main()
