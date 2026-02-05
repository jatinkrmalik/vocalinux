"""
Tests for the About Dialog module.

Tests the show_about_dialog function and AboutDialog class.
"""

import sys
import unittest
from unittest.mock import MagicMock, Mock, patch

# Mock GTK before importing anything that might use it
mock_gi = MagicMock()
mock_gtk = MagicMock()
mock_gdk_pixbuf = MagicMock()

sys.modules["gi"] = mock_gi
sys.modules["gi.repository"] = MagicMock()
sys.modules["gi.repository.Gtk"] = mock_gtk
sys.modules["gi.repository.GdkPixbuf"] = mock_gdk_pixbuf
sys.modules["gi.repository.Gdk"] = MagicMock()


class TestShowAboutDialog(unittest.TestCase):
    """Test cases for show_about_dialog function."""

    def setUp(self):
        """Set up test fixtures."""
        # Clear any cached imports
        if "vocalinux.ui.about_dialog" in sys.modules:
            del sys.modules["vocalinux.ui.about_dialog"]

    @patch("vocalinux.ui.about_dialog.os.path.exists")
    @patch("vocalinux.ui.about_dialog.GdkPixbuf")
    @patch("vocalinux.ui.about_dialog.Gtk")
    def test_show_about_dialog_creates_dialog(self, mock_gtk, mock_pixbuf, mock_exists):
        """Test that show_about_dialog creates and shows an AboutDialog."""
        from vocalinux.ui.about_dialog import show_about_dialog

        mock_dialog = MagicMock()
        mock_gtk.AboutDialog.return_value = mock_dialog
        mock_gtk.License.GPL_3_0 = 1
        mock_exists.return_value = False  # No logo file

        show_about_dialog(parent=None)

        # Verify dialog was created and configured
        mock_gtk.AboutDialog.assert_called_once()
        mock_dialog.set_program_name.assert_called_with("Vocalinux")
        mock_dialog.set_license_type.assert_called_with(1)
        mock_dialog.run.assert_called_once()
        mock_dialog.destroy.assert_called_once()

    @patch("vocalinux.ui.about_dialog.os.path.exists")
    @patch("vocalinux.ui.about_dialog.GdkPixbuf")
    @patch("vocalinux.ui.about_dialog.Gtk")
    def test_show_about_dialog_sets_version(self, mock_gtk, mock_pixbuf, mock_exists):
        """Test that show_about_dialog sets the version from version module."""
        from vocalinux.ui.about_dialog import show_about_dialog
        from vocalinux.version import __version__

        mock_dialog = MagicMock()
        mock_gtk.AboutDialog.return_value = mock_dialog
        mock_gtk.License.GPL_3_0 = 1
        mock_exists.return_value = False

        show_about_dialog(parent=None)

        mock_dialog.set_version.assert_called_with(__version__)

    @patch("vocalinux.ui.about_dialog.os.path.exists")
    @patch("vocalinux.ui.about_dialog.GdkPixbuf")
    @patch("vocalinux.ui.about_dialog.Gtk")
    def test_show_about_dialog_sets_copyright(self, mock_gtk, mock_pixbuf, mock_exists):
        """Test that show_about_dialog sets the copyright."""
        from vocalinux.ui.about_dialog import show_about_dialog
        from vocalinux.version import __copyright__

        mock_dialog = MagicMock()
        mock_gtk.AboutDialog.return_value = mock_dialog
        mock_gtk.License.GPL_3_0 = 1
        mock_exists.return_value = False

        show_about_dialog(parent=None)

        mock_dialog.set_copyright.assert_called_with(__copyright__)

    @patch("vocalinux.ui.about_dialog.os.path.exists")
    @patch("vocalinux.ui.about_dialog.GdkPixbuf")
    @patch("vocalinux.ui.about_dialog.Gtk")
    def test_show_about_dialog_sets_website(self, mock_gtk, mock_pixbuf, mock_exists):
        """Test that show_about_dialog sets the website URL."""
        from vocalinux.ui.about_dialog import show_about_dialog
        from vocalinux.version import __url__

        mock_dialog = MagicMock()
        mock_gtk.AboutDialog.return_value = mock_dialog
        mock_gtk.License.GPL_3_0 = 1
        mock_exists.return_value = False

        show_about_dialog(parent=None)

        mock_dialog.set_website.assert_called_with(__url__)
        mock_dialog.set_website_label.assert_called_with("Star on GitHub")

    @patch("vocalinux.ui.about_dialog.os.path.exists")
    @patch("vocalinux.ui.about_dialog.GdkPixbuf")
    @patch("vocalinux.ui.about_dialog.Gtk")
    def test_show_about_dialog_sets_authors(self, mock_gtk, mock_pixbuf, mock_exists):
        """Test that show_about_dialog sets the authors list."""
        from vocalinux.ui.about_dialog import show_about_dialog

        mock_dialog = MagicMock()
        mock_gtk.AboutDialog.return_value = mock_dialog
        mock_gtk.License.GPL_3_0 = 1
        mock_exists.return_value = False

        show_about_dialog(parent=None)

        # Verify authors were set
        mock_dialog.set_authors.assert_called_once()
        args = mock_dialog.set_authors.call_args[0][0]
        self.assertIsInstance(args, list)
        self.assertTrue(len(args) > 0)
        self.assertIn("Jatin K Malik", args[0])

    @patch("vocalinux.ui.about_dialog.os.path.exists")
    @patch("vocalinux.ui.about_dialog.GdkPixbuf")
    @patch("vocalinux.ui.about_dialog.Gtk")
    def test_show_about_dialog_adds_credit_sections(self, mock_gtk, mock_pixbuf, mock_exists):
        """Test that show_about_dialog adds credit sections."""
        from vocalinux.ui.about_dialog import show_about_dialog

        mock_dialog = MagicMock()
        mock_gtk.AboutDialog.return_value = mock_dialog
        mock_gtk.License.GPL_3_0 = 1
        mock_exists.return_value = False

        show_about_dialog(parent=None)

        # Verify credit sections were added
        self.assertTrue(mock_dialog.add_credit_section.called)
        # Should have at least 2 credit sections (Contributors, Built With)
        self.assertGreaterEqual(mock_dialog.add_credit_section.call_count, 2)

    @patch("vocalinux.ui.about_dialog.os.path.exists")
    @patch("vocalinux.ui.about_dialog.GdkPixbuf")
    @patch("vocalinux.ui.about_dialog.Gtk")
    def test_show_about_dialog_loads_logo(self, mock_gtk, mock_pixbuf, mock_exists):
        """Test that show_about_dialog loads and scales the logo."""
        from vocalinux.ui.about_dialog import show_about_dialog

        mock_dialog = MagicMock()
        mock_gtk.AboutDialog.return_value = mock_dialog
        mock_gtk.License.GPL_3_0 = 1
        mock_exists.return_value = True  # Logo exists

        mock_original_pixbuf = MagicMock()
        mock_scaled_pixbuf = MagicMock()
        mock_pixbuf.Pixbuf.new_from_file.return_value = mock_original_pixbuf
        mock_original_pixbuf.scale_simple.return_value = mock_scaled_pixbuf
        mock_pixbuf.InterpType.BILINEAR = 2

        show_about_dialog(parent=None)

        # Verify logo was loaded and scaled
        mock_pixbuf.Pixbuf.new_from_file.assert_called_once()
        mock_original_pixbuf.scale_simple.assert_called_once_with(128, 128, 2)
        mock_dialog.set_logo.assert_called_once_with(mock_scaled_pixbuf)

    @patch("vocalinux.ui.about_dialog.os.path.exists")
    @patch("vocalinux.ui.about_dialog.GdkPixbuf")
    @patch("vocalinux.ui.about_dialog.Gtk")
    def test_show_about_dialog_handles_logo_error(self, mock_gtk, mock_pixbuf, mock_exists):
        """Test that show_about_dialog handles logo loading errors gracefully."""
        from vocalinux.ui.about_dialog import show_about_dialog

        mock_dialog = MagicMock()
        mock_gtk.AboutDialog.return_value = mock_dialog
        mock_gtk.License.GPL_3_0 = 1
        mock_exists.return_value = True  # Logo exists

        # Simulate error loading logo
        mock_pixbuf.Pixbuf.new_from_file.side_effect = Exception("Load error")

        # Should not raise exception
        show_about_dialog(parent=None)

        # Dialog should still run and be destroyed
        mock_dialog.run.assert_called_once()
        mock_dialog.destroy.assert_called_once()
        # Logo should not be set due to error
        mock_dialog.set_logo.assert_not_called()

    @patch("vocalinux.ui.about_dialog.os.path.exists")
    @patch("vocalinux.ui.about_dialog.GdkPixbuf")
    @patch("vocalinux.ui.about_dialog.Gtk")
    def test_show_about_dialog_with_parent(self, mock_gtk, mock_pixbuf, mock_exists):
        """Test that show_about_dialog sets the transient parent."""
        from vocalinux.ui.about_dialog import show_about_dialog

        mock_dialog = MagicMock()
        mock_gtk.AboutDialog.return_value = mock_dialog
        mock_gtk.License.GPL_3_0 = 1
        mock_exists.return_value = False

        mock_parent = MagicMock()
        show_about_dialog(parent=mock_parent)

        mock_dialog.set_transient_for.assert_called_with(mock_parent)
        mock_dialog.set_modal.assert_called_with(True)


class TestAboutDialogClass(unittest.TestCase):
    """Test cases for AboutDialog custom class."""

    def setUp(self):
        """Set up test fixtures."""
        # Clear any cached imports
        if "vocalinux.ui.about_dialog" in sys.modules:
            del sys.modules["vocalinux.ui.about_dialog"]

    @patch("vocalinux.ui.about_dialog.os.path.exists")
    @patch("vocalinux.ui.about_dialog.GdkPixbuf")
    @patch("vocalinux.ui.about_dialog.Gtk")
    def test_about_dialog_class_exists(self, mock_gtk, mock_pixbuf, mock_exists):
        """Test that AboutDialog class is importable."""
        from vocalinux.ui.about_dialog import AboutDialog

        self.assertTrue(callable(AboutDialog))

    def test_about_dialog_has_css(self):
        """Test that AboutDialog has CSS styling defined."""
        # Read the source file directly to check for ABOUT_CSS
        import os

        source_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "src",
            "vocalinux",
            "ui",
            "about_dialog.py",
        )
        with open(source_path, "r") as f:
            source_code = f.read()

        # Check that ABOUT_CSS is defined in the source
        self.assertIn("ABOUT_CSS", source_code)
        self.assertIn(".about-dialog", source_code)
        self.assertIn(".about-header", source_code)


if __name__ == "__main__":
    unittest.main()
