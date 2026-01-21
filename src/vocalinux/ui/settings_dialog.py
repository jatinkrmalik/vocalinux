"""
Settings Dialog for Vocalinux.

Allows users to configure speech recognition engine, model size,
and other relevant parameters.
"""

import logging
import os
import threading
import time
from typing import TYPE_CHECKING

import gi

gi.require_version("Gtk", "3.0")
# Need GLib for idle_add
from gi.repository import GLib, Gtk  # noqa: E402

from ..common_types import RecognitionState  # noqa: E402

# Avoid circular imports for type checking
if TYPE_CHECKING:
    from ..speech_recognition.recognition_manager import SpeechRecognitionManager  # noqa: E402
    from .config_manager import ConfigManager  # noqa: E402

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

# Whisper model metadata for display
WHISPER_MODEL_INFO = {
    "tiny": {"size_mb": 75, "desc": "Fastest, lowest accuracy", "params": "39M"},
    "base": {"size_mb": 142, "desc": "Fast, good for basic use", "params": "74M"},
    "small": {"size_mb": 466, "desc": "Balanced speed/accuracy", "params": "244M"},
    "medium": {"size_mb": 1500, "desc": "High accuracy, slower", "params": "769M"},
    "large": {"size_mb": 2900, "desc": "Highest accuracy, slowest", "params": "1550M"},
}

# VOSK model metadata for display
VOSK_MODEL_INFO = {
    "small": {
        "size_mb": 40,
        "desc": "Lightweight, fast",
        "model_name": "vosk-model-small-en-us-0.15",
    },
    "medium": {
        "size_mb": 1800,
        "desc": "Balanced accuracy/speed",
        "model_name": "vosk-model-en-us-0.22",
    },
    "large": {
        "size_mb": 1800,
        "desc": "Same as medium (best available)",
        "model_name": "vosk-model-en-us-0.22",
    },
}

# Models directory
MODELS_DIR = os.path.expanduser("~/.local/share/vocalinux/models")
SYSTEM_MODELS_DIRS = [
    "/usr/local/share/vocalinux/models",
    "/usr/share/vocalinux/models",
]


def _get_whisper_cache_dir() -> str:
    """Get the Whisper model cache directory."""
    return os.path.expanduser("~/.local/share/vocalinux/models/whisper")


def _is_whisper_model_downloaded(model_name: str) -> bool:
    """Check if a Whisper model is downloaded."""
    cache_dir = _get_whisper_cache_dir()
    model_file = os.path.join(cache_dir, f"{model_name}.pt")
    if os.path.exists(model_file):
        return True
    # Also check default whisper cache
    default_cache = os.path.expanduser("~/.cache/whisper")
    return os.path.exists(os.path.join(default_cache, f"{model_name}.pt"))


def _format_size(size_mb: int) -> str:
    """Format size in MB to human readable string."""
    if size_mb >= 1000:
        return f"{size_mb / 1000:.1f} GB"
    return f"{size_mb} MB"


def _get_recommended_whisper_model() -> tuple:
    """Get recommended model based on system configuration."""
    import warnings

    try:
        import psutil

        ram_gb = psutil.virtual_memory().total // (1024**3)

        # Check for CUDA - suppress warnings during detection
        has_cuda = False
        cuda_memory_gb = 0
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                import torch

                if torch.cuda.is_available():
                    has_cuda = True
                    cuda_memory_gb = torch.cuda.get_device_properties(0).total_memory // (1024**3)
        except Exception:
            pass

        if has_cuda and cuda_memory_gb >= 8:
            return "medium", f"GPU with {cuda_memory_gb}GB VRAM"
        elif has_cuda and cuda_memory_gb >= 4:
            return "small", f"GPU with {cuda_memory_gb}GB VRAM"
        elif ram_gb >= 8:
            return "small", f"{ram_gb}GB RAM - good balance"
        elif ram_gb >= 4:
            return "base", f"{ram_gb}GB RAM"
        else:
            return "tiny", f"Limited RAM ({ram_gb}GB)"
    except Exception:
        return "base", "Default recommendation"


def _is_vosk_model_downloaded(model_name: str) -> bool:
    """Check if a VOSK model is downloaded."""
    if model_name not in VOSK_MODEL_INFO:
        return False

    vosk_model_name = VOSK_MODEL_INFO[model_name]["model_name"]

    # Check user's local models directory
    user_model_path = os.path.join(MODELS_DIR, vosk_model_name)
    if os.path.exists(user_model_path):
        return True

    # Check system-wide installation directories
    for system_dir in SYSTEM_MODELS_DIRS:
        system_model_path = os.path.join(system_dir, vosk_model_name)
        if os.path.exists(system_model_path):
            return True

    return False


def _get_recommended_vosk_model() -> tuple:
    """Get recommended VOSK model based on system configuration."""
    try:
        import psutil

        ram_gb = psutil.virtual_memory().total // (1024**3)

        # VOSK models are CPU-based, so we recommend based on RAM and disk space
        if ram_gb >= 4:
            return "medium", f"{ram_gb}GB RAM - better accuracy"
        else:
            return "small", f"Limited RAM ({ram_gb}GB) - optimized for speed"
    except Exception:
        return "small", "Default recommendation"


class ModelDownloadDialog(Gtk.Dialog):
    """Dialog showing model download progress with cancel support."""

    def __init__(self, parent, model_name: str, model_size_mb: int, engine: str = "whisper"):
        super().__init__(
            title=f"Downloading {model_name.capitalize()} Model",
            transient_for=parent,
            flags=Gtk.DialogFlags.MODAL,
        )
        self.set_default_size(450, 180)
        self.set_deletable(False)  # Prevent closing during download

        self.cancelled = False
        self.engine = engine
        self.model_name = model_name

        engine_display = engine.upper() if engine == "vosk" else engine.capitalize()

        box = self.get_content_area()
        box.set_spacing(12)
        box.set_margin_start(20)
        box.set_margin_end(20)
        box.set_margin_top(20)
        box.set_margin_bottom(15)

        # Info label
        self.info_label = Gtk.Label(
            label=f"Downloading {engine_display} {model_name} model (~{_format_size(model_size_mb)})...",
            wrap=True,
            justify=Gtk.Justification.CENTER,
        )
        box.pack_start(self.info_label, False, False, 0)

        # Progress bar
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_show_text(True)
        self.progress_bar.set_text("Connecting...")
        box.pack_start(self.progress_bar, False, False, 5)

        # Status label (shows speed and ETA)
        self.status_label = Gtk.Label(label="")
        self.status_label.set_markup("<i>Please wait...</i>")
        box.pack_start(self.status_label, False, False, 0)

        # Cancel button
        self.cancel_button = Gtk.Button(label="Cancel")
        self.cancel_button.connect("clicked", self._on_cancel_clicked)
        self.cancel_button.set_halign(Gtk.Align.CENTER)
        self.cancel_button.set_margin_top(10)
        box.pack_start(self.cancel_button, False, False, 0)

        self.show_all()

        # For Whisper, we can't track progress, so pulse
        if engine == "whisper":
            self._pulse_timeout = GLib.timeout_add(100, self._pulse_progress)
        else:
            self._pulse_timeout = None

    def _pulse_progress(self):
        """Pulse the progress bar while downloading (for Whisper)."""
        if self.cancelled:
            return False
        self.progress_bar.pulse()
        return True  # Continue pulsing

    def _on_cancel_clicked(self, widget):
        """Handle cancel button click."""
        self.cancelled = True
        self.cancel_button.set_sensitive(False)
        self.cancel_button.set_label("Cancelling...")
        self.status_label.set_markup("<i>Cancelling download...</i>")

    def update_progress(self, fraction: float, speed_mbps: float, status_text: str):
        """Update the progress bar with actual download progress."""
        if self.cancelled:
            return

        # Stop pulsing if we were pulsing
        if self._pulse_timeout:
            GLib.source_remove(self._pulse_timeout)
            self._pulse_timeout = None

        self.progress_bar.set_fraction(fraction)
        self.progress_bar.set_text(f"{fraction * 100:.0f}%")
        self.status_label.set_markup(f"<i>{status_text}</i>")

    def set_complete(self, success: bool, message: str = ""):
        """Mark download as complete."""
        if self._pulse_timeout:
            GLib.source_remove(self._pulse_timeout)
            self._pulse_timeout = None

        # Hide cancel button
        self.cancel_button.hide()

        if success:
            self.progress_bar.set_fraction(1.0)
            self.progress_bar.set_text("Complete!")
            self.status_label.set_markup("<b>✓ Model ready to use</b>")
        else:
            self.progress_bar.set_fraction(0)
            self.progress_bar.set_text("Failed")
            if "cancelled" in message.lower():
                self.status_label.set_markup("<span color='orange'>✗ Download cancelled</span>")
            else:
                self.status_label.set_markup(f"<span color='red'>✗ {message}</span>")

        # Allow closing now
        self.set_deletable(True)
        self.add_button("OK", Gtk.ResponseType.OK)


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
        self._initializing = True  # Flag to prevent auto-apply during initialization

        self.add_buttons(
            Gtk.STOCK_CLOSE,
            Gtk.ResponseType.CLOSE,
        )
        self.set_default_size(450, 400)
        self.set_border_width(10)

        # --- UI Elements ---
        self.grid = Gtk.Grid(column_spacing=10, row_spacing=8)
        self.get_content_area().add(self.grid)

        row = 0

        # ==================== AUDIO INPUT SECTION (TOP) ====================
        audio_label = Gtk.Label(label="<b>Audio Input</b>", use_markup=True, halign=Gtk.Align.START)
        self.grid.attach(audio_label, 0, row, 2, 1)
        row += 1

        # Audio device selection
        audio_device_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        audio_device_box.pack_start(
            Gtk.Label(label="Input Device:", halign=Gtk.Align.START), False, False, 0
        )

        self.audio_device_combo = Gtk.ComboBoxText()
        self.audio_device_combo.set_tooltip_text(
            "Select the microphone to use for voice recognition.\n"
            "If you're having issues with audio detection, try different devices."
        )
        self._populate_audio_devices()
        self.audio_device_combo.connect("changed", self._on_audio_device_changed)
        audio_device_box.pack_start(self.audio_device_combo, True, True, 0)

        # Refresh button
        refresh_btn = Gtk.Button()
        refresh_btn.set_image(Gtk.Image.new_from_icon_name("view-refresh", Gtk.IconSize.BUTTON))
        refresh_btn.set_tooltip_text("Refresh audio device list")
        refresh_btn.connect("clicked", self._on_refresh_audio_devices)
        audio_device_box.pack_start(refresh_btn, False, False, 0)

        self.grid.attach(audio_device_box, 0, row, 2, 1)
        row += 1

        # Audio level indicator and test button
        audio_test_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        level_label = Gtk.Label(label="Level:", halign=Gtk.Align.START)
        audio_test_box.pack_start(level_label, False, False, 0)

        self.audio_level_bar = Gtk.LevelBar()
        self.audio_level_bar.set_min_value(0)
        self.audio_level_bar.set_max_value(100)
        self.audio_level_bar.set_value(0)
        self.audio_level_bar.set_size_request(150, -1)
        audio_test_box.pack_start(self.audio_level_bar, True, True, 0)

        self.test_audio_btn = Gtk.Button(label="Test Mic")
        self.test_audio_btn.set_tooltip_text(
            "Test the selected microphone for 2 seconds.\n"
            "Speak into your microphone to verify it's working."
        )
        self.test_audio_btn.connect("clicked", self._on_test_audio_clicked)
        audio_test_box.pack_start(self.test_audio_btn, False, False, 0)

        self.grid.attach(audio_test_box, 0, row, 2, 1)
        row += 1

        # Audio test status label
        self.audio_test_status = Gtk.Label(label="", use_markup=True, halign=Gtk.Align.START)
        self.grid.attach(self.audio_test_status, 0, row, 2, 1)
        row += 1

        # ==================== SEPARATOR ====================
        self.grid.attach(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), 0, row, 2, 1)
        row += 1

        # ==================== SPEECH ENGINE SECTION ====================
        engine_label = Gtk.Label(
            label="<b>Speech Engine</b>", use_markup=True, halign=Gtk.Align.START
        )
        self.grid.attach(engine_label, 0, row, 2, 1)
        row += 1

        # Engine Selection
        self.grid.attach(Gtk.Label(label="Engine:", halign=Gtk.Align.START), 0, row, 1, 1)
        self.engine_combo = Gtk.ComboBoxText()
        self.grid.attach(self.engine_combo, 1, row, 1, 1)
        row += 1

        # Model Size Selection
        self.grid.attach(Gtk.Label(label="Model Size:", halign=Gtk.Align.START), 0, row, 1, 1)
        self.model_combo = Gtk.ComboBoxText()
        self.grid.attach(self.model_combo, 1, row, 1, 1)
        row += 1

        # Model legend (applies to both engines)
        model_legend = Gtk.Label(
            label="<small>✓ = Downloaded  ↓ = Will download  ★ = Recommended</small>",
            use_markup=True,
            halign=Gtk.Align.END,
        )
        self.grid.attach(model_legend, 0, row, 2, 1)
        row += 1

        # Whisper Info Box (initially hidden)
        self.whisper_info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.whisper_info_box.pack_start(
            Gtk.Label(
                label="<b>Whisper Model Info</b>",
                use_markup=True,
                halign=Gtk.Align.START,
            ),
            False,
            False,
            5,
        )

        # Model info label (will be updated based on selection)
        self.whisper_model_info_label = Gtk.Label(
            label="",
            use_markup=True,
            halign=Gtk.Align.START,
            wrap=True,
        )
        self.whisper_info_box.pack_start(self.whisper_model_info_label, False, False, 0)

        # Recommendation label
        self.whisper_recommendation_label = Gtk.Label(
            label="",
            use_markup=True,
            halign=Gtk.Align.START,
            wrap=True,
        )
        self.whisper_info_box.pack_start(self.whisper_recommendation_label, False, False, 5)

        self.grid.attach(self.whisper_info_box, 0, row, 2, 1)
        row += 1

        # Add model change handler
        self.model_combo.connect("changed", self._on_model_changed)

        # ==================== SEPARATOR ====================
        self.grid.attach(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), 0, row, 2, 1)
        row += 1

        # ==================== RECOGNITION SETTINGS SECTION ====================
        recognition_label = Gtk.Label(
            label="<b>Recognition Settings</b>", use_markup=True, halign=Gtk.Align.START
        )
        self.grid.attach(recognition_label, 0, row, 2, 1)
        row += 1

        # VAD Sensitivity (controls how sensitive the mic is to speech vs silence)
        self.grid.attach(
            Gtk.Label(label="VAD Sensitivity (1-5):", halign=Gtk.Align.START), 0, row, 1, 1
        )
        self.vad_spin = Gtk.SpinButton.new_with_range(1, 5, 1)
        self.vad_spin.set_tooltip_text("Higher = more sensitive to quiet speech")
        self.vad_spin.connect("value-changed", self._on_vad_changed)
        self.grid.attach(self.vad_spin, 1, row, 1, 1)
        row += 1

        # Silence Timeout (how long to wait before processing)
        self.grid.attach(
            Gtk.Label(label="Silence Timeout (sec):", halign=Gtk.Align.START), 0, row, 1, 1
        )
        self.silence_spin = Gtk.SpinButton.new_with_range(0.5, 5.0, 0.1)
        self.silence_spin.set_digits(1)
        self.silence_spin.set_tooltip_text("Wait time after silence before processing speech")
        self.silence_spin.connect("value-changed", self._on_silence_changed)
        self.grid.attach(self.silence_spin, 1, row, 1, 1)
        row += 1

        # VOSK Model info label (shown only for VOSK)
        self.vosk_model_info_label = Gtk.Label(
            label="",
            use_markup=True,
            halign=Gtk.Align.START,
            wrap=True,
        )
        self.grid.attach(self.vosk_model_info_label, 0, row, 2, 1)
        row += 1

        # VOSK Recommendation label (shown only for VOSK)
        self.vosk_recommendation_label = Gtk.Label(
            label="",
            use_markup=True,
            halign=Gtk.Align.START,
            wrap=True,
        )
        self.grid.attach(self.vosk_recommendation_label, 0, row, 2, 1)
        row += 1

        # Legacy recognition settings box (for compatibility)
        self.recognition_settings_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.recognition_grid = Gtk.Grid(column_spacing=10, row_spacing=10)

        # ==================== SEPARATOR ====================
        self.grid.attach(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), 0, row, 2, 1)
        row += 1

        # ==================== TEST RECOGNITION SECTION ====================
        test_label = Gtk.Label(
            label="<b>Test Recognition</b>", use_markup=True, halign=Gtk.Align.START
        )
        self.grid.attach(test_label, 0, row, 2, 1)
        row += 1

        scrolled_window = Gtk.ScrolledWindow(hexpand=True, vexpand=True)
        scrolled_window.set_min_content_height(80)
        self.test_textview = Gtk.TextView(
            editable=False, cursor_visible=False, wrap_mode=Gtk.WrapMode.WORD
        )
        self.test_buffer = self.test_textview.get_buffer()
        scrolled_window.add(self.test_textview)
        self.grid.attach(scrolled_window, 0, row, 2, 1)
        row += 1

        self.test_button = Gtk.Button(label="Start Test (3 seconds)")
        self.test_button.connect("clicked", self._on_test_clicked)
        self.grid.attach(self.test_button, 0, row, 2, 1)
        row += 1

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
            logger.warning("Could not set engine by ID, trying by index")
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

        # Show everything first
        self.show_all()

        # Then show/hide engine-specific sections (must be after show_all)
        self._update_engine_specific_ui()

        # Initialization complete - enable auto-apply
        self._initializing = False

    def _get_current_settings(self):
        """Get current settings from config manager."""
        # Always reload config from disk to reflect latest saved settings
        self.config_manager.load_config()
        settings = self.config_manager.get_settings()

        # Use .get with defaults for robustness
        sr_settings = settings.get("speech_recognition", {})
        engine = sr_settings.get("engine", "vosk")
        # Get model size for the specific engine
        model_size = self.config_manager.get_model_size_for_engine(engine)
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

        # Get the saved model size for THIS specific engine (not the generic one)
        saved_model_for_engine = self.config_manager.get_model_size_for_engine(engine)
        logger.info(f"Saved model for {engine}: {saved_model_for_engine}")

        # Track which models are downloaded and find smallest downloaded
        downloaded_models = []
        smallest_model = None

        # Add model sizes for this engine
        if engine in ENGINE_MODELS:
            # Add all options for this engine
            for size in ENGINE_MODELS[engine]:
                if engine == "whisper" and size in WHISPER_MODEL_INFO:
                    info = WHISPER_MODEL_INFO[size]
                    is_downloaded = _is_whisper_model_downloaded(size)
                    status = "✓" if is_downloaded else "↓"
                    display_text = f"{size.capitalize()} ({_format_size(info['size_mb'])}) {status}"
                    if is_downloaded:
                        downloaded_models.append(size)
                    if smallest_model is None:
                        smallest_model = size
                elif engine == "vosk" and size in VOSK_MODEL_INFO:
                    info = VOSK_MODEL_INFO[size]
                    is_downloaded = _is_vosk_model_downloaded(size)
                    status = "✓" if is_downloaded else "↓"
                    display_text = f"{size.capitalize()} ({_format_size(info['size_mb'])}) {status}"
                    if is_downloaded:
                        downloaded_models.append(size)
                    if smallest_model is None:
                        smallest_model = size
                else:
                    display_text = size.capitalize()
                # Use lowercase as ID, display text with info
                self.model_combo.append(size.capitalize(), display_text)

            # Determine which model to select:
            # 1. If saved model for this engine is downloaded, use it
            # 2. Else if saved model for this engine exists (even if not downloaded), use it
            #    (user will be prompted to download when applying)
            # 3. Else if any model is downloaded, use the smallest downloaded
            # 4. Else use the smallest model for this engine
            saved_model = saved_model_for_engine.lower()

            # Check if the saved model is valid for this engine
            valid_models = [m.lower() for m in ENGINE_MODELS.get(engine, [])]

            if saved_model in valid_models:
                # Use the saved model for this engine (whether downloaded or not)
                model_to_set = saved_model.capitalize()
            elif downloaded_models:
                # Saved model isn't valid for this engine, use smallest downloaded
                model_to_set = downloaded_models[0].capitalize()
            else:
                # No downloaded models, use the smallest model for this engine
                model_to_set = smallest_model.capitalize() if smallest_model else "Small"

            logger.info(
                f"Setting active model to: {model_to_set} (saved_for_engine={saved_model}, "
                f"valid={saved_model in valid_models}, downloaded={downloaded_models})"
            )

            # Try to set by ID
            if not self.model_combo.set_active_id(model_to_set):
                logger.warning(f"Could not set model by ID '{model_to_set}', trying by text")
                # Find by text as fallback
                model = self.model_combo.get_model()
                model_found = False
                for i, row in enumerate(model):
                    if row[0].lower() == model_to_set.lower():
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
        self._update_whisper_info()
        self._auto_apply_settings()

    def _on_model_changed(self, widget):
        """Handle changes in the selected model."""
        engine_text = self.engine_combo.get_active_text()
        if engine_text:
            engine = engine_text.lower()
            if engine == "whisper":
                self._update_whisper_info()
            elif engine == "vosk":
                self._update_vosk_info()
        self._auto_apply_settings()

    def _on_vad_changed(self, widget):
        """Handle changes in VAD sensitivity."""
        self._auto_apply_settings()

    def _on_silence_changed(self, widget):
        """Handle changes in silence timeout."""
        self._auto_apply_settings()

    def _auto_apply_settings(self):
        """Automatically apply settings when changed."""
        if self._initializing:
            return  # Don't auto-apply during initialization

        if self._test_active:
            return  # Don't apply during testing

        settings = self.get_selected_settings()
        engine = settings.get("engine", "vosk")
        model_name = settings.get("model_size", "small")

        # Check if model needs to be downloaded
        needs_download = False
        if engine == "whisper" and not _is_whisper_model_downloaded(model_name):
            needs_download = True
            model_info = WHISPER_MODEL_INFO.get(model_name, {"size_mb": 500})
        elif engine == "vosk" and not _is_vosk_model_downloaded(model_name):
            needs_download = True
            model_info = VOSK_MODEL_INFO.get(model_name, {"size_mb": 50})

        if needs_download:
            # Show download dialog for models that need downloading
            logger.info(f"Model {model_name} needs download, showing progress dialog")
            download_dialog = ModelDownloadDialog(
                self, model_name, model_info["size_mb"], engine=engine
            )

            def progress_callback(fraction, speed, status):
                """Update UI with download progress."""
                GLib.idle_add(download_dialog.update_progress, fraction, speed, status)

            def download_and_apply():
                try:
                    # Set up progress callback for downloads (both VOSK and Whisper)
                    self.speech_engine.set_download_progress_callback(progress_callback)

                    # Check for cancellation periodically
                    def check_cancelled():
                        if download_dialog.cancelled:
                            self.speech_engine.cancel_download()
                        return not download_dialog.cancelled

                    # Start cancellation checker
                    cancel_check_id = GLib.timeout_add(100, check_cancelled)

                    try:
                        self._apply_settings_internal(settings)
                        GLib.idle_add(download_dialog.set_complete, True, "")
                        # Refresh model list after download to update icons
                        GLib.idle_add(self._populate_model_options)
                    finally:
                        GLib.source_remove(cancel_check_id)
                        self.speech_engine.set_download_progress_callback(None)

                except Exception as e:
                    error_msg = str(e)
                    if "cancelled" in error_msg.lower():
                        GLib.idle_add(download_dialog.set_complete, False, "Download cancelled")
                    elif engine == "whisper" and "no module named" in error_msg.lower():
                        GLib.idle_add(download_dialog.set_complete, False, "Whisper not installed")
                        GLib.idle_add(self._show_whisper_install_dialog)
                    else:
                        GLib.idle_add(download_dialog.set_complete, False, error_msg[:100])

            threading.Thread(target=download_and_apply, daemon=True).start()
            download_dialog.run()
            download_dialog.destroy()
            return

        # Model already downloaded, just apply settings directly
        logger.info(f"Auto-applying settings: {settings}")

        try:
            # Update config manager
            self.config_manager.update_speech_recognition_settings(settings)
            self.config_manager.save_settings()

            # Reconfigure speech engine (don't stop/start if idle)
            self.speech_engine.reconfigure(**settings)
            logger.info("Settings auto-applied successfully")
        except Exception as e:
            logger.error(f"Failed to auto-apply settings: {e}")

    def _update_engine_specific_ui(self):
        """Show/hide UI elements specific to the selected engine."""
        selected_engine_text = self.engine_combo.get_active_text()
        if not selected_engine_text:
            self.recognition_settings_box.hide()
            self.whisper_info_box.hide()
            return

        selected_engine = selected_engine_text.lower()

        # Recognition settings (VAD, silence timeout) apply to both engines
        self.recognition_settings_box.show()

        if selected_engine == "vosk":
            # Show VOSK-specific info labels
            self.vosk_model_info_label.show()
            self.vosk_recommendation_label.show()
            self.whisper_info_box.hide()
            self._update_vosk_info()
        elif selected_engine == "whisper":
            # Hide VOSK-specific info labels, show Whisper info
            self.vosk_model_info_label.hide()
            self.vosk_recommendation_label.hide()
            self.whisper_info_box.show()
            self._update_whisper_info()
        else:
            self.recognition_settings_box.hide()
            self.whisper_info_box.hide()

    def _update_whisper_info(self):
        """Update the Whisper model info display."""
        engine_text = self.engine_combo.get_active_text()
        if not engine_text or engine_text.lower() != "whisper":
            return

        model_id = self.model_combo.get_active_id()
        if not model_id:
            return

        model_name = model_id.lower()
        if model_name not in WHISPER_MODEL_INFO:
            return

        info = WHISPER_MODEL_INFO[model_name]
        is_downloaded = _is_whisper_model_downloaded(model_name)

        # Build info text
        if is_downloaded:
            status_text = "<span foreground='green'>✓ Downloaded and ready</span>"
        else:
            status_text = (
                f"<span foreground='orange'>↓ Will download ~{_format_size(info['size_mb'])}</span>"
            )

        info_text = (
            f"<b>{model_name.capitalize()}</b>: {info['desc']}\n"
            f"Parameters: {info['params']}  •  {status_text}"
        )
        self.whisper_model_info_label.set_markup(info_text)

        # Update recommendation
        recommended, reason = _get_recommended_whisper_model()
        if model_name == recommended:
            self.whisper_recommendation_label.set_markup(
                f"<span foreground='green'>★ Recommended for your system: {reason}</span>"
            )
        else:
            self.whisper_recommendation_label.set_markup(
                f"<small>Tip: <b>{recommended.capitalize()}</b> is recommended for your system ({reason})</small>"
            )

    def _update_vosk_info(self):
        """Update the VOSK model info display."""
        engine_text = self.engine_combo.get_active_text()
        if not engine_text or engine_text.lower() != "vosk":
            return

        model_id = self.model_combo.get_active_id()
        if not model_id:
            return

        model_name = model_id.lower()
        if model_name not in VOSK_MODEL_INFO:
            return

        info = VOSK_MODEL_INFO[model_name]
        is_downloaded = _is_vosk_model_downloaded(model_name)

        # Build info text
        if is_downloaded:
            status_text = "<span foreground='green'>✓ Downloaded and ready</span>"
        else:
            status_text = (
                f"<span foreground='orange'>↓ Will download ~{_format_size(info['size_mb'])}</span>"
            )

        info_text = (
            f"<b>{model_name.capitalize()}</b>: {info['desc']}\n"
            f"Size: {_format_size(info['size_mb'])}  •  {status_text}"
        )
        self.vosk_model_info_label.set_markup(info_text)

        # Update recommendation
        recommended, reason = _get_recommended_vosk_model()
        if model_name == recommended:
            self.vosk_recommendation_label.set_markup(
                f"<span foreground='green'>★ Recommended for your system: {reason}</span>"
            )
        else:
            self.vosk_recommendation_label.set_markup(
                f"<small>Tip: <b>{recommended.capitalize()}</b> is recommended for your system ({reason})</small>"
            )

    def get_selected_settings(self) -> dict:
        """Return the currently selected settings from the UI."""
        engine_text = self.engine_combo.get_active_text()
        # Get model by ID (which is the capitalized name) not the display text
        model_id = self.model_combo.get_active_id()

        # Handle cases where combo boxes might be empty (shouldn't happen with defaults)
        engine = engine_text.lower() if engine_text else "vosk"
        # Extract model name from ID (which is the capitalized name like "Small")
        model_size = model_id.lower() if model_id else "small"

        vad = int(self.vad_spin.get_value())
        silence = self.silence_spin.get_value()

        settings = {
            "engine": engine,
            "model_size": model_size,
            "vad_sensitivity": vad,
            "silence_timeout": silence,
        }

        return settings

    def _on_test_clicked(self, widget):
        """Handle click on the test button."""
        if self._test_active:
            logger.warning("Test already in progress.")
            return

        # Ensure settings are applied before testing
        current_config = self.config_manager.get_settings().get("speech_recognition", {})
        selected_settings = self.get_selected_settings()

        # Check if settings in dialog differ from saved config
        # This is a basic check; a more robust diff might be needed
        settings_differ = False
        if current_config.get("engine") != selected_settings.get("engine") or current_config.get(
            "model_size"
        ) != selected_settings.get("model_size"):
            settings_differ = True
        elif selected_settings.get("engine") == "vosk":
            if current_config.get("vad_sensitivity") != selected_settings.get(
                "vad_sensitivity"
            ) or current_config.get("silence_timeout") != selected_settings.get("silence_timeout"):
                settings_differ = True
        # Add checks for other engines if they get specific settings

        if settings_differ:
            # Auto-apply settings before testing
            self.test_buffer.set_text("Applying settings...")
            if not self.apply_settings():
                self.test_buffer.set_text("Failed to apply settings. Please try again.")
                return
            self.test_buffer.set_text("Settings applied. Starting test...")

        self._test_active = True
        self.test_button.set_sensitive(False)
        self.test_button.set_label("Testing... Speak Now!")
        self.test_buffer.set_text("")  # Clear previous results
        self._test_result = ""

        # Save existing text callbacks and replace with test-only callback
        # This prevents the text injector from typing into the dialog during testing
        self._saved_text_callbacks = self.speech_engine.get_text_callbacks()
        self.speech_engine.set_text_callbacks([self._test_text_callback])

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
        separator = " " if current_text.strip() else ""  # Check strip() to avoid leading space
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

        # Restore the original text callbacks (including text injector)
        if hasattr(self, "_saved_text_callbacks"):
            self.speech_engine.set_text_callbacks(self._saved_text_callbacks)
            del self._saved_text_callbacks

        self._test_active = False
        self.test_button.set_sensitive(True)
        self.test_button.set_label("Start Test (3 seconds)")

        # Schedule the "no speech" check after a short delay to allow
        # any pending callbacks to complete first
        GLib.timeout_add(200, self._check_test_result)

        return False  # Remove idle callback

    def _check_test_result(self):
        """Check if any text was captured after all callbacks have run."""
        final_text = self.test_buffer.get_text(
            self.test_buffer.get_start_iter(), self.test_buffer.get_end_iter(), False
        )
        if not final_text.strip():
            self.test_buffer.set_text("(No speech detected during test)")
        return False  # Don't repeat

    def _show_whisper_install_dialog(self):
        """Show a dialog with instructions for installing Whisper."""
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.OK,
            text="Whisper Not Installed",
        )

        install_text = """Whisper AI is not installed. To use Whisper for speech recognition, you need to install it first.

Installation Options:

1. Using the installation script:
   ./install.sh --with-whisper

2. Manual installation in virtual environment:
   source venv/bin/activate
   pip install openai-whisper torch torchaudio

3. If you have SSL issues, try:
   pip install openai-whisper torch torchaudio --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org

Note: Whisper requires significant disk space (~1-3GB) and may take time to download.

For now, the engine has been reverted to VOSK."""

        dialog.format_secondary_text(install_text)
        dialog.run()
        dialog.destroy()

        # Revert the engine selection back to VOSK
        self.engine_combo.set_active_id("Vosk")
        self._populate_model_options()
        self._update_engine_specific_ui()

    def apply_settings(self):
        """Apply the selected settings."""
        settings = self.get_selected_settings()
        logger.info(f"Applying settings: {settings}")

        engine = settings.get("engine", "vosk")
        model_name = settings.get("model_size", "small")

        # Check if we need to download a model
        needs_download = False
        if engine == "whisper" and not _is_whisper_model_downloaded(model_name):
            needs_download = True
            model_info = WHISPER_MODEL_INFO.get(model_name, {"size_mb": 500})
        elif engine == "vosk" and not _is_vosk_model_downloaded(model_name):
            needs_download = True
            model_info = VOSK_MODEL_INFO.get(model_name, {"size_mb": 50})

        if needs_download:
            # Show download dialog
            download_dialog = ModelDownloadDialog(
                self, model_name, model_info["size_mb"], engine=engine
            )

            def progress_callback(fraction, speed, status):
                """Update UI with download progress."""
                GLib.idle_add(download_dialog.update_progress, fraction, speed, status)

            def download_and_apply():
                try:
                    # Set up progress callback for downloads (both VOSK and Whisper)
                    self.speech_engine.set_download_progress_callback(progress_callback)

                    # Check for cancellation periodically
                    def check_cancelled():
                        if download_dialog.cancelled:
                            self.speech_engine.cancel_download()
                        return not download_dialog.cancelled

                    cancel_check_id = GLib.timeout_add(100, check_cancelled)

                    try:
                        self._apply_settings_internal(settings)
                        GLib.idle_add(download_dialog.set_complete, True, "")
                    finally:
                        GLib.source_remove(cancel_check_id)
                        self.speech_engine.set_download_progress_callback(None)

                except Exception as e:
                    error_msg = str(e)
                    if "cancelled" in error_msg.lower():
                        GLib.idle_add(download_dialog.set_complete, False, "Download cancelled")
                    elif engine == "whisper" and "no module named" in error_msg.lower():
                        GLib.idle_add(download_dialog.set_complete, False, "Whisper not installed")
                        GLib.idle_add(self._show_whisper_install_dialog)
                    else:
                        GLib.idle_add(download_dialog.set_complete, False, error_msg[:100])

            threading.Thread(target=download_and_apply, daemon=True).start()
            download_dialog.run()
            download_dialog.destroy()

            # Refresh the model list to show updated download status
            self._populate_model_options()
            return True

        return self._apply_settings_internal(settings)

    def _apply_settings_internal(self, settings: dict) -> bool:
        """Internal method to apply settings."""
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

            # Check if this is a Whisper import error
            if "whisper" in str(e).lower() and "no module named" in str(e).lower():
                self._show_whisper_install_dialog()
            else:
                # Show generic error dialog
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

    def _populate_audio_devices(self):
        """Populate the audio device dropdown with available input devices."""
        # Lazy import to avoid circular dependency
        from ..speech_recognition.recognition_manager import get_audio_input_devices

        self.audio_device_combo.remove_all()

        # Add "System Default" option first
        self.audio_device_combo.append("-1", "System Default")

        # Get available devices
        devices = get_audio_input_devices()

        for device_index, device_name, is_default in devices:
            label = device_name
            if is_default:
                label += " (default)"
            self.audio_device_combo.append(str(device_index), label)

        # Get saved device from config
        saved_device = self.config_manager.get("audio", "device_index", None)

        if saved_device is None:
            self.audio_device_combo.set_active_id("-1")
        else:
            if not self.audio_device_combo.set_active_id(str(saved_device)):
                # Saved device no longer available, fall back to default
                logger.warning(f"Saved audio device {saved_device} no longer available")
                self.audio_device_combo.set_active_id("-1")

        logger.info(f"Found {len(devices)} audio input devices")

    def _on_refresh_audio_devices(self, widget):
        """Handle refresh button click for audio devices."""
        self._populate_audio_devices()
        self.audio_test_status.set_markup("<i>Device list refreshed</i>")

    def _on_audio_device_changed(self, widget):
        """Handle changes in the selected audio device."""
        if self._initializing:
            return

        device_id = self.audio_device_combo.get_active_id()
        if device_id is None:
            return

        device_index = int(device_id)
        device_name = self.audio_device_combo.get_active_text()

        # Save to config
        if device_index == -1:
            self.config_manager.set("audio", "device_index", None)
            self.config_manager.set("audio", "device_name", None)
        else:
            self.config_manager.set("audio", "device_index", device_index)
            self.config_manager.set("audio", "device_name", device_name)

        self.config_manager.save_settings()

        # Update speech engine
        if device_index == -1:
            self.speech_engine.set_audio_device(None)
        else:
            self.speech_engine.set_audio_device(device_index)

        logger.info(f"Audio device changed to: [{device_index}] {device_name}")
        self.audio_test_status.set_markup(f"<i>Selected: {device_name}</i>")

    def _on_test_audio_clicked(self, widget):
        """Handle test audio button click."""
        self.test_audio_btn.set_sensitive(False)
        self.test_audio_btn.set_label("Testing...")
        self.audio_test_status.set_markup("<i>Recording... speak into your microphone</i>")
        self.audio_level_bar.set_value(0)

        # Get selected device
        device_id = self.audio_device_combo.get_active_id()
        device_index = None if device_id == "-1" else int(device_id)

        def run_test():
            # Lazy import to avoid circular dependency
            from ..speech_recognition.recognition_manager import test_audio_input

            result = test_audio_input(device_index=device_index, duration=2.0)
            GLib.idle_add(self._handle_audio_test_result, result)

        threading.Thread(target=run_test, daemon=True).start()

    def _handle_audio_test_result(self, result: dict):
        """Handle the result of an audio test."""
        self.test_audio_btn.set_sensitive(True)
        self.test_audio_btn.set_label("Test Mic")

        if result.get("success"):
            max_level = result.get("max_amplitude", 0)
            has_signal = result.get("has_signal", False)

            # Update level bar with max level (normalized to 0-100)
            level_percent = min(100, (max_level / 327.68))
            self.audio_level_bar.set_value(level_percent)

            if has_signal:
                self.audio_test_status.set_markup(
                    f"<span color='green'>✓ Audio detected!</span> "
                    f"Peak level: {level_percent:.0f}%"
                )
            else:
                self.audio_test_status.set_markup(
                    f"<span color='orange'>⚠ Very low audio level</span> "
                    f"(peak: {level_percent:.1f}%)\n"
                    "<small>Check if microphone is muted or try a different device</small>"
                )
        else:
            error_msg = result.get("error", "Unknown error")
            self.audio_test_status.set_markup(
                f"<span color='red'>✗ Test failed:</span> {error_msg}"
            )

        return False  # Don't repeat
