"""
About Dialog for Vocalinux.

A modern, GNOME HIG-compliant about dialog with:
- Clean card-based layout
- App icon and branding
- Version and description
- Credits section with tabs
- Links to GitHub and license

UX Design Notes:
- Follows GNOME Human Interface Guidelines
- Uses standard Gtk.AboutDialog as base (GNOME apps do this)
- Customizes with better styling and organization
- Close-only button pattern
"""

import logging
import os

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GdkPixbuf, Gtk  # noqa: E402

logger = logging.getLogger(__name__)


def show_about_dialog(parent: Gtk.Window = None):
    """
    Show the About dialog for Vocalinux.

    Uses Gtk.AboutDialog which is the GNOME-standard way to show app info.
    This is the recommended approach per GNOME HIG.

    Args:
        parent: Parent window for the dialog
    """
    from ..utils.resource_manager import ResourceManager
    from ..version import __copyright__, __description__, __url__, __version__

    resource_manager = ResourceManager()

    about_dialog = Gtk.AboutDialog()
    about_dialog.set_transient_for(parent)
    about_dialog.set_modal(True)

    # Basic info
    about_dialog.set_program_name("Vocalinux")
    about_dialog.set_version(__version__)
    about_dialog.set_copyright(__copyright__)

    # Description with cleaner formatting (no emojis in main comments)
    about_dialog.set_comments(__description__)

    # Website
    about_dialog.set_website(__url__)
    about_dialog.set_website_label("Star on GitHub")

    # License
    about_dialog.set_license_type(Gtk.License.GPL_3_0)

    # Credits
    about_dialog.set_authors(["Jatin K Malik <jatinkrmalik@gmail.com>"])
    about_dialog.set_documenters(["Jatin K Malik"])
    about_dialog.set_artists(["Jatin K Malik"])

    # Additional credits section
    about_dialog.add_credit_section(
        "Contributors",
        [
            "Open to contributions!",
            "github.com/jatinkrmalik/vocalinux",
        ],
    )

    about_dialog.add_credit_section(
        "Built With",
        [
            "VOSK Speech Recognition",
            "OpenAI Whisper",
            "GTK 3 / PyGObject",
        ],
    )

    # Set the logo
    logo_path = resource_manager.get_icon_path("vocalinux")
    if os.path.exists(logo_path):
        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(logo_path)
            # Scale to appropriate size for about dialog
            scaled_pixbuf = pixbuf.scale_simple(128, 128, GdkPixbuf.InterpType.BILINEAR)
            about_dialog.set_logo(scaled_pixbuf)
        except Exception as e:
            logger.warning(f"Failed to load or scale logo: {e}")

    # Run and clean up
    about_dialog.run()
    about_dialog.destroy()


class AboutDialog(Gtk.Dialog):
    """
    Custom About Dialog with modern GNOME styling.

    This is an alternative to Gtk.AboutDialog for apps that want more
    customization. Uses card-based layout with tabs for different sections.
    """

    # CSS for modern styling
    ABOUT_CSS = """
    .about-dialog {
        background-color: @theme_bg_color;
    }

    .about-header {
        padding: 32px 24px 24px 24px;
    }

    .about-icon {
        margin-bottom: 16px;
    }

    .about-title {
        font-size: 1.5em;
        font-weight: bold;
        margin-bottom: 4px;
    }

    .about-version {
        font-size: 0.9em;
        color: @theme_unfocused_fg_color;
        margin-bottom: 12px;
    }

    .about-description {
        color: @theme_unfocused_fg_color;
        margin-bottom: 16px;
    }

    .about-links {
        margin-top: 8px;
    }

    .about-link-button {
        padding: 8px 16px;
        border-radius: 8px;
        background-color: @theme_selected_bg_color;
        color: @theme_selected_fg_color;
    }

    .about-link-button:hover {
        background-color: shade(@theme_selected_bg_color, 1.1);
    }

    .about-section {
        background-color: @theme_base_color;
        border-radius: 12px;
        padding: 16px;
        margin: 8px 24px;
        border: 1px solid alpha(@borders, 0.5);
    }

    .about-section-title {
        font-weight: 600;
        font-size: 0.85em;
        color: @theme_unfocused_fg_color;
        margin-bottom: 8px;
    }

    .about-credit {
        padding: 4px 0;
    }

    .about-credit-name {
        font-weight: 500;
    }

    .about-credit-role {
        font-size: 0.85em;
        color: @theme_unfocused_fg_color;
    }

    .about-footer {
        padding: 16px 24px;
        color: @theme_unfocused_fg_color;
        font-size: 0.85em;
    }
    """

    def __init__(self, parent: Gtk.Window = None):
        from ..utils.resource_manager import ResourceManager
        from ..version import __copyright__, __description__, __url__, __version__

        super().__init__(
            title="About Vocalinux",
            transient_for=parent,
            flags=Gtk.DialogFlags.MODAL,
        )

        self.resource_manager = ResourceManager()
        self.version = __version__
        self.description = __description__
        self.url = __url__
        self.copyright = __copyright__

        # Setup
        self._setup_css()
        self.set_default_size(400, -1)
        self.set_resizable(False)
        self.get_style_context().add_class("about-dialog")

        # Only Close button
        self.add_button("_Close", Gtk.ResponseType.CLOSE)

        # Build UI
        self._build_ui()

        # Connect response
        self.connect("response", lambda d, r: d.destroy())

        self.show_all()

    def _setup_css(self):
        """Set up CSS styling."""
        from gi.repository import Gdk

        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(self.ABOUT_CSS.encode())
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

    def _build_ui(self):
        """Build the dialog UI."""
        content_area = self.get_content_area()

        # Main container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        content_area.add(main_box)

        # Header section (icon, name, version, description)
        header = self._build_header()
        main_box.pack_start(header, False, False, 0)

        # Links section
        links = self._build_links()
        main_box.pack_start(links, False, False, 0)

        # Credits section
        credits_section = self._build_credits()
        main_box.pack_start(credits_section, False, False, 0)

        # Footer (copyright, license)
        footer = self._build_footer()
        main_box.pack_start(footer, False, False, 0)

    def _build_header(self):
        """Build the header with icon, name, version."""
        header = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        header.get_style_context().add_class("about-header")
        header.set_halign(Gtk.Align.CENTER)

        # App icon
        logo_path = self.resource_manager.get_icon_path("vocalinux")
        if os.path.exists(logo_path):
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file(logo_path)
                scaled = pixbuf.scale_simple(96, 96, GdkPixbuf.InterpType.BILINEAR)
                icon = Gtk.Image.new_from_pixbuf(scaled)
                icon.get_style_context().add_class("about-icon")
                header.pack_start(icon, False, False, 0)
            except Exception as e:
                logger.warning(f"Failed to load logo: {e}")

        # App name
        name_label = Gtk.Label(label="Vocalinux")
        name_label.get_style_context().add_class("about-title")
        header.pack_start(name_label, False, False, 0)

        # Version
        version_label = Gtk.Label(label=self.version)
        version_label.get_style_context().add_class("about-version")
        header.pack_start(version_label, False, False, 0)

        # Description
        desc_label = Gtk.Label(label=self.description)
        desc_label.get_style_context().add_class("about-description")
        desc_label.set_line_wrap(True)
        desc_label.set_max_width_chars(40)
        desc_label.set_justify(Gtk.Justification.CENTER)
        header.pack_start(desc_label, False, False, 0)

        return header

    def _build_links(self):
        """Build the links section."""
        links_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        links_box.set_halign(Gtk.Align.CENTER)
        links_box.get_style_context().add_class("about-links")
        links_box.set_margin_bottom(16)

        # GitHub button
        github_button = Gtk.LinkButton.new_with_label(self.url, "Star on GitHub")
        github_button.get_style_context().add_class("about-link-button")
        links_box.pack_start(github_button, False, False, 0)

        return links_box

    def _build_credits(self):
        """Build the credits section."""
        section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        section.get_style_context().add_class("about-section")

        # Title
        title = Gtk.Label(label="CREDITS", xalign=0)
        title.get_style_context().add_class("about-section-title")
        section.pack_start(title, False, False, 0)

        # Author
        author_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        author_box.get_style_context().add_class("about-credit")

        author_name = Gtk.Label(label="Jatin K Malik", xalign=0)
        author_name.get_style_context().add_class("about-credit-name")
        author_box.pack_start(author_name, False, False, 0)

        author_role = Gtk.Label(label="Author & Maintainer", xalign=0)
        author_role.get_style_context().add_class("about-credit-role")
        author_box.pack_start(author_role, False, False, 0)

        section.pack_start(author_box, False, False, 0)

        # Technologies
        tech_label = Gtk.Label(xalign=0)
        tech_label.set_markup("<small>Built with VOSK, OpenAI Whisper, GTK 3, and Python</small>")
        tech_label.get_style_context().add_class("about-credit-role")
        tech_label.set_margin_top(8)
        section.pack_start(tech_label, False, False, 0)

        return section

    def _build_footer(self):
        """Build the footer with copyright and license."""
        footer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        footer.get_style_context().add_class("about-footer")
        footer.set_halign(Gtk.Align.CENTER)

        # Copyright
        copyright_label = Gtk.Label(label=self.copyright)
        copyright_label.set_line_wrap(True)
        footer.pack_start(copyright_label, False, False, 0)

        # License
        license_label = Gtk.Label()
        license_label.set_markup(
            '<a href="https://www.gnu.org/licenses/gpl-3.0.html">'
            "GNU General Public License v3.0</a>"
        )
        footer.pack_start(license_label, False, False, 0)

        return footer
