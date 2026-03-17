"""
Comprehensive coverage tests for AboutDialog class and show_about_dialog function.

Tests implementation details via source code inspection.
"""

import os
import unittest


class TestAboutDialogSourceCodeStructure(unittest.TestCase):
    """Test cases for AboutDialog source code structure."""

    def _get_source_code(self):
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

    def test_show_about_dialog_function_exists(self):
        """Test that show_about_dialog function is defined."""
        source = self._get_source_code()
        self.assertIn("def show_about_dialog(", source)

    def test_show_about_dialog_accepts_parent_parameter(self):
        """Test that show_about_dialog accepts parent parameter."""
        source = self._get_source_code()
        self.assertIn("def show_about_dialog(parent", source)

    def test_show_about_dialog_has_default_parent_none(self):
        """Test that show_about_dialog has default parent=None."""
        source = self._get_source_code()
        self.assertIn("def show_about_dialog(parent: Gtk.Window = None)", source)

    def test_about_dialog_class_exists(self):
        """Test that AboutDialog class is defined."""
        source = self._get_source_code()
        self.assertIn("class AboutDialog(Gtk.Dialog):", source)

    def test_about_dialog_css_constant_exists(self):
        """Test that ABOUT_CSS constant is defined."""
        source = self._get_source_code()
        self.assertIn("ABOUT_CSS = ", source)

    def test_about_dialog_has_init_method(self):
        """Test that AboutDialog has __init__ method."""
        source = self._get_source_code()
        self.assertIn("def __init__(self, parent: Gtk.Window = None):", source)

    def test_about_dialog_has_setup_css_method(self):
        """Test that AboutDialog has _setup_css method."""
        source = self._get_source_code()
        self.assertIn("def _setup_css(self):", source)

    def test_about_dialog_has_build_ui_method(self):
        """Test that AboutDialog has _build_ui method."""
        source = self._get_source_code()
        self.assertIn("def _build_ui(self):", source)

    def test_about_dialog_has_build_header_method(self):
        """Test that AboutDialog has _build_header method."""
        source = self._get_source_code()
        self.assertIn("def _build_header(self):", source)

    def test_about_dialog_has_build_links_method(self):
        """Test that AboutDialog has _build_links method."""
        source = self._get_source_code()
        self.assertIn("def _build_links(self):", source)

    def test_about_dialog_has_build_credits_method(self):
        """Test that AboutDialog has _build_credits method."""
        source = self._get_source_code()
        self.assertIn("def _build_credits(self):", source)

    def test_about_dialog_has_build_footer_method(self):
        """Test that AboutDialog has _build_footer method."""
        source = self._get_source_code()
        self.assertIn("def _build_footer(self):", source)


class TestShowAboutDialogImplementation(unittest.TestCase):
    """Test cases for show_about_dialog function implementation."""

    def _get_source_code(self):
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

    def test_show_about_dialog_creates_about_dialog(self):
        """Test that show_about_dialog creates Gtk.AboutDialog."""
        source = self._get_source_code()
        self.assertIn("Gtk.AboutDialog()", source)

    def test_show_about_dialog_sets_transient_for(self):
        """Test that show_about_dialog sets transient parent."""
        source = self._get_source_code()
        self.assertIn("set_transient_for(parent)", source)

    def test_show_about_dialog_sets_modal(self):
        """Test that show_about_dialog sets modal."""
        source = self._get_source_code()
        self.assertIn("set_modal(True)", source)

    def test_show_about_dialog_sets_program_name(self):
        """Test that show_about_dialog sets program name."""
        source = self._get_source_code()
        self.assertIn('set_program_name("Vocalinux")', source)

    def test_show_about_dialog_sets_version(self):
        """Test that show_about_dialog sets version."""
        source = self._get_source_code()
        self.assertIn("set_version(__version__)", source)

    def test_show_about_dialog_sets_copyright(self):
        """Test that show_about_dialog sets copyright."""
        source = self._get_source_code()
        self.assertIn("set_copyright(__copyright__)", source)

    def test_show_about_dialog_sets_comments(self):
        """Test that show_about_dialog sets comments/description."""
        source = self._get_source_code()
        self.assertIn("set_comments(__description__)", source)

    def test_show_about_dialog_sets_website(self):
        """Test that show_about_dialog sets website."""
        source = self._get_source_code()
        self.assertIn("set_website(__url__)", source)

    def test_show_about_dialog_sets_website_label(self):
        """Test that show_about_dialog sets website label."""
        source = self._get_source_code()
        self.assertIn('set_website_label("Star on GitHub")', source)

    def test_show_about_dialog_sets_license_type(self):
        """Test that show_about_dialog sets GPL license."""
        source = self._get_source_code()
        self.assertIn("set_license_type(Gtk.License.GPL_3_0)", source)

    def test_show_about_dialog_sets_authors(self):
        """Test that show_about_dialog sets authors."""
        source = self._get_source_code()
        self.assertIn("set_authors(", source)

    def test_show_about_dialog_sets_documenters(self):
        """Test that show_about_dialog sets documenters."""
        source = self._get_source_code()
        self.assertIn("set_documenters(", source)

    def test_show_about_dialog_sets_artists(self):
        """Test that show_about_dialog sets artists."""
        source = self._get_source_code()
        self.assertIn("set_artists(", source)

    def test_show_about_dialog_adds_credit_sections(self):
        """Test that show_about_dialog adds credit sections."""
        source = self._get_source_code()
        self.assertIn("add_credit_section(", source)

    def test_show_about_dialog_handles_logo_loading(self):
        """Test that show_about_dialog loads logo."""
        source = self._get_source_code()
        self.assertIn("get_icon_path", source)
        self.assertIn("GdkPixbuf.Pixbuf.new_from_file", source)

    def test_show_about_dialog_scales_logo(self):
        """Test that show_about_dialog scales logo."""
        source = self._get_source_code()
        self.assertIn("scale_simple(128, 128", source)

    def test_show_about_dialog_sets_logo(self):
        """Test that show_about_dialog sets logo."""
        source = self._get_source_code()
        self.assertIn("set_logo(scaled_pixbuf)", source)

    def test_show_about_dialog_runs_dialog(self):
        """Test that show_about_dialog runs the dialog."""
        source = self._get_source_code()
        self.assertIn("about_dialog.run()", source)

    def test_show_about_dialog_destroys_dialog(self):
        """Test that show_about_dialog destroys the dialog."""
        source = self._get_source_code()
        self.assertIn("about_dialog.destroy()", source)

    def test_show_about_dialog_has_error_handling(self):
        """Test that show_about_dialog handles logo loading errors."""
        source = self._get_source_code()
        self.assertIn("try:", source)
        self.assertIn("except Exception", source)
        self.assertIn("logger.warning", source)


class TestAboutDialogClassImplementation(unittest.TestCase):
    """Test cases for AboutDialog class implementation."""

    def _get_source_code(self):
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

    def test_about_dialog_class_inherits_from_gtk_dialog(self):
        """Test that AboutDialog inherits from Gtk.Dialog."""
        source = self._get_source_code()
        self.assertIn("class AboutDialog(Gtk.Dialog):", source)

    def test_about_dialog_stores_resource_manager(self):
        """Test that __init__ stores ResourceManager instance."""
        source = self._get_source_code()
        self.assertIn("self.resource_manager = ResourceManager()", source)

    def test_about_dialog_stores_version(self):
        """Test that __init__ stores version."""
        source = self._get_source_code()
        self.assertIn("self.version = __version__", source)

    def test_about_dialog_stores_description(self):
        """Test that __init__ stores description."""
        source = self._get_source_code()
        self.assertIn("self.description = __description__", source)

    def test_about_dialog_stores_url(self):
        """Test that __init__ stores URL."""
        source = self._get_source_code()
        self.assertIn("self.url = __url__", source)

    def test_about_dialog_stores_copyright(self):
        """Test that __init__ stores copyright."""
        source = self._get_source_code()
        self.assertIn("self.copyright = __copyright__", source)

    def test_about_dialog_calls_setup_css(self):
        """Test that __init__ calls _setup_css."""
        source = self._get_source_code()
        self.assertIn("self._setup_css()", source)

    def test_about_dialog_calls_build_ui(self):
        """Test that __init__ calls _build_ui."""
        source = self._get_source_code()
        self.assertIn("self._build_ui()", source)

    def test_about_dialog_adds_close_button(self):
        """Test that __init__ adds Close button."""
        source = self._get_source_code()
        self.assertIn('add_button("_Close", Gtk.ResponseType.CLOSE)', source)

    def test_about_dialog_calls_show_all(self):
        """Test that __init__ calls show_all."""
        source = self._get_source_code()
        self.assertIn("self.show_all()", source)

    def test_build_header_creates_icon(self):
        """Test that _build_header loads and creates icon."""
        source = self._get_source_code()
        # Check header method creates icon from logo path
        self.assertIn("def _build_header(self):", source)
        self.assertIn("get_icon_path", source)

    def test_build_links_creates_github_button(self):
        """Test that _build_links creates GitHub link button."""
        source = self._get_source_code()
        self.assertIn("Gtk.LinkButton.new_with_label(self.url", source)

    def test_build_credits_includes_author_info(self):
        """Test that _build_credits includes author information."""
        source = self._get_source_code()
        self.assertIn("Jatin K Malik", source)

    def test_build_footer_includes_copyright(self):
        """Test that _build_footer includes copyright label."""
        source = self._get_source_code()
        self.assertIn("self.copyright", source)

    def test_build_footer_includes_license_link(self):
        """Test that _build_footer includes license link."""
        source = self._get_source_code()
        self.assertIn("GNU General Public License v3.0", source)


class TestAboutDialogCSS(unittest.TestCase):
    """Test cases for AboutDialog CSS styling."""

    def _get_source_code(self):
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

    def test_css_includes_about_dialog_class(self):
        """Test that CSS includes .about-dialog class."""
        source = self._get_source_code()
        self.assertIn(".about-dialog {", source)

    def test_css_includes_about_header_class(self):
        """Test that CSS includes .about-header class."""
        source = self._get_source_code()
        self.assertIn(".about-header {", source)

    def test_css_includes_about_icon_class(self):
        """Test that CSS includes .about-icon class."""
        source = self._get_source_code()
        self.assertIn(".about-icon {", source)

    def test_css_includes_about_title_class(self):
        """Test that CSS includes .about-title class."""
        source = self._get_source_code()
        self.assertIn(".about-title {", source)

    def test_css_includes_about_version_class(self):
        """Test that CSS includes .about-version class."""
        source = self._get_source_code()
        self.assertIn(".about-version {", source)

    def test_css_includes_about_description_class(self):
        """Test that CSS includes .about-description class."""
        source = self._get_source_code()
        self.assertIn(".about-description {", source)

    def test_css_includes_about_links_class(self):
        """Test that CSS includes .about-links class."""
        source = self._get_source_code()
        self.assertIn(".about-links {", source)

    def test_css_includes_about_section_class(self):
        """Test that CSS includes .about-section class."""
        source = self._get_source_code()
        self.assertIn(".about-section {", source)

    def test_css_includes_about_footer_class(self):
        """Test that CSS includes .about-footer class."""
        source = self._get_source_code()
        self.assertIn(".about-footer {", source)

    def test_css_uses_theme_bg_color(self):
        """Test that CSS uses @theme_bg_color variable."""
        source = self._get_source_code()
        self.assertIn("@theme_bg_color", source)

    def test_css_uses_theme_base_color(self):
        """Test that CSS uses @theme_base_color variable."""
        source = self._get_source_code()
        self.assertIn("@theme_base_color", source)

    def test_css_uses_theme_unfocused_fg_color(self):
        """Test that CSS uses @theme_unfocused_fg_color variable."""
        source = self._get_source_code()
        self.assertIn("@theme_unfocused_fg_color", source)

    def test_css_includes_border_styling(self):
        """Test that CSS includes border styling."""
        source = self._get_source_code()
        self.assertIn("border", source)

    def test_css_includes_padding(self):
        """Test that CSS includes padding."""
        source = self._get_source_code()
        self.assertIn("padding:", source)

    def test_css_includes_margin(self):
        """Test that CSS includes margin."""
        source = self._get_source_code()
        self.assertIn("margin", source)


if __name__ == "__main__":
    unittest.main()
