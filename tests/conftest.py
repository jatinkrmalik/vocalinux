"""
Configuration file for pytest.
This file makes sure that the 'src' module can be imported in tests.
"""

import os
import sys

# Add the parent directory to sys.path so that 'src' can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# This will help pytest discover all test files correctly
pytest_plugins = []
