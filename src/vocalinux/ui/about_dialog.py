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
