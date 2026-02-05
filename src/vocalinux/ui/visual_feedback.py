"""
Visual feedback module for Vocalinux.

This module provides a visual feedback indicator at the cursor position
during voice typing to give users clear feedback when the system is listening.
"""

import logging
import math
from typing import Optional

# Try to import GTK, but handle gracefully if not available
GTK_AVAILABLE = False
try:
    import gi

    gi.require_version("Gtk", "3.0")
    gi.require_version("Gdk", "3.0")
    from gi.repository import Gdk, GLib, Gtk

    GTK_AVAILABLE = True
except (ImportError, ValueError) as e:
    logging.warning(f"GTK not available for visual feedback: {e}")

from ..common_types import RecognitionState

logger = logging.getLogger(__name__)


class CursorPosition:
    """Represents the cursor position on screen."""

    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    def __str__(self):
        return f"CursorPosition(x={self.x}, y={self.y})"


class VisualFeedbackIndicator:
    """
    Visual feedback indicator that shows at cursor position during voice typing.

    This creates a semi-transparent overlay window that follows the cursor
    and provides visual feedback when voice recognition is active.
    """

    def __init__(self, config_manager=None):
        """Initialize the visual feedback indicator.

        Args:
            config_manager: Optional ConfigManager instance to check settings.
        """
        self.enabled = True

        # Check configuration if provided
        if config_manager is not None:
            self.enabled = config_manager.get("ui", "enable_visual_feedback", True)

        if not self.enabled:
            logger.info("Visual feedback disabled via configuration")
            return

        if not GTK_AVAILABLE:
            logger.warning("GTK not available - visual feedback disabled")
            return

        self.overlay_window: Optional[Gtk.Window] = None
        self.current_cursor_pos: Optional[CursorPosition] = None
        self.is_visible = False
        self.animation_phase = 0
        self.animation_timeout_id = None
        self.position_update_timeout_id = None
        self.last_cursor_position: Optional[CursorPosition] = None

        # Visual configuration
        self.indicator_size = 40
        self.base_color = (0.2, 0.6, 1.0, 0.8)  # Nice blue with transparency
        self.pulse_min_scale = 0.8
        self.pulse_max_scale = 1.2
        self.pulse_speed = 0.1

        logger.info("Visual feedback indicator initialized")

    def _create_overlay_window(self):
        """Create the overlay window for the visual indicator."""
        if not GTK_AVAILABLE:
            logger.warning("GTK not available - cannot create overlay window")
            return

        if self.overlay_window is not None:
            return

        try:
            # Check if GTK can be initialized
            if not Gtk.init_check()[0]:
                logger.warning("GTK cannot be initialized - cannot create overlay window")
                return

            # Create a transparent, non-decorated window
            self.overlay_window = Gtk.Window(
                type=Gtk.WindowType.POPUP,
                skip_pager_hint=True,
                skip_taskbar_hint=True,
                decorated=False,
                resizable=False,
            )

            # Set window properties for overlay behavior
            self.overlay_window.set_accept_focus(False)
            self.overlay_window.set_focus_on_map(False)
            self.overlay_window.set_keep_above(True)
            self.overlay_window.set_type_hint(Gdk.WindowTypeHint.NOTIFICATION)

            # Make window click-through
            self.overlay_window.set_app_paintable(True)

            # Set size
            self.overlay_window.set_default_size(self.indicator_size * 2, self.indicator_size * 2)
            self.overlay_window.set_size_request(self.indicator_size * 2, self.indicator_size * 2)

            # Connect drawing signal
            self.overlay_window.connect("draw", self._on_draw)

            # Set visual properties for transparency
            screen = self.overlay_window.get_screen()
            visual = screen.get_rgba_visual()
            if visual:
                self.overlay_window.set_visual(visual)

            # Make window transparent
            self.overlay_window.set_opacity(0.9)

            logger.debug("Overlay window created")

        except Exception as e:
            logger.error(f"Failed to create overlay window: {e}")
            self.overlay_window = None

    def _on_draw(self, widget, cr):
        """Draw the visual indicator."""
        if not widget.get_visible():
            return False

        # Get window dimensions
        allocation = widget.get_allocation()
        width = allocation.width
        height = allocation.height
        center_x = width // 2
        center_y = height // 2

        # Clear the background
        cr.set_source_rgba(0, 0, 0, 0)  # Fully transparent
        cr.set_operator(cr.OPERATOR_SOURCE)
        cr.paint()
        cr.set_operator(cr.OPERATOR_OVER)

        # Calculate animation scale
        scale = self.pulse_min_scale + (
            (self.pulse_max_scale - self.pulse_min_scale) * (math.sin(self.animation_phase) + 1) / 2
        )
        radius = (self.indicator_size // 2) * scale

        # Draw outer glow
        glow_radius = radius * 1.5
        for i in range(5):
            alpha = (self.base_color[3] * (1 - i / 5)) * 0.3
            cr.set_source_rgba(*self.base_color[:3], alpha)
            cr.arc(center_x, center_y, glow_radius + i * 2, 0, 2 * math.pi)
            cr.fill()

        # Draw main circle
        cr.set_source_rgba(*self.base_color)
        cr.arc(center_x, center_y, radius, 0, 2 * math.pi)
        cr.fill()

        # Draw inner highlight
        highlight_radius = radius * 0.6
        cr.set_source_rgba(1, 1, 1, 0.6)
        cr.arc(
            center_x - radius * 0.2, center_y - radius * 0.2, highlight_radius * 0.3, 0, 2 * math.pi
        )
        cr.fill()

        return True

    def _get_cursor_position(self) -> Optional[CursorPosition]:
        """
        Get the current cursor position.

        Returns:
            CursorPosition or None if position cannot be determined
        """
        try:
            display = Gdk.Display.get_default()
            if display is None:
                return None

            seat = display.get_default_seat()
            if seat is None:
                return None

            pointer = seat.get_pointer()
            if pointer is None:
                return None

            screen = pointer.get_position()
            if screen is None:
                return None

            x, y = screen.x, screen.y
            return CursorPosition(x, y)

        except Exception as e:
            logger.debug(f"Could not get cursor position: {e}")
            return None

    def _update_position(self):
        """Update the indicator position to follow the cursor."""
        if not self.is_visible or self.overlay_window is None:
            return

        # Get current cursor position
        current_pos = self._get_cursor_position()
        if current_pos is None:
            return

        # Only update if position actually changed
        if (
            self.last_cursor_position is None
            or abs(current_pos.x - self.last_cursor_position.x) > 5
            or abs(current_pos.y - self.last_cursor_position.y) > 5
        ):

            # Calculate window position (center indicator on cursor)
            window_x = current_pos.x - self.indicator_size
            window_y = current_pos.y - self.indicator_size

            # Move the window
            self.overlay_window.move(window_x, window_y)
            self.last_cursor_position = current_pos

        # Schedule next update
        self.position_update_timeout_id = GLib.timeout_add(50, self._update_position)

    def _animate(self):
        """Animate the visual indicator."""
        if not self.is_visible:
            return False

        # Update animation phase
        self.animation_phase += self.pulse_speed

        # Redraw the window
        if self.overlay_window:
            self.overlay_window.queue_draw()

        # Schedule next animation frame
        return True  # Continue animation

    def show(self):
        """Show the visual feedback indicator."""
        if not self.enabled:
            return

        if not GTK_AVAILABLE:
            logger.debug("GTK not available - cannot show visual feedback")
            return

        if self.is_visible:
            return

        logger.debug("Showing visual feedback indicator")

        # Create overlay window if needed
        self._create_overlay_window()

        if self.overlay_window is None:
            logger.error("Could not create overlay window")
            return

        # Get initial cursor position
        cursor_pos = self._get_cursor_position()
        if cursor_pos is None:
            logger.warning("Could not get cursor position, using screen center")
            # Use screen center as fallback
            screen = Gdk.Screen.get_default()
            if screen:
                cursor_pos = CursorPosition(screen.get_width() // 2, screen.get_height() // 2)
            else:
                cursor_pos = CursorPosition(0, 0)

        # Position window
        window_x = cursor_pos.x - self.indicator_size
        window_y = cursor_pos.y - self.indicator_size
        self.overlay_window.move(window_x, window_y)
        self.overlay_window.show_all()

        # Start animation
        self.is_visible = True
        self.animation_timeout_id = GLib.timeout_add(16, self._animate)  # ~60 FPS

        # Start position tracking
        self.position_update_timeout_id = GLib.timeout_add(50, self._update_position)

        logger.info("Visual feedback indicator is now visible")

    def hide(self):
        """Hide the visual feedback indicator."""
        if not self.enabled:
            return

        if not GTK_AVAILABLE:
            return

        if not self.is_visible:
            return

        logger.debug("Hiding visual feedback indicator")

        # Stop animation
        if self.animation_timeout_id:
            GLib.source_remove(self.animation_timeout_id)
            self.animation_timeout_id = None

        # Stop position updates
        if self.position_update_timeout_id:
            GLib.source_remove(self.position_update_timeout_id)
            self.position_update_timeout_id = None

        # Hide and destroy window
        if self.overlay_window:
            self.overlay_window.hide()
            self.overlay_window = None

        self.is_visible = False
        self.last_cursor_position = None
        logger.info("Visual feedback indicator hidden")

    def update_state(self, state: RecognitionState):
        """
        Update the visual indicator based on recognition state.

        Args:
            state: The current recognition state
        """
        if not self.enabled:
            return

        if not GTK_AVAILABLE:
            return

        if state == RecognitionState.LISTENING:
            # Update color for listening state (blue)
            self.base_color = (0.2, 0.6, 1.0, 0.8)
            self.show()
        elif state == RecognitionState.PROCESSING:
            # Update color for processing state (orange)
            self.base_color = (1.0, 0.6, 0.2, 0.8)
            if self.overlay_window:
                self.overlay_window.queue_draw()
        elif state in [RecognitionState.IDLE, RecognitionState.ERROR]:
            # Hide indicator when not listening
            self.hide()

    def cleanup(self):
        """Clean up resources."""
        if not self.enabled:
            return

        if GTK_AVAILABLE:
            self.hide()
        logger.info("Visual feedback indicator cleaned up")
