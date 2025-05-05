"""
Settings Dialog for Vocalinux.

Allows users to configure speech recognition engine, model size,
and other relevant parameters.
"""

import logging
import threading
import time
from typing import TYPE_CHECKING, Optional

import gi

gi.require_version("Gtk", "3.0")
# Need GLib for idle_add
from gi.repository import GLib, GObject, Gtk

from ..common_types import RecognitionState

# Avoid circular imports for type checking
if TYPE_CHECKING:
    from ..speech_recognition.recognition_manager import SpeechRecognitionManager
    from .config_manager import ConfigManager

logger = logging.getLogger(__name__)

# Define available models for each engine
ENGINE_MODELS = {
    "vosk": [
        "small",
        "medium",
        "large",
    ],  # Note: 'large' maps to vosk-en-us-0.22 internally
    "whisper": [
        "tiny",
        "base",
        "small",
        "medium",
        "large",
    ],  # Add more whisper sizes if needed
}


class SettingsDialog(Gtk.Dialog):
    """GTK Dialog for configuring Vocalinux settings."""

    def __init__(
        self,
        parent: Gtk.Window,
        config_manager: "ConfigManager",
        speech_engine: "SpeechRecognitionManager",
    ):
        super().__init__(title="Vocalinux Settings", transient_for=parent, flags=0)
        self.config_manager = config_manager
        self.speech_engine = speech_engine
        self._test_active = False
        self._test_result = ""

        self.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_APPLY,
            Gtk.ResponseType.APPLY,
        )
        self.set_default_size(450, 400)
        self.set_border_width(10)

        # --- UI Elements ---
        self.grid = Gtk.Grid(column_spacing=10, row_spacing=15)
        self.get_content_area().add(self.grid)

        # Engine Selection
        self.grid.attach(
            Gtk.Label(label="Speech Engine:", halign=Gtk.Align.START), 0, 0, 1, 1
        )
        self.engine_combo = Gtk.ComboBoxText()

        # Model Size Selection
        self.grid.attach(
            Gtk.Label(label="Model Size:", halign=Gtk.Align.START), 0, 1, 1, 1
        )
        self.model_combo = Gtk.ComboBoxText()
        self.grid.attach(self.model_combo, 1, 1, 1, 1)

        # VOSK Specific Settings Box (initially hidden)
        self.vosk_settings_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=10
        )
        self.vosk_grid = Gtk.Grid(column_spacing=10, row_spacing=10)
        self.vosk_settings_box.pack_start(
            Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 5
        )
        self.vosk_settings_box.pack_start(
            Gtk.Label(
                label="<b>VOSK Settings</b>", use_markup=True, halign=Gtk.Align.START
            ),
            False,
            False,
            5,
        )
        self.vosk_settings_box.pack_start(self.vosk_grid, False, False, 0)
        self.grid.attach(self.vosk_settings_box, 0, 2, 2, 1)

        # VAD Sensitivity
        self.vosk_grid.attach(Gtk.Label(label="VAD Sensitivity (1-5):"), 0, 0, 1, 1)
        self.vad_spin = Gtk.SpinButton.new_with_range(1, 5, 1)
        self.vosk_grid.attach(self.vad_spin, 1, 0, 1, 1)

        # Silence Timeout
        self.vosk_grid.attach(Gtk.Label(label="Silence Timeout (sec):"), 0, 1, 1, 1)
        self.silence_spin = Gtk.SpinButton.new_with_range(0.5, 5.0, 0.1)
        self.silence_spin.set_digits(1)
        self.vosk_grid.attach(self.silence_spin, 1, 1, 1, 1)

        # Test Area
        self.grid.attach(
            Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), 0, 3, 2, 1
        )
        test_label = Gtk.Label(
            label="<b>Test Recognition</b>", use_markup=True, halign=Gtk.Align.START
        )
        self.grid.attach(test_label, 0, 4, 2, 1)

        scrolled_window = Gtk.ScrolledWindow(hexpand=True, vexpand=True)
        scrolled_window.set_min_content_height(100)
        self.test_textview = Gtk.TextView(
            editable=False, cursor_visible=False, wrap_mode=Gtk.WrapMode.WORD
        )
        self.test_buffer = self.test_textview.get_buffer()
        scrolled_window.add(self.test_textview)
        self.grid.attach(scrolled_window, 0, 5, 2, 1)

        self.test_button = Gtk.Button(label="Start Test (3 seconds)")
        self.test_button.connect("clicked", self._on_test_clicked)
        self.grid.attach(self.test_button, 0, 6, 2, 1)

        # ---- CRITICAL CHANGE ----
        # Load settings FIRST before creating UI connections
        settings = self._get_current_settings()
        self.current_engine = settings["engine"]
        self.current_model_size = settings["model_size"]
        self.current_vad = settings.get("vad_sensitivity", 3)
        self.current_silence = settings.get("silence_timeout", 2.0)

        logger.info(
            f"Starting dialog with settings: engine={self.current_engine}, model={self.current_model_size}"
        )

        # Populate engine combo
        for engine in ENGINE_MODELS.keys():
            capitalized_engine = engine.capitalize()
            self.engine_combo.append(capitalized_engine, capitalized_engine)

        # Add engine change handler AFTER populating, but before setting active
        self.engine_combo.connect("changed", self._on_engine_changed)
        self.grid.attach(self.engine_combo, 1, 0, 1, 1)

        # Set engine active
        engine_text = self.current_engine.capitalize()
        logger.info(f"Setting active engine to: {engine_text}")
        if not self.engine_combo.set_active_id(engine_text):
            logger.warning(f"Could not set engine by ID, trying by index")
            # Fallback to setting by index
            if self.current_engine == "vosk":
                self.engine_combo.set_active(0)
            elif self.current_engine == "whisper":
                self.engine_combo.set_active(1)

        # Populate model options for the selected engine
        self._populate_model_options()

        # Set non-dependent widgets directly
        self.vad_spin.set_value(self.current_vad)
        self.silence_spin.set_value(self.current_silence)

        # Show/hide VOSK settings based on the engine
        self._update_engine_specific_ui()

        # Show everything
        self.show_all()

    def _get_current_settings(self):
        """Get current settings from config manager."""
        # Always reload config from disk to reflect latest saved settings
        self.config_manager.load_config()
        settings = self.config_manager.get_settings()

        # Use .get with defaults for robustness
        sr_settings = settings.get("speech_recognition", {})
        engine = sr_settings.get("engine", "vosk")
        model_size = sr_settings.get("model_size", "small")
        vad_sensitivity = sr_settings.get("vad_sensitivity", 3)
        silence_timeout = sr_settings.get("silence_timeout", 2.0)

        logger.info(
            f"Loaded current settings: engine={engine}, model_size={model_size}, "
            f"vad={vad_sensitivity}, silence={silence_timeout}"
        )

        return {
            "engine": engine,
            "model_size": model_size,
            "vad_sensitivity": vad_sensitivity,
            "silence_timeout": silence_timeout,
        }

    def _populate_model_options(self):
        """Populate model options based on the current engine selection."""
        # Clear existing items
        self.model_combo.remove_all()

        # Get the current engine text and convert to lowercase for lookup
        engine_text = self.engine_combo.get_active_text()
        if not engine_text:
            logger.warning("No engine selected during model options population")
            return

        engine = engine_text.lower()
        logger.info(f"Populating model options for engine: {engine}")

        # Add model sizes for this engine
        if engine in ENGINE_MODELS:
            # Add all options for this engine
            for size in ENGINE_MODELS[engine]:
                capitalized_size = size.capitalize()
                self.model_combo.append(capitalized_size, capitalized_size)

            # Set the active model from settings
            model_to_set = self.current_model_size.capitalize()
            logger.info(f"Setting active model to: {model_to_set}")

            # Try to set by ID
            if not self.model_combo.set_active_id(model_to_set):
                logger.warning(
                    f"Could not set model by ID '{model_to_set}', trying by text"
                )
                # Find by text as fallback
                model = self.model_combo.get_model()
                model_found = False
                for i, row in enumerate(model):
                    if row[0].lower() == self.current_model_size.lower():
                        self.model_combo.set_active(i)
                        model_found = True
                        logger.info(f"Set model by index {i}")
                        break

                # If still not found, default to first
                if not model_found and len(ENGINE_MODELS[engine]) > 0:
                    logger.warning(
                        f"Model '{model_to_set}' not found in options, defaulting to first"
                    )
                    self.model_combo.set_active(0)

            # Log final selection
            logger.info(f"Final selected model: {self.model_combo.get_active_text()}")

    def _on_engine_changed(self, widget):
        """Handle changes in the selected engine."""
        self._populate_model_options()
        self._update_engine_specific_ui()

    def _update_engine_specific_ui(self):
        """Show/hide UI elements specific to the selected engine."""
        selected_engine_text = self.engine_combo.get_active_text()
        if not selected_engine_text:
            self.vosk_settings_box.hide()
            return

        selected_engine = selected_engine_text.lower()
        if selected_engine == "vosk":
            self.vosk_settings_box.show()
        else:
            self.vosk_settings_box.hide()

    def get_selected_settings(self) -> dict:
        """Return the currently selected settings from the UI."""
        engine_text = self.engine_combo.get_active_text()
        model_text = self.model_combo.get_active_text()

        # Handle cases where combo boxes might be empty (shouldn't happen with defaults)
        engine = engine_text.lower() if engine_text else "vosk"
        model_size = model_text.lower() if model_text else "small"

        vad = int(self.vad_spin.get_value())
        silence = self.silence_spin.get_value()

        settings = {
            "engine": engine,
            "model_size": model_size,
        }
        # Only include VOSK settings if VOSK is selected
        if engine == "vosk":
            settings["vad_sensitivity"] = vad
            settings["silence_timeout"] = silence

        return settings

    def _on_test_clicked(self, widget):
        """Handle click on the test button."""
        if self._test_active:
            logger.warning("Test already in progress.")
            return

        # Ensure settings are applied before testing
        current_config = self.config_manager.get_settings().get(
            "speech_recognition", {}
        )
        selected_settings = self.get_selected_settings()

        # Check if settings in dialog differ from saved config
        # This is a basic check; a more robust diff might be needed
        settings_differ = False
        if current_config.get("engine") != selected_settings.get(
            "engine"
        ) or current_config.get("model_size") != selected_settings.get("model_size"):
            settings_differ = True
        elif selected_settings.get("engine") == "vosk":
            if current_config.get("vad_sensitivity") != selected_settings.get(
                "vad_sensitivity"
            ) or current_config.get("silence_timeout") != selected_settings.get(
                "silence_timeout"
            ):
                settings_differ = True
        # Add checks for other engines if they get specific settings

        if settings_differ:
            self.test_buffer.set_text("Please Apply settings before testing.")
            return

        self._test_active = True
        self.test_button.set_sensitive(False)
        self.test_button.set_label("Testing... Speak Now!")
        self.test_buffer.set_text("")  # Clear previous results
        self._test_result = ""

        # Register a temporary callback for test results
        self.speech_engine.register_text_callback(self._test_text_callback)

        # Start recognition
        self.speech_engine.start_recognition()

        # Stop recognition after a delay (e.g., 3 seconds) in a separate thread
        threading.Thread(target=self._stop_test_after_delay, args=(3,)).start()

    def _test_text_callback(self, text: str):
        """Callback specifically for the test recognition."""
        # Append text in the GTK main thread
        GLib.idle_add(self._append_test_result, text)

    def _append_test_result(self, text: str):
        current_text = self.test_buffer.get_text(
            self.test_buffer.get_start_iter(), self.test_buffer.get_end_iter(), False
        )
        # Add a space if there's existing text
        separator = (
            " " if current_text.strip() else ""
        )  # Check strip() to avoid leading space
        self.test_buffer.insert(self.test_buffer.get_end_iter(), separator + text)
        # Ensure the text view scrolls to the end
        mark = self.test_buffer.get_insert()
        self.test_textview.scroll_to_mark(mark, 0.0, True, 0.0, 1.0)
        return False  # Remove idle callback

    def _stop_test_after_delay(self, delay: int):
        """Stops the recognition test after a specified delay."""
        time.sleep(delay)
        # Stop recognition in the main GTK thread if possible, or directly
        # Using GLib.idle_add ensures it runs in the correct thread
        GLib.idle_add(self._finalize_test)

    def _finalize_test(self):
        """Finalize the test state and UI updates."""
        if not self._test_active:
            return False  # Already finalized

        self.speech_engine.stop_recognition()
        # Give a brief moment for final processing if needed
        # time.sleep(0.2) # May not be needed if stop_recognition is synchronous enough
        self.speech_engine.unregister_text_callback(self._test_text_callback)

        self._test_active = False
        self.test_button.set_sensitive(True)
        self.test_button.set_label("Start Test (3 seconds)")

        # Check if any text was captured
        final_text = self.test_buffer.get_text(
            self.test_buffer.get_start_iter(), self.test_buffer.get_end_iter(), False
        )
        if not final_text.strip():
            self.test_buffer.set_text("(No speech detected during test)")

        return False  # Remove idle callback

    def apply_settings(self):
        """Apply the selected settings."""
        settings = self.get_selected_settings()
        logger.info(f"Applying settings: {settings}")
        try:
            # 1. Update Config Manager
            self.config_manager.update_speech_recognition_settings(settings)
            self.config_manager.save_settings()

            # 2. Reconfigure Speech Engine
            # Stop engine before reconfiguring if it's running
            was_running = self.speech_engine.state != RecognitionState.IDLE
            if was_running:
                self.speech_engine.stop_recognition()
                # Give it a moment to fully stop
                time.sleep(0.5)

            self.speech_engine.reconfigure(**settings)

            # Restart if it was running before
            # if was_running:
            #    self.speech_engine.start_recognition() # Maybe don't auto-restart?

            logger.info("Settings applied successfully.")
            # Optionally show a confirmation message
            return True
        except Exception as e:
            logger.error(f"Failed to apply settings: {e}", exc_info=True)
            # Show error dialog to the user
            error_dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Error Applying Settings",
            )
            error_dialog.format_secondary_text(f"Could not apply settings: {e}")
            error_dialog.run()
            error_dialog.destroy()
            return False
