"""
Tests for the About Dialog module.

Tests the show_about_dialog function using source code
inspection to verify expected behavior (since GTK mocking is complex across
Python versions).
"""

import os
import unittest


def _get_source_code():
    """Read the about_dialog.py source code."""
    source_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "src",
        "vocalinux",
        "ui",
        "about_dialog.py",
    )
    with open(source_path, "r") as f:
        return f.read()


class TestShowAboutDialogFunction(unittest.TestCase):
    """Test cases for show_about_dialog function structure."""

    def setUp(self):
        """Set up test fixtures."""
        self.source_code = _get_source_code()

    def test_show_about_dialog_function_exists(self):
        """Test that show_about_dialog function is defined."""
        self.assertIn("def show_about_dialog(", self.source_code)

    def test_show_about_dialog_accepts_parent_parameter(self):
        """Test that show_about_dialog accepts a parent parameter."""
        self.assertIn("def show_about_dialog(parent", self.source_code)

    def test_show_about_dialog_creates_about_dialog(self):
        """Test that show_about_dialog creates a Gtk.AboutDialog."""
        self.assertIn("Gtk.AboutDialog()", self.source_code)

    def test_show_about_dialog_sets_program_name(self):
        """Test that show_about_dialog sets the program name."""
        self.assertIn('set_program_name("Vocalinux")', self.source_code)

    def test_show_about_dialog_sets_version(self):
        """Test that show_about_dialog sets the version."""
        self.assertIn("set_version(__version__)", self.source_code)

    def test_show_about_dialog_sets_copyright(self):
        """Test that show_about_dialog sets the copyright."""
        self.assertIn("set_copyright(__copyright__)", self.source_code)

    def test_show_about_dialog_sets_website(self):
        """Test that show_about_dialog sets the website URL."""
        self.assertIn("set_website(__url__)", self.source_code)
        self.assertIn('set_website_label("Star on GitHub")', self.source_code)

    def test_show_about_dialog_sets_license_type(self):
        """Test that show_about_dialog sets the license type."""
        self.assertIn("set_license_type(Gtk.License.GPL_3_0)", self.source_code)

    def test_show_about_dialog_sets_authors(self):
        """Test that show_about_dialog sets authors."""
        self.assertIn("set_authors(", self.source_code)
        self.assertIn("Jatin K Malik", self.source_code)

    def test_show_about_dialog_adds_credit_sections(self):
        """Test that show_about_dialog adds credit sections."""
        self.assertIn("add_credit_section(", self.source_code)
        self.assertIn("Contributors", self.source_code)
        self.assertIn("Built With", self.source_code)

    def test_show_about_dialog_handles_logo(self):
        """Test that show_about_dialog handles logo loading."""
        self.assertIn("get_icon_path", self.source_code)
        self.assertIn("set_logo(", self.source_code)
        self.assertIn("scale_simple(128, 128", self.source_code)

    def test_show_about_dialog_runs_and_destroys(self):
        """Test that show_about_dialog runs and destroys the dialog."""
        self.assertIn("about_dialog.run()", self.source_code)
        self.assertIn("about_dialog.destroy()", self.source_code)

    def test_show_about_dialog_sets_transient_for(self):
        """Test that show_about_dialog sets transient parent."""
        self.assertIn("set_transient_for(parent)", self.source_code)

    def test_show_about_dialog_sets_modal(self):
        """Test that show_about_dialog sets modal."""
        self.assertIn("set_modal(True)", self.source_code)
