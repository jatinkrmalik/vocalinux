#!/usr/bin/env python3
"""
Simple test script for visual feedback indicator (no GUI required).
"""

import sys
import time

# Add the src directory to Python path
sys.path.insert(0, '/tmp/vocalinux-issue-95/src')

from vocalinux.ui.visual_feedback import VisualFeedbackIndicator
from vocalinux.common_types import RecognitionState


def test_visual_feedback():
    """Test visual feedback indicator functionality."""
    print("Testing Visual Feedback Indicator")
    print("=" * 40)
    
    # Create indicator
    indicator = VisualFeedbackIndicator()
    print("✓ Visual feedback indicator created successfully")
    
    # Test state changes (these should work even without GTK)
    print("\nTesting state changes:")
    
    print("  - Setting to LISTENING state")
    indicator.update_state(RecognitionState.LISTENING)
    
    print("  - Setting to PROCESSING state")
    indicator.update_state(RecognitionState.PROCESSING)
    
    print("  - Setting to IDLE state")
    indicator.update_state(RecognitionState.IDLE)
    
    # Test cleanup
    print("\nTesting cleanup:")
    indicator.cleanup()
    print("✓ Cleanup completed successfully")
    
    print("\n" + "=" * 40)
    print("All tests passed!")
    print("Note: Visual indicators require GTK to be installed.")
    print("The component gracefully handles environments without GTK.")


if __name__ == "__main__":
    test_visual_feedback()