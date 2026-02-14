"""
First-run dialog for Vocalinux.

This module shows a dialog on first run to ask the user about autostart preferences.
"""

import logging
from typing import Optional

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

logger = logging.getLogger(__name__)


class FirstRunDialog(Gtk.Dialog):
    """Dialog shown on first run to configure autostart preference."""

    def __init__(self, parent: Optional[Gtk.Window] = None):
        super().__init__(
            title="Welcome to Vocalinux",
            transient_for=parent,
            flags=Gtk.DialogFlags.MODAL,
        )
        self.set_default_size(400, 200)

        box = self.get_content_area()
        box.set_spacing(16)
        box.set_margin_start(24)
        box.set_margin_end(24)
        box.set_margin_top(24)
        box.set_margin_bottom(20)

        title_label = Gtk.Label(label="<b>Welcome to Vocalinux!</b>", use_markup=True)
        title_label.set_justify(Gtk.Justification.CENTER)
        box.pack_start(title_label, False, False, 0)

        description_label = Gtk.Label(
            label="Would you like Vocalinux to start automatically when you log in?",
            wrap=True,
            justify=Gtk.Justification.CENTER,
        )
        box.pack_start(description_label, False, False, 8)

        subtitle_label = Gtk.Label(
            label="This will add Vocalinux to your system's autostart applications.",
            wrap=True,
            justify=Gtk.Justification.CENTER,
        )
        subtitle_label.get_style_context().add_class("preference-row-subtitle")
        box.pack_start(subtitle_label, False, False, 0)

        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        button_box.set_halign(Gtk.Align.CENTER)
        button_box.set_margin_top(16)

        yes_button = Gtk.Button(label="Yes, start on login")
        yes_button.get_style_context().add_class("suggested-action")
        yes_button.connect("clicked", self._on_yes_clicked)
        button_box.pack_start(yes_button, False, False, 0)

        no_button = Gtk.Button(label="No, I'll start manually")
        no_button.connect("clicked", self._on_no_clicked)
        button_box.pack_start(no_button, False, False, 0)

        later_button = Gtk.Button(label="Ask me later")
        later_button.connect("clicked", self._on_later_clicked)
        button_box.pack_start(later_button, False, False, 0)

        box.pack_start(button_box, False, False, 0)

        self.result = None
        self.show_all()

    def _on_yes_clicked(self, widget):
        """Handle Yes button click."""
        self.result = "yes"
        self.destroy()

    def _on_no_clicked(self, widget):
        """Handle No button click."""
        self.result = "no"
        self.destroy()

    def _on_later_clicked(self, widget):
        """Handle Later button click."""
        self.result = "later"
        self.destroy()


def show_first_run_dialog(parent: Optional[Gtk.Window] = None) -> Optional[str]:
    """
    Show the first-run dialog and return the user's choice.

    Args:
        parent: The parent window for the dialog

    Returns:
        "yes" if user chose to enable autostart
        "no" if user chose to disable autostart
        "later" if user wants to be asked later
        None if dialog was closed without making a choice
    """
    dialog = FirstRunDialog(parent)
    dialog.run()
    return dialog.result
