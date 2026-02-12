"""
Settings Dialog for Vocalinux.

Allows users to configure speech recognition engine, model size,
and other relevant parameters.

UX Design Notes:
- Follows GNOME Human Interface Guidelines (HIG) for modern desktop look
- Uses preference-page style layout with clearly grouped sections
- Implements instant-apply pattern: settings apply immediately when changed
- Close button only (no Apply/Cancel) - consistent with GNOME Settings app
- Provides real-time progress feedback for recognition state
- Multi-modal feedback (text + icon + audio level) for accessibility
- Modal dialog for model downloads (explicit confirmation for large downloads)
"""

import logging
import os
import threading
import time
from typing import TYPE_CHECKING

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
# Need GLib for idle_add
from gi.repository import Gdk, GLib, Gtk, Pango  # noqa: E402

from ..common_types import RecognitionState  # noqa: E402
from ..utils.vosk_model_info import SUPPORTED_LANGUAGES, VOSK_MODEL_INFO  # noqa: E402
from ..utils.whispercpp_model_info import (
    WHISPERCPP_MODEL_INFO,
    detect_compute_backend,
    get_backend_display_name,
)
from ..utils.whispercpp_model_info import get_recommended_model as get_recommended_whispercpp_model
from ..utils.whispercpp_model_info import is_model_downloaded as is_whispercpp_model_downloaded
from .keyboard_backends import SHORTCUT_DISPLAY_NAMES, SUPPORTED_SHORTCUTS  # noqa: E402

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
    ],  # Note: 'large' maps to medium internally, as higher version wasn't available
    "whisper": [
        "tiny",
        "base",
        "small",
        "medium",
        "large",
    ],  # Add more whisper sizes if needed
    "whisper_cpp": [
        "tiny",
        "base",
        "small",
        "medium",
        "large",
    ],  # whisper.cpp models (ggml format)
}

# Whisper model metadata for display
WHISPER_MODEL_INFO = {
    "tiny": {"size_mb": 75, "desc": "Fastest, lowest accuracy", "params": "39M"},
    "base": {"size_mb": 142, "desc": "Fast, good for basic use", "params": "74M"},
    "small": {"size_mb": 466, "desc": "Balanced speed/accuracy", "params": "244M"},
    "medium": {"size_mb": 1500, "desc": "High accuracy, slower", "params": "769M"},
    "large": {"size_mb": 2900, "desc": "Highest accuracy, slowest", "params": "1550M"},
}


def format_engine_display_name(engine_id):
    """
    Format engine ID for display in the UI.
    
    Args:
        engine_id: The engine identifier (e.g., "whisper_cpp", "vosk")
        
    Returns:
        User-friendly display name (e.g., "whisper.cpp", "Vosk")
    """
    display_names = {
        "whisper_cpp": "whisper.cpp",
        "whisper": "Whisper",
        "vosk": "VOSK",
    }
    return display_names.get(engine_id, engine_id.capitalize())


def get_available_engines():
    """
    Detect which speech recognition engines are available/installed.
    Returns a dictionary of engine_name -> availability (bool).
    """
    engines = {"vosk": False, "whisper": False, "whisper_cpp": False}

    # Check VOSK
    try:
        import vosk

        engines["vosk"] = True
    except ImportError:
        pass

    # Check OpenAI Whisper
    try:
        import whisper

        engines["whisper"] = True
    except ImportError:
        pass

    # Check whisper.cpp (pywhispercpp)
    try:
        from pywhispercpp.model import Model

        engines["whisper_cpp"] = True
    except ImportError:
        pass

    logger.debug(f"Available engines: {engines}")
    return engines


# Models directory
MODELS_DIR = os.path.expanduser("~/.local/share/vocalinux/models")
SYSTEM_MODELS_DIRS = [
    "/usr/local/share/vocalinux/models",
    "/usr/share/vocalinux/models",
]

# CSS for modern styling
SETTINGS_CSS = """
/* Modern GNOME-style settings dialog */
.settings-dialog {
    background-color: @theme_bg_color;
}

/* Preference group styling - card-like appearance */
.preferences-group {
    background-color: @theme_base_color;
    border-radius: 12px;
    padding: 0;
    margin: 6px 0;
    border: 1px solid alpha(@borders, 0.5);
}

.preferences-group-title {
    font-weight: bold;
    font-size: 0.9em;
    color: @theme_unfocused_fg_color;
    padding: 12px 16px 6px 16px;
    margin: 0;
}

/* Row styling */
.preference-row {
    padding: 12px 16px;
    min-height: 32px;
    border-bottom: 1px solid alpha(@borders, 0.3);
}

.preference-row:last-child {
    border-bottom: none;
}

.preference-row:hover {
    background-color: alpha(@theme_selected_bg_color, 0.1);
}

.preference-row-title {
    font-weight: 500;
}

.preference-row-subtitle {
    font-size: 0.85em;
    color: @theme_unfocused_fg_color;
}

/* Status indicators */
.status-success {
    color: #26a269;
}

.status-warning {
    color: #e5a50a;
}

.status-error {
    color: #c01c28;
}

.status-info {
    color: @theme_unfocused_fg_color;
}

/* Test area styling */
.test-area {
    background-color: @theme_base_color;
    border-radius: 8px;
    padding: 12px;
    border: 1px solid alpha(@borders, 0.5);
}

.test-textview {
    font-family: monospace;
    font-size: 0.95em;
    padding: 8px;
    background-color: alpha(@theme_bg_color, 0.5);
    border-radius: 6px;
}

/* Level bars */
levelbar block.filled {
    background-color: @theme_selected_bg_color;
    border-radius: 3px;
}

levelbar block.empty {
    background-color: alpha(@theme_fg_color, 0.1);
    border-radius: 3px;
}

/* Combo boxes and spin buttons */
combobox button,
spinbutton {
    min-height: 32px;
    border-radius: 6px;
}

/* Section headers */
.section-header {
    font-size: 1.1em;
    font-weight: bold;
    margin-top: 12px;
    margin-bottom: 6px;
}

/* Info box styling */
.info-box {
    background-color: alpha(@theme_selected_bg_color, 0.1);
    border-radius: 8px;
    padding: 12px;
    border-left: 4px solid @theme_selected_bg_color;
}

.info-box-warning {
    background-color: alpha(#e5a50a, 0.1);
    border-left-color: #e5a50a;
}

/* Recognition status */
.recognition-idle {
    color: @theme_unfocused_fg_color;
}

.recognition-listening {
    color: #26a269;
}

.recognition-processing {
    color: #e5a50a;
}

.recognition-error {
    color: #c01c28;
}

/* Buttons */
.suggested-action {
    background-color: @theme_selected_bg_color;
    color: @theme_selected_fg_color;
}

.flat-button {
    background: transparent;
    border: none;
    padding: 8px;
    border-radius: 6px;
}

.flat-button:hover {
    background-color: alpha(@theme_fg_color, 0.1);
}

/* Scrolled content */
.scrolled-content {
    background-color: transparent;
}

/* Model info card */
.model-info-card {
    background-color: alpha(@theme_base_color, 0.8);
    border-radius: 8px;
    padding: 12px 16px;
    margin: 8px 0;
}

.model-info-title {
    font-weight: bold;
    font-size: 1.0em;
}

.model-info-subtitle {
    font-size: 0.9em;
    color: @theme_unfocused_fg_color;
}

/* Tip styling */
.tip-label {
    font-size: 0.85em;
    color: @theme_unfocused_fg_color;
    font-style: italic;
}

.tip-highlight {
    font-weight: bold;
    color: @theme_selected_bg_color;
}
"""


def _setup_css():
    """Set up CSS styling for the settings dialog."""
    css_provider = Gtk.CssProvider()
    css_provider.load_from_data(SETTINGS_CSS.encode())
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(),
        css_provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
    )


def _prevent_scroll_on_hover(widget: Gtk.Widget):
    """
    Prevent scroll events from modifying widget values when hovering.

    This fixes a common GTK UX issue where scrolling through a settings dialog
    accidentally changes ComboBox or SpinButton values when the mouse happens
    to be over them. The widget will only respond to scroll events after being
    explicitly clicked/focused.

    Args:
        widget: The widget to prevent scroll events on (ComboBox, SpinButton, etc.)
    """

    def on_scroll(widget, event):
        # Only process scroll if widget has explicit focus
        if not widget.has_focus():
            # Stop propagation to prevent value changes
            return True
        return False

    widget.connect("scroll-event", on_scroll)

    # Also prevent focus-on-hover behavior
    widget.set_can_focus(True)


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


def _is_vosk_model_downloaded(size: str, language: str) -> bool:
    """Check if a VOSK model is downloaded."""
    if size not in VOSK_MODEL_INFO:
        return False

    # Auto-detect is not supported by VOSK, fall back to en-us
    if language == "auto" or language not in VOSK_MODEL_INFO[size]["languages"]:
        language = "en-us"

    model_name = VOSK_MODEL_INFO[size]["languages"][language]

    # Check user's local models directory
    user_model_path = os.path.join(MODELS_DIR, model_name)
    if os.path.exists(user_model_path):
        return True

    # Check system-wide installation directories
    for system_dir in SYSTEM_MODELS_DIRS:
        system_model_path = os.path.join(system_dir, model_name)
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


class PreferencesGroup(Gtk.Box):
    """A card-style group of preferences, similar to libadwaita's AdwPreferencesGroup."""

    def __init__(self, title: str = "", description: str = ""):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.get_style_context().add_class("preferences-group")

        # Header with title
        if title:
            header_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            header_box.set_margin_top(12)
            header_box.set_margin_bottom(4)
            header_box.set_margin_start(16)
            header_box.set_margin_end(16)

            title_label = Gtk.Label(label=title, xalign=0)
            title_label.get_style_context().add_class("preferences-group-title")
            header_box.pack_start(title_label, False, False, 0)

            if description:
                desc_label = Gtk.Label(label=description, xalign=0, wrap=True)
                desc_label.get_style_context().add_class("preference-row-subtitle")
                header_box.pack_start(desc_label, False, False, 0)

            self.pack_start(header_box, False, False, 0)

        # Content area with listbox for rows
        self.listbox = Gtk.ListBox()
        self.listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.listbox.set_activate_on_single_click(False)
        self.pack_start(self.listbox, False, False, 0)

    def add_row(self, widget):
        """Add a widget as a row in the preferences group."""
        self.listbox.add(widget)


class PreferenceRow(Gtk.ListBoxRow):
    """A single preference row with title, subtitle, and a control widget."""

    def __init__(
        self,
        title: str,
        subtitle: str = "",
        widget: Gtk.Widget = None,
        activatable: bool = False,
    ):
        super().__init__()
        self.set_activatable(activatable)
        self.get_style_context().add_class("preference-row")

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        hbox.set_margin_top(12)
        hbox.set_margin_bottom(12)
        hbox.set_margin_start(16)
        hbox.set_margin_end(16)

        # Text container (title + subtitle)
        text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        text_box.set_valign(Gtk.Align.CENTER)

        title_label = Gtk.Label(label=title, xalign=0)
        title_label.get_style_context().add_class("preference-row-title")
        text_box.pack_start(title_label, False, False, 0)

        if subtitle:
            subtitle_label = Gtk.Label(label=subtitle, xalign=0, wrap=True)
            subtitle_label.get_style_context().add_class("preference-row-subtitle")
            subtitle_label.set_max_width_chars(40)
            subtitle_label.set_line_wrap(True)
            subtitle_label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
            text_box.pack_start(subtitle_label, False, False, 0)

        hbox.pack_start(text_box, True, True, 0)

        # Control widget on the right
        if widget:
            widget.set_valign(Gtk.Align.CENTER)
            hbox.pack_end(widget, False, False, 0)

        self.add(hbox)


class ModelDownloadDialog(Gtk.Dialog):
    """Dialog showing model download progress with cancel support."""

    def __init__(
        self,
        parent,
        model_name: str,
        model_size_mb: int,
        engine: str = "whisper",
        language: str = "en-us",
    ):
        super().__init__(
            title=f"Downloading {model_name.capitalize()} Model",
            transient_for=parent,
            flags=Gtk.DialogFlags.MODAL,
        )
        self.set_default_size(450, 200)
        self.set_deletable(False)  # Prevent closing during download

        self.cancelled = False
        self.engine = engine
        self.model_name = model_name

        engine_display = engine.upper() if engine == "vosk" else engine.capitalize()

        box = self.get_content_area()
        box.set_spacing(16)
        box.set_margin_start(24)
        box.set_margin_end(24)
        box.set_margin_top(24)
        box.set_margin_bottom(20)

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
        box.pack_start(self.progress_bar, False, False, 8)

        # Status label (shows speed and ETA)
        self.status_label = Gtk.Label(label="")
        self.status_label.set_markup("<i>Please wait...</i>")
        self.status_label.get_style_context().add_class("status-info")
        box.pack_start(self.status_label, False, False, 0)

        # Cancel button
        self.cancel_button = Gtk.Button(label="Cancel")
        self.cancel_button.connect("clicked", self._on_cancel_clicked)
        self.cancel_button.set_halign(Gtk.Align.CENTER)
        self.cancel_button.set_margin_top(12)
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
            self.status_label.set_markup(
                "<span foreground='#26a269'><b>✓ Model ready to use</b></span>"
            )
        else:
            self.progress_bar.set_fraction(0)
            self.progress_bar.set_text("Failed")
            if "cancelled" in message.lower():
                self.status_label.set_markup(
                    "<span foreground='#e5a50a'>✗ Download cancelled</span>"
                )
            else:
                self.status_label.set_markup(f"<span foreground='#c01c28'>✗ {message}</span>")

        # Allow closing now
        self.set_deletable(True)
        self.add_button("OK", Gtk.ResponseType.OK)


class SettingsDialog(Gtk.Dialog):
    """Modern GTK Dialog for configuring Vocalinux settings."""

    def __init__(
        self,
        parent: Gtk.Window,
        config_manager: "ConfigManager",
        speech_engine: "SpeechRecognitionManager",
        shortcut_update_callback: callable = None,
    ):
        super().__init__(title="Vocalinux Settings", transient_for=parent, flags=0)
        self.config_manager = config_manager
        self.speech_engine = speech_engine
        self.shortcut_update_callback = shortcut_update_callback
        self._test_active = False
        self._test_result = ""
        self._initializing = True  # Flag to prevent auto-apply during initialization
        self._populating_models = False  # Flag to prevent model change handler during population
        self._processing_language_change = (
            False  # Flag to prevent recursive language change handling
        )
        self._applying_settings = False  # Flag to prevent recursive settings application

        # Setup CSS styling
        _setup_css()

        # Dialog configuration - Close button only (instant-apply pattern)
        self.add_button("_Close", Gtk.ResponseType.CLOSE)
        # Calculate dialog size - 75% of screen height for better visibility
        display = Gdk.Display.get_default()
        if display:
            monitor = display.get_primary_monitor()
            if not monitor and display.get_n_monitors() > 0:
                monitor = display.get_monitor(0)
            if monitor:
                geometry = monitor.get_geometry()
                screen_height = geometry.height
                screen_width = geometry.width
            else:
                screen_height = 1080  # Default fallback
                screen_width = 1920
        else:
            screen_height = 1080  # Default fallback
            screen_width = 1920
        dialog_height = int(screen_height * 0.75)
        dialog_width = min(520, int(screen_width * 0.8))
        self.set_default_size(dialog_width, dialog_height)
        self.get_style_context().add_class("settings-dialog")

        # Main scrolled window for content
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.get_style_context().add_class("scrolled-content")

        # Main content box
        self.content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.content_box.set_margin_top(16)
        self.content_box.set_margin_bottom(16)
        self.content_box.set_margin_start(16)
        self.content_box.set_margin_end(16)

        scrolled.add(self.content_box)
        self.get_content_area().pack_start(scrolled, True, True, 0)

        # Build UI sections
        self._build_audio_section()
        self._build_engine_section()
        self._build_recognition_section()
        self._build_shortcuts_section()
        self._build_test_section()

        # Load settings and populate UI
        self._load_and_apply_settings()

        # Show everything first
        self.show_all()

        # Then update visibility of engine-specific elements
        self._update_engine_specific_ui()

        # Initialize recognition progress UI
        self.update_recognition_progress("Idle")

        # Connect to recognition manager for progress updates
        self.connect_to_recognition_manager()

        # Initialization complete - enable auto-apply
        self._initializing = False

    def _build_audio_section(self):
        """Build the Audio Input section."""
        group = PreferencesGroup(title="Audio Input")

        # Device selection row
        device_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.audio_device_combo = Gtk.ComboBoxText()
        self.audio_device_combo.set_tooltip_text(
            "Select the microphone to use for voice recognition"
        )
        self.audio_device_combo.set_size_request(250, -1)
        _prevent_scroll_on_hover(self.audio_device_combo)
        device_box.pack_start(self.audio_device_combo, True, True, 0)

        refresh_btn = Gtk.Button.new_from_icon_name("view-refresh-symbolic", Gtk.IconSize.BUTTON)
        refresh_btn.set_tooltip_text("Refresh device list")
        refresh_btn.get_style_context().add_class("flat-button")
        refresh_btn.connect("clicked", self._on_refresh_audio_devices)
        device_box.pack_start(refresh_btn, False, False, 0)

        device_row = PreferenceRow(
            title="Input Device",
            subtitle="Select the microphone for voice recognition",
            widget=device_box,
        )
        group.add_row(device_row)

        # Audio level test row
        level_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.audio_level_bar = Gtk.LevelBar()
        self.audio_level_bar.set_min_value(0)
        self.audio_level_bar.set_max_value(100)
        self.audio_level_bar.set_value(0)
        self.audio_level_bar.set_size_request(150, -1)
        level_box.pack_start(self.audio_level_bar, True, True, 0)

        self.test_audio_btn = Gtk.Button(label="Test")
        self.test_audio_btn.set_tooltip_text("Test the microphone for 2 seconds")
        self.test_audio_btn.connect("clicked", self._on_test_audio_clicked)
        level_box.pack_start(self.test_audio_btn, False, False, 0)

        level_row = PreferenceRow(
            title="Audio Level",
            subtitle="Test your microphone",
            widget=level_box,
        )
        group.add_row(level_row)

        # Status label for audio testing (added below the group)
        self.audio_test_status = Gtk.Label(label="", use_markup=True, xalign=0)
        self.audio_test_status.set_margin_start(16)
        self.audio_test_status.set_margin_top(4)
        self.audio_test_status.get_style_context().add_class("status-info")

        self.content_box.pack_start(group, False, False, 0)
        self.content_box.pack_start(self.audio_test_status, False, False, 0)

        # Populate devices
        self._populate_audio_devices()
        self.audio_device_combo.connect("changed", self._on_audio_device_changed)

    def _build_engine_section(self):
        """Build the Speech Engine section."""
        group = PreferencesGroup(title="Speech Engine")

        # Engine selection
        self.engine_combo = Gtk.ComboBoxText()
        self.engine_combo.set_size_request(180, -1)
        _prevent_scroll_on_hover(self.engine_combo)
        engine_row = PreferenceRow(
            title="Engine",
            subtitle="Speech recognition backend",
            widget=self.engine_combo,
        )
        group.add_row(engine_row)

        # Model size selection
        self.model_combo = Gtk.ComboBoxText()
        self.model_combo.set_size_request(180, -1)
        _prevent_scroll_on_hover(self.model_combo)
        model_row = PreferenceRow(
            title="Model Size",
            subtitle="Larger models are more accurate but slower",
            widget=self.model_combo,
        )
        group.add_row(model_row)

        # Language selection
        self.language_combo = Gtk.ComboBoxText()
        self.language_combo.set_size_request(180, -1)
        self.language_combo.set_tooltip_text("Primary language for speech recognition")
        _prevent_scroll_on_hover(self.language_combo)
        language_row = PreferenceRow(
            title="Language",
            subtitle="Primary language for recognition",
            widget=self.language_combo,
        )
        group.add_row(language_row)

        self.content_box.pack_start(group, False, False, 0)

        # Model info card (shown below the group)
        self.model_info_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.model_info_card.get_style_context().add_class("model-info-card")
        self.model_info_card.set_margin_start(4)
        self.model_info_card.set_margin_end(4)

        self.model_info_title = Gtk.Label(xalign=0)
        self.model_info_title.get_style_context().add_class("model-info-title")
        self.model_info_card.pack_start(self.model_info_title, False, False, 0)

        self.model_info_subtitle = Gtk.Label(xalign=0, wrap=True)
        self.model_info_subtitle.get_style_context().add_class("model-info-subtitle")
        self.model_info_card.pack_start(self.model_info_subtitle, False, False, 0)

        self.model_recommendation = Gtk.Label(xalign=0, wrap=True)
        self.model_recommendation.get_style_context().add_class("tip-label")
        self.model_info_card.pack_start(self.model_recommendation, False, False, 0)

        self.content_box.pack_start(self.model_info_card, False, False, 0)

        # Language warning (for auto-detect)
        self.language_warning = Gtk.Label(label="", use_markup=True, xalign=0)
        self.language_warning.set_margin_start(16)
        self.language_warning.get_style_context().add_class("status-warning")
        self.content_box.pack_start(self.language_warning, False, False, 0)

        # Legend
        legend_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        legend_box.set_halign(Gtk.Align.CENTER)
        legend_box.set_margin_top(4)
        legend_box.set_margin_bottom(4)

        for symbol, text in [("✓", "Downloaded"), ("↓", "Will download"), ("★", "Recommended")]:
            item = Gtk.Label(label=f"{symbol} {text}")
            item.get_style_context().add_class("status-info")
            legend_box.pack_start(item, False, False, 0)

        self.content_box.pack_start(legend_box, False, False, 0)

        # Connect signals
        self.engine_combo.connect("changed", self._on_engine_changed)
        self.model_combo.connect("changed", self._on_model_changed)
        self.language_combo.connect("changed", self._on_language_changed)

    def _build_recognition_section(self):
        """Build the Recognition Settings section."""
        group = PreferencesGroup(title="Recognition Settings")

        # VAD Sensitivity
        self.vad_spin = Gtk.SpinButton.new_with_range(1, 5, 1)
        self.vad_spin.set_tooltip_text("Higher = more sensitive to quiet speech")
        _prevent_scroll_on_hover(self.vad_spin)
        vad_row = PreferenceRow(
            title="VAD Sensitivity",
            subtitle="Voice Activity Detection sensitivity (1-5)",
            widget=self.vad_spin,
        )
        group.add_row(vad_row)

        # Silence Timeout
        self.silence_spin = Gtk.SpinButton.new_with_range(0.5, 5.0, 0.1)
        self.silence_spin.set_digits(1)
        self.silence_spin.set_tooltip_text("Wait time after silence before processing speech")
        _prevent_scroll_on_hover(self.silence_spin)
        silence_row = PreferenceRow(
            title="Silence Timeout",
            subtitle="Seconds of silence before processing",
            widget=self.silence_spin,
        )
        group.add_row(silence_row)

        self.content_box.pack_start(group, False, False, 0)

        # Connect signals
        self.vad_spin.connect("value-changed", self._on_vad_changed)
        self.silence_spin.connect("value-changed", self._on_silence_changed)

    def _build_shortcuts_section(self):
        """Build the Keyboard Shortcuts section."""
        group = PreferencesGroup(
            title="Keyboard Shortcuts",
            description="Configure the shortcut to toggle voice recognition",
        )

        # Shortcut selection combo
        self.shortcut_combo = Gtk.ComboBoxText()
        self.shortcut_combo.set_size_request(200, -1)
        self.shortcut_combo.set_tooltip_text("Select the keyboard shortcut to toggle voice typing")
        _prevent_scroll_on_hover(self.shortcut_combo)

        # Populate shortcut options
        for shortcut_id, display_name in SHORTCUT_DISPLAY_NAMES.items():
            self.shortcut_combo.append(shortcut_id, display_name)

        # Load current shortcut from config
        current_shortcut = self.config_manager.get("shortcuts", "toggle_recognition", "ctrl+ctrl")
        if not self.shortcut_combo.set_active_id(current_shortcut):
            self.shortcut_combo.set_active_id("ctrl+ctrl")

        shortcut_row = PreferenceRow(
            title="Toggle Recognition",
            subtitle="Press this shortcut twice quickly to start/stop",
            widget=self.shortcut_combo,
        )
        group.add_row(shortcut_row)

        self.content_box.pack_start(group, False, False, 0)

        # Info box about the shortcut
        info_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        info_box.get_style_context().add_class("info-box")
        info_box.set_margin_start(4)
        info_box.set_margin_end(4)
        info_box.set_margin_top(4)

        info_icon = Gtk.Image.new_from_icon_name("dialog-information-symbolic", Gtk.IconSize.MENU)
        info_box.pack_start(info_icon, False, False, 0)

        self.shortcut_info_label = Gtk.Label(
            label="Changes take effect immediately. Double-tap the key to toggle voice typing.",
            xalign=0,
            wrap=True,
        )
        self.shortcut_info_label.get_style_context().add_class("tip-label")
        info_box.pack_start(self.shortcut_info_label, True, True, 0)

        self.content_box.pack_start(info_box, False, False, 0)

        # Connect signal
        self.shortcut_combo.connect("changed", self._on_shortcut_changed)

    def _on_shortcut_changed(self, widget):
        """Handle shortcut selection change."""
        if self._initializing:
            return

        shortcut_id = self.shortcut_combo.get_active_id()
        if not shortcut_id:
            return

        # Save to config
        self.config_manager.set("shortcuts", "toggle_recognition", shortcut_id)
        self.config_manager.save_settings()

        display_name = SHORTCUT_DISPLAY_NAMES.get(shortcut_id, shortcut_id)
        logger.info(f"Keyboard shortcut changed to: {display_name}")

        # Try to apply the shortcut change live
        if self.shortcut_update_callback:
            success = self.shortcut_update_callback(shortcut_id)
            if success:
                self.shortcut_info_label.set_markup(
                    f"<span foreground='#26a269'>Shortcut updated to <b>{display_name}</b>. "
                    f"Active now!</span>"
                )
            else:
                self.shortcut_info_label.set_markup(
                    f"<i>Shortcut updated to <b>{display_name}</b>. "
                    f"Restart the app for the change to take full effect.</i>"
                )
        else:
            # No callback provided, fall back to restart message
            self.shortcut_info_label.set_markup(
                f"<i>Shortcut updated to <b>{display_name}</b>. "
                f"Restart the app for the change to take full effect.</i>"
            )

    def _build_test_section(self):
        """Build the Test Recognition section."""
        group = PreferencesGroup(title="Test Recognition")

        # Test area inside the group's listbox as a custom row
        test_container = Gtk.ListBoxRow()
        test_container.set_activatable(False)
        test_container.get_style_context().add_class("preference-row")

        test_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        test_box.set_margin_top(12)
        test_box.set_margin_bottom(12)
        test_box.set_margin_start(16)
        test_box.set_margin_end(16)

        # Text view for test results
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_min_content_height(80)
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.get_style_context().add_class("test-area")

        self.test_textview = Gtk.TextView()
        self.test_textview.set_editable(False)
        self.test_textview.set_cursor_visible(False)
        self.test_textview.set_wrap_mode(Gtk.WrapMode.WORD)
        self.test_textview.get_style_context().add_class("test-textview")
        self.test_buffer = self.test_textview.get_buffer()
        scrolled_window.add(self.test_textview)
        test_box.pack_start(scrolled_window, True, True, 0)

        # Test button
        self.test_button = Gtk.Button(label="Start Test (3 seconds)")
        self.test_button.get_style_context().add_class("suggested-action")
        self.test_button.connect("clicked", self._on_test_clicked)
        test_box.pack_start(self.test_button, False, False, 0)

        test_container.add(test_box)
        group.listbox.add(test_container)

        self.content_box.pack_start(group, False, False, 0)

        # Recognition Progress section
        progress_group = PreferencesGroup(title="Recognition Status")

        # Status row
        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.recognition_status_label = Gtk.Label(label="Idle", xalign=0)
        status_box.pack_start(self.recognition_status_label, True, True, 0)

        self.recognition_indicator = Gtk.Image.new_from_icon_name(
            "media-record-symbolic", Gtk.IconSize.MENU
        )
        self.recognition_indicator.set_opacity(0.3)
        status_box.pack_end(self.recognition_indicator, False, False, 0)

        status_row = PreferenceRow(
            title="Status",
            widget=status_box,
        )
        progress_group.add_row(status_row)

        # Audio level row
        self.recognition_audio_level = Gtk.LevelBar()
        self.recognition_audio_level.set_min_value(0)
        self.recognition_audio_level.set_max_value(100)
        self.recognition_audio_level.set_value(0)
        self.recognition_audio_level.set_size_request(150, -1)

        level_row = PreferenceRow(
            title="Audio Level",
            widget=self.recognition_audio_level,
        )
        progress_group.add_row(level_row)

        self.content_box.pack_start(progress_group, False, False, 0)

        # Progress info label
        self.progress_info_label = Gtk.Label(label="", use_markup=True, xalign=0)
        self.progress_info_label.set_margin_start(16)
        self.progress_info_label.set_margin_bottom(8)
        self.content_box.pack_start(self.progress_info_label, False, False, 0)

    def _load_and_apply_settings(self):
        """Load current settings and populate the UI."""
        settings = self._get_current_settings()
        self.current_engine = settings["engine"]
        self.language = settings["language"]
        self.current_model_size = settings["model_size"]
        self.current_vad = settings.get("vad_sensitivity", 3)
        self.current_silence = settings.get("silence_timeout", 2.0)

        logger.info(
            f"Starting dialog with settings: engine={self.current_engine}, model={self.current_model_size}"
        )

        # Populate engine combo with only available engines
        available_engines = get_available_engines()
        available_count = 0
        
        for engine in ENGINE_MODELS.keys():
            if available_engines.get(engine, False):
                display_name = format_engine_display_name(engine)
                self.engine_combo.append(display_name, display_name)
                available_count += 1

        if available_count == 0:
            logger.error("No speech recognition engines available!")
            # Still add them so the UI works, but log the error
            for engine in ENGINE_MODELS.keys():
                display_name = format_engine_display_name(engine)
                self.engine_combo.append(display_name, display_name)
        else:
            logger.info(f"Populated {available_count} available engines: {available_engines}")
        
        # Set engine active - check if current engine is available
        if not available_engines.get(self.current_engine, False):
            logger.warning(f"Current engine '{self.current_engine}' is not available, selecting first available")
            # Find first available engine
            for engine in ENGINE_MODELS.keys():
                if available_engines.get(engine, False):
                    self.current_engine = engine
                    break
        
        engine_text = format_engine_display_name(self.current_engine)
        logger.info(f"Setting active engine to: {engine_text}")
        if not self.engine_combo.set_active_id(engine_text):
            logger.warning("Could not set engine by ID, trying by index")
            # Find index of current engine
            model = self.engine_combo.get_model()
            for i, row in enumerate(model):
                if row[0].lower() == self.current_engine.lower():
                    self.engine_combo.set_active(i)
                    break
            else:
                # Fallback to first available
                if self.engine_combo.get_model():
                    self.engine_combo.set_active(0)

        # Populate model options for the selected engine
        self._populate_model_options()

        # Populate language options
        self._populate_language_options()
        if self.language:
            if not self.language_combo.set_active_id(self.language):
                logger.warning(f"Language '{self.language}' not found in options, using auto")
                self.language_combo.set_active_id("auto")
                self.language = "auto"

        # Set spin button values
        self.vad_spin.set_value(self.current_vad)
        self.silence_spin.set_value(self.current_silence)

    def _get_current_settings(self):
        """Get current settings from config manager."""
        self.config_manager.load_config()
        settings = self.config_manager.get_settings()

        sr_settings = settings.get("speech_recognition", {})
        engine = sr_settings.get("engine", "vosk")
        language = sr_settings.get("language", "en-us")
        model_size = self.config_manager.get_model_size_for_engine(engine)
        vad_sensitivity = sr_settings.get("vad_sensitivity", 3)
        silence_timeout = sr_settings.get("silence_timeout", 2.0)

        logger.info(
            f"Loaded current settings: engine={engine}, language={language}, model_size={model_size}, "
            f"vad={vad_sensitivity}, silence={silence_timeout}"
        )

        return {
            "engine": engine,
            "language": language,
            "model_size": model_size,
            "vad_sensitivity": vad_sensitivity,
            "silence_timeout": silence_timeout,
        }

    def _populate_model_options(self):
        """Populate model options based on the current engine selection."""
        self._populating_models = True
        try:
            self.model_combo.remove_all()

            engine_text = self.engine_combo.get_active_text()
            if not engine_text:
                logger.warning("No engine selected during model options population")
                return

            engine = engine_text.lower()
            logger.info(f"Populating model options for engine: {engine}")

            saved_model_for_engine = self.config_manager.get_model_size_for_engine(engine)
            logger.info(f"Saved model for {engine}: {saved_model_for_engine}")

            downloaded_models = []
            smallest_model = None
            if engine == "whisper":
                recommended_model, _ = _get_recommended_whisper_model()
            elif engine == "whisper_cpp":
                recommended_model, _ = get_recommended_whispercpp_model()
            else:
                recommended_model, _ = _get_recommended_vosk_model()

            if engine in ENGINE_MODELS:
                for size in ENGINE_MODELS[engine]:
                    if engine == "whisper" and size in WHISPER_MODEL_INFO:
                        info = WHISPER_MODEL_INFO[size]
                        is_downloaded = _is_whisper_model_downloaded(size)
                    elif engine == "whisper_cpp" and size in WHISPERCPP_MODEL_INFO:
                        info = WHISPERCPP_MODEL_INFO[size]
                        is_downloaded = is_whispercpp_model_downloaded(size)
                    elif engine == "vosk" and size in VOSK_MODEL_INFO:
                        info = VOSK_MODEL_INFO[size]
                        is_downloaded = _is_vosk_model_downloaded(size, self.language)
                    else:
                        is_downloaded = False
                        info = {"size_mb": 0}

                    status = "✓" if is_downloaded else "↓"
                    star = " ★" if size == recommended_model else ""
                    display_text = f"{size.capitalize()} ({_format_size(info.get('size_mb', 0))}) {status}{star}"

                    if is_downloaded:
                        downloaded_models.append(size)
                    if smallest_model is None:
                        smallest_model = size

                    self.model_combo.append(size.capitalize(), display_text)

            # Determine which model to select
            saved_model = saved_model_for_engine.lower()
            valid_models = [m.lower() for m in ENGINE_MODELS.get(engine, [])]

            if saved_model in valid_models:
                model_to_set = saved_model.capitalize()
            elif downloaded_models:
                model_to_set = downloaded_models[0].capitalize()
            else:
                model_to_set = smallest_model.capitalize() if smallest_model else "Small"

            logger.info(f"Setting active model to: {model_to_set}")

            if not self.model_combo.set_active_id(model_to_set):
                logger.warning(f"Could not set model by ID '{model_to_set}'")
                model = self.model_combo.get_model()
                for i, row in enumerate(model):
                    if row[0].lower() == model_to_set.lower():
                        self.model_combo.set_active(i)
                        break
                else:
                    if len(ENGINE_MODELS.get(engine, [])) > 0:
                        self.model_combo.set_active(0)

            logger.info(f"Final selected model: {self.model_combo.get_active_text()}")
        finally:
            self._populating_models = False

    def _on_engine_changed(self, widget):
        """Handle changes in the selected engine."""
        engine_text = self.engine_combo.get_active_text()
        if not engine_text:
            return

        engine = engine_text.lower()

        current_lang = self.language_combo.get_active_id()
        if current_lang:
            if engine == "vosk" and (
                current_lang == "auto" or not SUPPORTED_LANGUAGES.get(current_lang, {}).get("vosk")
            ):
                self.language = "en-us"
            elif engine in ["whisper", "whisper_cpp"] and not current_lang:
                self.language = "auto"

        self._populate_model_options()
        self._populate_language_options()
        self.language_combo.set_active_id(self.language)
        self._update_engine_specific_ui()
        self._update_model_info()

    def _on_model_changed(self, widget):
        """Handle changes in the selected model."""
        if self._populating_models:
            return

        self._update_model_info()
        self._auto_apply_settings()

    def _on_vad_changed(self, widget):
        """Handle changes in VAD sensitivity."""
        self._auto_apply_settings()

    def _on_silence_changed(self, widget):
        """Handle changes in silence timeout."""
        self._auto_apply_settings()

    def _populate_language_options(self):
        """Populate language dropdown with supported languages."""
        self.language_combo.remove_all()
        engine = self.engine_combo.get_active_text()
        if not engine:
            return

        engine = engine.lower()

        for lang_code, lang_info in SUPPORTED_LANGUAGES.items():
            display_text = lang_info["name"]

            if engine == "vosk":
                has_model = lang_info["vosk"] is not None
                if not has_model or lang_code == "auto":
                    continue
                is_downloaded = _is_vosk_model_downloaded("small", lang_code)
                display_text += " ✓" if is_downloaded else " ↓"
            elif engine in ["whisper", "whisper_cpp"]:
                # Both Whisper and whisper.cpp support auto-detect
                if lang_code == "auto":
                    display_text += " ⚠"
            else:
                continue

            self.language_combo.append(lang_code, display_text)

    def _on_language_changed(self, widget):
        """Handle language selection change."""
        if self._processing_language_change:
            return

        lang_code = self.language_combo.get_active_id()
        if not lang_code:
            return

        engine = self.engine_combo.get_active_text()
        if not engine:
            return

        self._processing_language_change = True
        try:
            engine = engine.lower()
            lang_info = SUPPORTED_LANGUAGES.get(lang_code, {})

            if lang_info.get("warning"):
                self.language_warning.set_markup(
                    f"<span foreground='#e5a50a'>⚠ {lang_info['warning']}</span>"
                )
                self.language_warning.show()
            else:
                self.language_warning.set_markup("")
                self.language_warning.hide()

            self.language = lang_code
            self._populate_model_options()
            self._auto_apply_settings()
        finally:
            self._processing_language_change = False

    def _update_engine_specific_ui(self):
        """Show/hide UI elements specific to the selected engine."""
        self._update_model_info()

    def _update_model_info(self):
        """Update the model info card display."""
        engine_text = self.engine_combo.get_active_text()
        if not engine_text:
            self.model_info_card.hide()
            return

        engine = engine_text.lower()
        model_id = self.model_combo.get_active_id()
        if not model_id:
            self.model_info_card.hide()
            return

        model_name = model_id.lower()

        if engine == "whisper":
            if model_name not in WHISPER_MODEL_INFO:
                self.model_info_card.hide()
                return
            info = WHISPER_MODEL_INFO[model_name]
            is_downloaded = _is_whisper_model_downloaded(model_name)
            recommended, reason = _get_recommended_whisper_model()
            extra_info = f"Parameters: {info['params']}"
        elif engine == "whisper_cpp":
            if model_name not in WHISPERCPP_MODEL_INFO:
                self.model_info_card.hide()
                return
            info = WHISPERCPP_MODEL_INFO[model_name]
            is_downloaded = is_whispercpp_model_downloaded(model_name)
            recommended, reason = get_recommended_whispercpp_model()
            backend, backend_info = detect_compute_backend()
            extra_info = (
                f"Parameters: {info['params']} • Backend: {get_backend_display_name(backend)}"
            )
        elif engine == "vosk":
            if model_name not in VOSK_MODEL_INFO:
                self.model_info_card.hide()
                return
            info = VOSK_MODEL_INFO[model_name]
            is_downloaded = _is_vosk_model_downloaded(model_name, self.language)
            recommended, reason = _get_recommended_vosk_model()
            extra_info = f"Size: {_format_size(info['size_mb'])}"
        else:
            self.model_info_card.hide()
            return

        # Update title
        self.model_info_title.set_markup(f"<b>{model_name.capitalize()}</b>: {info['desc']}")

        # Update subtitle with status
        if is_downloaded:
            status = "<span foreground='#26a269'>✓ Downloaded and ready</span>"
        else:
            status = f"<span foreground='#e5a50a'>↓ Will download ~{_format_size(info['size_mb'])}</span>"
        self.model_info_subtitle.set_markup(f"{extra_info} • {status}")

        # Update recommendation
        if model_name == recommended:
            self.model_recommendation.set_markup(
                f"<span foreground='#26a269'>★ Recommended for your system ({reason})</span>"
            )
        else:
            self.model_recommendation.set_markup(
                f"Tip: <b>{recommended.capitalize()}</b> is recommended for your system ({reason})"
            )

        self.model_info_card.show_all()

    def _auto_apply_settings(self):
        """Automatically apply settings when changed."""
        if self._applying_settings:
            return

        if self._initializing:
            return

        if self._test_active:
            return

        if self._populating_models:
            return

        self._applying_settings = True
        try:
            settings = self.get_selected_settings()
            engine = settings.get("engine", "vosk")
            model_name = settings.get("model_size", "small")

            # Check if model needs to be downloaded
            needs_download = False
            model_info = {"size_mb": 100}  # Default
            if engine == "whisper" and not _is_whisper_model_downloaded(model_name):
                needs_download = True
                model_info = WHISPER_MODEL_INFO.get(model_name, {"size_mb": 500})
            elif engine == "whisper_cpp" and not is_whispercpp_model_downloaded(model_name):
                needs_download = True
                model_info = WHISPERCPP_MODEL_INFO.get(model_name, {"size_mb": 39})
            elif engine == "vosk" and not _is_vosk_model_downloaded(model_name, self.language):
                needs_download = True
                model_info = VOSK_MODEL_INFO.get(model_name, {"size_mb": 50})

            if needs_download:
                logger.info(f"Model {model_name} needs download, showing progress dialog")
                download_dialog = ModelDownloadDialog(
                    self,
                    model_name,
                    model_info["size_mb"],
                    engine=engine,
                    language=self.language,
                )

                def progress_callback(fraction, speed, status):
                    GLib.idle_add(download_dialog.update_progress, fraction, speed, status)

                def download_and_apply():
                    try:
                        self.speech_engine.set_download_progress_callback(progress_callback)

                        def check_cancelled():
                            if download_dialog.cancelled:
                                self.speech_engine.cancel_download()
                            return not download_dialog.cancelled

                        cancel_check_id = GLib.timeout_add(100, check_cancelled)

                        try:
                            self._apply_settings_internal(settings)
                            GLib.idle_add(download_dialog.set_complete, True, "")
                            GLib.idle_add(self._populate_model_options)
                        finally:
                            GLib.source_remove(cancel_check_id)
                            self.speech_engine.set_download_progress_callback(None)

                    except Exception as e:
                        error_msg = str(e)
                        if "cancelled" in error_msg.lower():
                            GLib.idle_add(download_dialog.set_complete, False, "Download cancelled")
                        elif engine == "whisper" and "no module named" in error_msg.lower():
                            GLib.idle_add(
                                download_dialog.set_complete, False, "Whisper not installed"
                            )
                            GLib.idle_add(self._show_whisper_install_dialog)
                        else:
                            GLib.idle_add(download_dialog.set_complete, False, error_msg[:100])

                threading.Thread(target=download_and_apply, daemon=True).start()
                download_dialog.run()
                download_dialog.destroy()
                return

            logger.info(f"Auto-applying settings: {settings}")

            self.config_manager.update_speech_recognition_settings(settings)
            self.config_manager.save_settings()
            self.speech_engine.reconfigure(**settings)
            logger.info("Settings auto-applied successfully")
        except Exception as e:
            logger.error(f"Failed to auto-apply settings: {e}")
        finally:
            self._applying_settings = False

    def get_selected_settings(self) -> dict:
        """Return the currently selected settings from the UI."""
        engine_text = self.engine_combo.get_active_text()
        model_id = self.model_combo.get_active_id()
        language_id = self.language_combo.get_active_id()

        engine = engine_text.lower() if engine_text else "vosk"
        model_size = model_id.lower() if model_id else "small"
        language = language_id if language_id else "auto"

        vad = int(self.vad_spin.get_value())
        silence = self.silence_spin.get_value()

        return {
            "engine": engine,
            "model_size": model_size,
            "language": language,
            "vad_sensitivity": vad,
            "silence_timeout": silence,
        }

    def _on_test_clicked(self, widget):
        """Handle click on the test button."""
        if self._test_active:
            logger.warning("Test already in progress.")
            return

        current_config = self.config_manager.get_settings().get("speech_recognition", {})
        selected_settings = self.get_selected_settings()

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

        if settings_differ:
            self.test_buffer.set_text("Applying settings...")
            if not self.apply_settings():
                self.test_buffer.set_text("Failed to apply settings. Please try again.")
                return
            self.test_buffer.set_text("Settings applied. Starting test...")

        self._test_active = True
        self.test_button.set_sensitive(False)
        self.test_button.set_label("Testing... Speak Now!")
        self.test_buffer.set_text("")
        self._test_result = ""

        self.connect_to_recognition_manager()
        self.update_recognition_progress("Listening", info="Starting recognition test...")

        self._saved_text_callbacks = self.speech_engine.get_text_callbacks()
        self.speech_engine.set_text_callbacks([self._test_text_callback])

        self.speech_engine.start_recognition()
        threading.Thread(target=self._stop_test_after_delay, args=(3,)).start()

    def _test_text_callback(self, text: str):
        """Callback specifically for the test recognition."""
        GLib.idle_add(self._append_test_result, text)

    def _append_test_result(self, text: str):
        current_text = self.test_buffer.get_text(
            self.test_buffer.get_start_iter(), self.test_buffer.get_end_iter(), False
        )
        separator = " " if current_text.strip() else ""
        self.test_buffer.insert(self.test_buffer.get_end_iter(), separator + text)
        mark = self.test_buffer.get_insert()
        self.test_textview.scroll_to_mark(mark, 0.0, True, 0.0, 1.0)
        return False

    def _stop_test_after_delay(self, delay: int):
        """Stops the recognition test after a specified delay."""
        time.sleep(delay)
        GLib.idle_add(self._finalize_test)

    def _finalize_test(self):
        """Finalize the test state and UI updates."""
        if not self._test_active:
            return False

        self.speech_engine.stop_recognition()

        if hasattr(self, "_saved_text_callbacks"):
            self.speech_engine.set_text_callbacks(self._saved_text_callbacks)
            del self._saved_text_callbacks

        self._test_active = False
        self.test_button.set_sensitive(True)
        self.test_button.set_label("Start Test (3 seconds)")

        self.update_recognition_progress("Idle")
        GLib.timeout_add(200, self._check_test_result)

        return False

    def _check_test_result(self):
        """Check if any text was captured after all callbacks have run."""
        final_text = self.test_buffer.get_text(
            self.test_buffer.get_start_iter(), self.test_buffer.get_end_iter(), False
        )
        if not final_text.strip():
            self.test_buffer.set_text("(No speech detected during test)")
        return False

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

        self.engine_combo.set_active_id("Vosk")
        self._populate_model_options()
        self._update_engine_specific_ui()

    def apply_settings(self):
        """Apply the selected settings."""
        settings = self.get_selected_settings()
        logger.info(f"Applying settings: {settings}")

        engine = settings.get("engine", "vosk")
        model_name = settings.get("model_size", "small")

        needs_download = False
        model_info = {"size_mb": 100}  # Default
        if engine == "whisper" and not _is_whisper_model_downloaded(model_name):
            needs_download = True
            model_info = WHISPER_MODEL_INFO.get(model_name, {"size_mb": 500})
        elif engine == "vosk" and not _is_vosk_model_downloaded(model_name, self.language):
            needs_download = True
            model_info = VOSK_MODEL_INFO.get(model_name, {"size_mb": 50})

        if needs_download:
            download_dialog = ModelDownloadDialog(
                self,
                model_name,
                model_info["size_mb"],
                engine=engine,
                language=self.language,
            )

            def progress_callback(fraction, speed, status):
                GLib.idle_add(download_dialog.update_progress, fraction, speed, status)

            def download_and_apply():
                try:
                    self.speech_engine.set_download_progress_callback(progress_callback)

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

            self._populate_model_options()
            return True

        return self._apply_settings_internal(settings)

    def _apply_settings_internal(self, settings: dict) -> bool:
        """Internal method to apply settings."""
        try:
            self.config_manager.update_speech_recognition_settings(settings)
            self.config_manager.save_settings()

            was_running = self.speech_engine.state != RecognitionState.IDLE
            if was_running:
                self.speech_engine.stop_recognition()
                time.sleep(0.5)

            self.speech_engine.reconfigure(**settings)

            logger.info("Settings applied successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to apply settings: {e}", exc_info=True)

            if "whisper" in str(e).lower() and "no module named" in str(e).lower():
                self._show_whisper_install_dialog()
            else:
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
        from ..speech_recognition.recognition_manager import get_audio_input_devices

        self.audio_device_combo.remove_all()

        self.audio_device_combo.append("-1", "System Default")

        devices = get_audio_input_devices()

        for device_index, device_name, is_default in devices:
            label = device_name
            if is_default:
                label += " (default)"
            self.audio_device_combo.append(str(device_index), label)

        saved_device = self.config_manager.get("audio", "device_index", None)

        if saved_device is None:
            self.audio_device_combo.set_active_id("-1")
        else:
            if not self.audio_device_combo.set_active_id(str(saved_device)):
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

        if device_index == -1:
            self.config_manager.set("audio", "device_index", None)
            self.config_manager.set("audio", "device_name", None)
        else:
            self.config_manager.set("audio", "device_index", device_index)
            self.config_manager.set("audio", "device_name", device_name)

        self.config_manager.save_settings()

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

        device_id = self.audio_device_combo.get_active_id()
        device_index = None if device_id == "-1" else int(device_id)

        def run_test():
            from ..speech_recognition.recognition_manager import test_audio_input

            result = test_audio_input(device_index=device_index, duration=2.0)
            GLib.idle_add(self._handle_audio_test_result, result)

        threading.Thread(target=run_test, daemon=True).start()

    def _handle_audio_test_result(self, result: dict):
        """Handle the result of an audio test."""
        self.test_audio_btn.set_sensitive(True)
        self.test_audio_btn.set_label("Test")

        if result.get("success"):
            max_level = result.get("max_amplitude", 0)
            has_signal = result.get("has_signal", False)

            level_percent = min(100, (max_level / 327.68))
            self.audio_level_bar.set_value(level_percent)

            if has_signal:
                self.audio_test_status.set_markup(
                    f"<span foreground='#26a269'>✓ Audio detected!</span> "
                    f"Peak level: {level_percent:.0f}%"
                )
            else:
                self.audio_test_status.set_markup(
                    f"<span foreground='#e5a50a'>⚠ Very low audio level</span> "
                    f"(peak: {level_percent:.1f}%)\n"
                    "<small>Check if microphone is muted or try a different device</small>"
                )
        else:
            error_msg = result.get("error", "Unknown error")
            self.audio_test_status.set_markup(
                f"<span foreground='#c01c28'>✗ Test failed:</span> {error_msg}"
            )

        return False

    def do_response(self, response_id):
        """Handle dialog button responses."""
        if response_id == Gtk.ResponseType.CLOSE:
            logger.info("Close button clicked")
            self.destroy()

        return True

    def update_recognition_progress(self, state: str, audio_level: float = 0.0, info: str = ""):
        """Update the recognition progress feedback UI."""
        self.recognition_status_label.set_text(state)

        # Remove existing state classes
        for css_class in [
            "recognition-idle",
            "recognition-listening",
            "recognition-processing",
            "recognition-error",
        ]:
            self.recognition_status_label.get_style_context().remove_class(css_class)

        if state == "Listening":
            self.recognition_indicator.set_opacity(1.0)
            self.recognition_status_label.get_style_context().add_class("recognition-listening")
            self.progress_info_label.set_markup("<span foreground='#26a269'>● Listening...</span>")
        elif state == "Processing":
            self.recognition_indicator.set_opacity(1.0)
            self.recognition_status_label.get_style_context().add_class("recognition-processing")
            self.progress_info_label.set_markup(
                "<span foreground='#e5a50a'>● Processing speech...</span>"
            )
        elif state == "Idle":
            self.recognition_indicator.set_opacity(0.3)
            self.recognition_status_label.get_style_context().add_class("recognition-idle")
            self.progress_info_label.set_text("")
        elif state == "Error":
            self.recognition_indicator.set_opacity(0.3)
            self.recognition_status_label.get_style_context().add_class("recognition-error")
            self.progress_info_label.set_markup(
                f"<span foreground='#c01c28'>✗ Error: {info}</span>"
            )
        else:
            self.recognition_indicator.set_opacity(0.3)
            if info:
                self.progress_info_label.set_text(info)

        if audio_level > 0:
            normalized_level = min(100, max(0, audio_level))
            self.recognition_audio_level.set_value(normalized_level)
        elif state == "Idle":
            self.recognition_audio_level.set_value(0)

    def connect_to_recognition_manager(self):
        """Connect to speech recognition manager for progress updates."""
        if hasattr(self, "speech_engine") and self.speech_engine:
            if not hasattr(self, "_callbacks_registered"):
                self.speech_engine.state_callbacks.append(self._on_recognition_state_changed)
                self.speech_engine.register_audio_level_callback(self._on_audio_level_changed)
                self._callbacks_registered = True
                self.connect("destroy", self._on_dialog_destroy)

    def _on_dialog_destroy(self, widget):
        """Clean up callbacks when dialog is destroyed."""
        if hasattr(self, "speech_engine") and self.speech_engine:
            if self._on_recognition_state_changed in self.speech_engine.state_callbacks:
                self.speech_engine.state_callbacks.remove(self._on_recognition_state_changed)
            self.speech_engine.unregister_audio_level_callback(self._on_audio_level_changed)

    def _on_recognition_state_changed(self, state):
        """Handle recognition state changes."""
        state_map = {
            RecognitionState.IDLE: "Idle",
            RecognitionState.LISTENING: "Listening",
            RecognitionState.PROCESSING: "Processing",
            RecognitionState.ERROR: "Error",
        }

        state_str = state_map.get(state, "Unknown")
        GLib.idle_add(self.update_recognition_progress, state_str)

    def _on_audio_level_changed(self, level: float):
        """Handle audio level changes."""
        GLib.idle_add(self.update_recognition_progress, "Listening", level)
