"""
Logging viewer dialog for VocaLinux.

This module provides a GTK dialog for viewing, filtering, and exporting
application logs for debugging purposes.
"""

import logging
import os
import threading
from datetime import datetime
from typing import Optional

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, GObject, Gtk

from .logging_manager import LogRecord, get_logging_manager

logger = logging.getLogger(__name__)


class LoggingDialog(Gtk.Dialog):
    """GTK Dialog for viewing and managing application logs."""

    def __init__(self, parent: Optional[Gtk.Window] = None):
        super().__init__(
            title="VocaLinux Logs",
            transient_for=parent,
            flags=Gtk.DialogFlags.DESTROY_WITH_PARENT,
            modal=False,
        )

        self.logging_manager = get_logging_manager()
        self.auto_scroll = True
        self.filter_level = None
        self.filter_module = None

        # Set dialog properties
        self.set_default_size(900, 700)
        self.set_border_width(10)

        # Add buttons
        self.add_button("Close", Gtk.ResponseType.CLOSE)
        self.add_button("Copy All", Gtk.ResponseType.HELP)
        self.add_button("Export", Gtk.ResponseType.APPLY)
        self.add_button("Clear", Gtk.ResponseType.REJECT)

        # Create UI
        self._create_ui()

        # Register for new log records
        self.logging_manager.register_callback(self._on_new_log_record)

        # Load existing logs
        self._refresh_logs()

        # Connect signals
        self.connect("response", self._on_response)
        self.connect("destroy", self._on_destroy)

    def _create_ui(self):
        """Create the user interface."""
        content_area = self.get_content_area()

        # Create main container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        content_area.add(main_box)

        # Create toolbar
        toolbar_box = self._create_toolbar()
        main_box.pack_start(toolbar_box, False, False, 0)

        # Create log view (give it most of the space)
        log_view_box = self._create_log_view()
        main_box.pack_start(log_view_box, True, True, 0)

        # Create status bar
        status_box = self._create_status_bar()
        main_box.pack_start(status_box, False, False, 0)

        # Show all widgets
        main_box.show_all()

    def _create_toolbar(self):
        """Create the toolbar with filters and controls."""
        toolbar_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        # Level filter
        level_label = Gtk.Label(label="Level:")
        toolbar_box.pack_start(level_label, False, False, 0)

        self.level_combo = Gtk.ComboBoxText()
        self.level_combo.append("ALL", "All Levels")
        self.level_combo.append("DEBUG", "Debug")
        self.level_combo.append("INFO", "Info")
        self.level_combo.append("WARNING", "Warning")
        self.level_combo.append("ERROR", "Error")
        self.level_combo.append("CRITICAL", "Critical")
        self.level_combo.set_active(0)
        self.level_combo.connect("changed", self._on_filter_changed)
        toolbar_box.pack_start(self.level_combo, False, False, 0)

        # Module filter
        module_label = Gtk.Label(label="Module:")
        toolbar_box.pack_start(module_label, False, False, 0)

        self.module_entry = Gtk.Entry()
        self.module_entry.set_placeholder_text("Filter by module name...")
        self.module_entry.connect("changed", self._on_filter_changed)
        toolbar_box.pack_start(self.module_entry, True, True, 0)

        # Auto-scroll toggle
        self.auto_scroll_check = Gtk.CheckButton(label="Auto-scroll")
        self.auto_scroll_check.set_active(True)
        self.auto_scroll_check.connect("toggled", self._on_auto_scroll_toggled)
        toolbar_box.pack_start(self.auto_scroll_check, False, False, 0)

        # Refresh button
        refresh_button = Gtk.Button(label="Refresh")
        refresh_button.connect("clicked", self._on_refresh_clicked)
        toolbar_box.pack_start(refresh_button, False, False, 0)

        return toolbar_box

    def _create_log_view(self):
        """Create the main log viewing area."""
        # Create scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_shadow_type(Gtk.ShadowType.IN)
        # Set minimum height to ensure the text view takes up most of the dialog space
        scrolled.set_min_content_height(400)
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)

        # Create text view
        self.text_view = Gtk.TextView()
        self.text_view.set_editable(False)
        self.text_view.set_cursor_visible(False)
        self.text_view.set_wrap_mode(Gtk.WrapMode.WORD)
        # Ensure the text view expands to fill available space
        self.text_view.set_vexpand(True)
        self.text_view.set_hexpand(True)

        # Set monospace font
        font_desc = self.text_view.get_pango_context().get_font_description()
        font_desc.set_family("monospace")
        font_desc.set_size(9 * 1024)  # 9pt
        self.text_view.override_font(font_desc)

        # Get text buffer
        self.text_buffer = self.text_view.get_buffer()

        # Create text tags for different log levels
        self._create_text_tags()

        scrolled.add(self.text_view)

        # Store reference to scrolled window for auto-scrolling
        self.scrolled_window = scrolled

        return scrolled

    def _create_text_tags(self):
        """Create text tags for different log levels."""
        # Debug - gray
        debug_tag = self.text_buffer.create_tag("DEBUG")
        debug_tag.set_property("foreground", "#666666")

        # Info - default color
        info_tag = self.text_buffer.create_tag("INFO")

        # Warning - orange
        warning_tag = self.text_buffer.create_tag("WARNING")
        warning_tag.set_property("foreground", "#FF8C00")
        warning_tag.set_property("weight", 600)

        # Error - red
        error_tag = self.text_buffer.create_tag("ERROR")
        error_tag.set_property("foreground", "#DC143C")
        error_tag.set_property("weight", 700)

        # Critical - red background
        critical_tag = self.text_buffer.create_tag("CRITICAL")
        critical_tag.set_property("foreground", "#FFFFFF")
        critical_tag.set_property("background", "#DC143C")
        critical_tag.set_property("weight", 700)

    def _create_status_bar(self):
        """Create the status bar."""
        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        self.status_label = Gtk.Label()
        self.status_label.set_halign(Gtk.Align.START)
        status_box.pack_start(self.status_label, True, True, 0)

        # Update status
        self._update_status()

        return status_box

    def _update_status(self):
        """Update the status bar with current log statistics."""
        stats = self.logging_manager.get_log_stats()

        if stats["total"] == 0:
            status_text = "No log records"
        else:
            level_counts = []
            for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
                count = stats["by_level"].get(level, 0)
                if count > 0:
                    level_counts.append(f"{level}: {count}")

            status_text = f"Total: {stats['total']} | " + " | ".join(level_counts)

        self.status_label.set_text(status_text)

    def _on_filter_changed(self, widget):
        """Handle filter changes."""
        # Get current filter values
        level_id = self.level_combo.get_active_id()
        self.filter_level = None if level_id == "ALL" else level_id

        module_text = self.module_entry.get_text().strip()
        self.filter_module = module_text if module_text else None

        # Refresh logs with new filters
        self._refresh_logs()

    def _on_auto_scroll_toggled(self, widget):
        """Handle auto-scroll toggle."""
        self.auto_scroll = widget.get_active()

    def _on_refresh_clicked(self, widget):
        """Handle refresh button click."""
        self._refresh_logs()

    def _refresh_logs(self):
        """Refresh the log display with current filters."""
        # Get filtered logs
        records = self.logging_manager.get_logs(
            level_filter=self.filter_level, module_filter=self.filter_module
        )

        # Clear text buffer
        self.text_buffer.set_text("")

        # Add log records
        for record in records:
            self._append_log_record(record)

        # Update status
        self._update_status()

        # Auto-scroll to bottom
        if self.auto_scroll:
            self._scroll_to_bottom()

    def _append_log_record(self, record: LogRecord):
        """
        Append a log record to the text view.

        Args:
            record: The log record to append
        """
        # Format the log line
        log_line = str(record) + "\n"

        # Get end iterator
        end_iter = self.text_buffer.get_end_iter()

        # Insert text with appropriate tag
        tag_name = record.level
        if tag_name in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            self.text_buffer.insert_with_tags_by_name(end_iter, log_line, tag_name)
        else:
            self.text_buffer.insert(end_iter, log_line)

    def _scroll_to_bottom(self):
        """Scroll the text view to the bottom."""
        mark = self.text_buffer.get_insert()
        end_iter = self.text_buffer.get_end_iter()
        self.text_buffer.place_cursor(end_iter)
        self.text_view.scroll_to_mark(mark, 0.0, False, 0.0, 0.0)

    def _on_new_log_record(self, record: LogRecord):
        """
        Handle new log record from the logging manager.

        Args:
            record: The new log record
        """
        # Check if record matches current filters
        if self.filter_level and record.level != self.filter_level:
            return

        if self.filter_module and self.filter_module.lower() not in record.logger_name.lower():
            return

        # Add to UI in main thread
        GLib.idle_add(self._append_log_record_safe, record)

    def _append_log_record_safe(self, record: LogRecord):
        """
        Safely append a log record in the main thread.

        Args:
            record: The log record to append
        """
        try:
            self._append_log_record(record)

            # Auto-scroll if enabled
            if self.auto_scroll:
                self._scroll_to_bottom()

            # Update status
            self._update_status()

        except Exception as e:
            print(f"Error appending log record: {e}")

        return False  # Remove from idle queue

    def _on_response(self, dialog, response_id):
        """Handle dialog responses."""
        if response_id == Gtk.ResponseType.APPLY:
            self._export_logs()
        elif response_id == Gtk.ResponseType.REJECT:
            self._clear_logs()
        elif response_id == Gtk.ResponseType.HELP:
            self._copy_logs_to_clipboard()
        elif response_id == Gtk.ResponseType.CLOSE:
            self.destroy()

    def _export_logs(self):
        """Export logs to a file."""
        # Create file chooser dialog
        file_dialog = Gtk.FileChooserDialog(
            title="Export Logs", parent=self, action=Gtk.FileChooserAction.SAVE
        )

        file_dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.OK
        )

        # Set default filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"vocalinux_logs_{timestamp}.txt"
        file_dialog.set_current_name(default_filename)

        # Add file filter
        file_filter = Gtk.FileFilter()
        file_filter.set_name("Text files")
        file_filter.add_pattern("*.txt")
        file_dialog.add_filter(file_filter)

        response = file_dialog.run()

        if response == Gtk.ResponseType.OK:
            filepath = file_dialog.get_filename()
            success = self.logging_manager.export_logs(
                filepath, level_filter=self.filter_level, module_filter=self.filter_module
            )

            if success:
                self._show_message("Export successful", f"Logs exported to:\n{filepath}")
            else:
                self._show_message(
                    "Export failed",
                    "Failed to export logs. Check the logs for details.",
                    Gtk.MessageType.ERROR,
                )

        file_dialog.destroy()

    def _copy_logs_to_clipboard(self):
        """Copy all visible logs to clipboard."""
        try:
            # Get all text from the text buffer
            start_iter = self.text_buffer.get_start_iter()
            end_iter = self.text_buffer.get_end_iter()
            text_content = self.text_buffer.get_text(start_iter, end_iter, False)

            if not text_content.strip():
                self._show_message("No logs to copy", "There are no logs to copy to clipboard.")
                return

            # Get the clipboard
            from gi.repository import Gdk

            clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)

            # Create header for clipboard content
            from datetime import datetime

            header = f"VocaLinux Logs - Copied at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            header += "=" * 80 + "\n\n"

            # Combine header and content
            clipboard_content = header + text_content

            # Set clipboard content
            clipboard.set_text(clipboard_content, -1)
            clipboard.store()

            # Count lines for user feedback
            line_count = len(text_content.strip().split("\n"))
            self._show_message(
                "Logs copied to clipboard",
                f"Successfully copied {line_count} log lines to clipboard.\n\n"
                "You can now paste them into any text editor or document.",
            )

        except Exception as e:
            logger.error(f"Failed to copy logs to clipboard: {e}")
            self._show_message(
                "Copy failed", f"Failed to copy logs to clipboard: {e}", Gtk.MessageType.ERROR
            )

    def _clear_logs(self):
        """Clear all logs after confirmation."""
        # Show confirmation dialog
        confirm_dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Clear all logs?",
        )
        confirm_dialog.format_secondary_text(
            "This will permanently remove all log records from memory. "
            "This action cannot be undone."
        )

        response = confirm_dialog.run()
        confirm_dialog.destroy()

        if response == Gtk.ResponseType.YES:
            self.logging_manager.clear_logs()
            self._refresh_logs()
            self._show_message("Logs cleared", "All log records have been cleared.")

    def _show_message(
        self, title: str, message: str, message_type: Gtk.MessageType = Gtk.MessageType.INFO
    ):
        """
        Show a message dialog.

        Args:
            title: Dialog title
            message: Message text
            message_type: Type of message
        """
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=message_type,
            buttons=Gtk.ButtonsType.OK,
            text=title,
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()

    def _on_destroy(self, widget):
        """Handle dialog destruction."""
        # Unregister callback
        self.logging_manager.unregister_callback(self._on_new_log_record)
