#!/usr/bin/env python3
"""
Test script for visual feedback indicator.

This script tests the visual feedback functionality independently.
"""

import sys
import time
import signal
from gi.repository import GLib, Gtk

# Add the src directory to Python path
sys.path.insert(0, '/tmp/vocalinux-issue-95/src')

from vocalinux.ui.visual_feedback import VisualFeedbackIndicator
from vocalinux.common_types import RecognitionState


class VisualFeedbackTest:
    """Test class for visual feedback indicator."""
    
    def __init__(self):
        """Initialize the test."""
        self.indicator = VisualFeedbackIndicator()
        self.test_running = True
        
        # Set up signal handler for graceful exit
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        print(f"\nReceived signal {signum}, shutting down...")
        self.test_running = False
        self.indicator.hide()
        Gtk.main_quit()
    
    def run_test(self):
        """Run the visual feedback test."""
        print("Starting Visual Feedback Test")
        print("=" * 40)
        print("This will show a visual indicator at cursor position.")
        print("Press Ctrl+C to exit.")
        print("=" * 40)
        
        # Test sequence
        try:
            print("\n1. Testing LISTENING state (blue indicator)")
            self.indicator.update_state(RecognitionState.LISTENING)
            time.sleep(3)
            
            if not self.test_running:
                return
            
            print("\n2. Testing PROCESSING state (orange indicator)")
            self.indicator.update_state(RecognitionState.PROCESSING)
            time.sleep(3)
            
            if not self.test_running:
                return
            
            print("\n3. Testing IDLE state (indicator hidden)")
            self.indicator.update_state(RecognitionState.IDLE)
            time.sleep(2)
            
            if not self.test_running:
                return
            
            print("\n4. Testing show/hide directly")
            self.indicator.show()
            print("   - Indicator should be visible")
            time.sleep(2)
            
            if not self.test_running:
                return
            
            self.indicator.hide()
            print("   - Indicator should be hidden")
            time.sleep(1)
            
            if not self.test_running:
                return
            
            print("\n5. Final test: Continuous animation")
            print("   - Will show indicator for 5 seconds")
            self.indicator.update_state(RecognitionState.LISTENING)
            
            # Use GLib timeout for async operation
            GLib.timeout_add(5000, self._final_test_complete)
            
        except KeyboardInterrupt:
            print("\nTest interrupted by user")
        except Exception as e:
            print(f"\nTest failed with error: {e}")
        finally:
            self.indicator.hide()
    
    def _final_test_complete(self):
        """Called when final test is complete."""
        print("\nFinal test complete!")
        print("All tests passed successfully!")
        self.indicator.hide()
        self.test_running = False
        Gtk.main_quit()
        return False  # Don't repeat timeout


def main():
    """Main function."""
    # Check if we're running in a graphical environment
    display = None
    try:
        from gi.repository import Gdk
        display = Gdk.Display.get_default()
    except ImportError:
        print("Error: GTK not available")
        sys.exit(1)
    
    if display is None:
        print("Error: No display available. Make sure you're running in a graphical environment.")
        sys.exit(1)
    
    # Run the test
    test = VisualFeedbackTest()
    
    # Start GTK main loop in a way that allows our test to run
    try:
        # Start the test after GTK main loop starts
        GLib.idle_add(test.run_test)
        Gtk.main()
    except KeyboardInterrupt:
        print("\nTest interrupted")
    finally:
        test.indicator.cleanup()
    
    print("\nTest completed.")


if __name__ == "__main__":
    main()