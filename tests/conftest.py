"""
Configuration file for pytest.
This file makes sure that the 'src' module can be imported in tests.
"""

import os
import sys

import pytest

# Add the parent directory to sys.path so that 'src' can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# This will help pytest discover all test files correctly
pytest_plugins = []


def pytest_addoption(parser):
    """Add custom command line options for pytest."""
    parser.addoption(
        "--run-tray-tests",
        action="store_true",
        default=False,
        help="Run tray indicator tests (may hang in headless environments)",
    )


def pytest_collection_modifyitems(config, items):
    """Modify collected test items to skip tray_indicator tests when running the full suite."""
    # Check if we should run tray tests (environment variable or command line option)
    run_tray_tests = os.getenv(
        "RUN_TRAY_TESTS", "false"
    ).lower() == "true" or config.getoption("--run-tray-tests", default=False)

    # Get the list of file names being tested
    test_files = set()
    for item in items:
        test_files.add(item.fspath.basename)

    # If we're running more than just the tray_indicator tests and not explicitly enabling them, skip them
    if (
        len(test_files) > 1
        and "test_tray_indicator.py" in test_files
        and not run_tray_tests
    ):
        skip_tray = pytest.mark.skip(
            reason="Skipping tray_indicator tests in full suite to prevent hanging (use --run-tray-tests or RUN_TRAY_TESTS=true to enable)"
        )
        for item in items:
            if item.fspath.basename == "test_tray_indicator.py":
                item.add_marker(skip_tray)
