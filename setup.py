#!/usr/bin/env python3
"""
Vocalinux - A seamless voice dictation system for Linux
"""

import os
import sys
import platform
from setuptools import find_packages, setup

# Check Python version
MIN_PYTHON_VERSION = (3, 8)
if sys.version_info < MIN_PYTHON_VERSION:
    sys.exit(f"Error: Vocalinux requires Python {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]} or higher")

# This package requires several system dependencies that must be installed manually:
# For PyAudio: portaudio19-dev (on Ubuntu/Debian)
# For PyGObject: libgirepository1.0-dev, libcairo2-dev, pkg-config, python3-dev

# Get long description from README if available
long_description = ""
if os.path.exists("README.md"):
    with open("README.md", "r", encoding="utf-8") as fh:
        long_description = fh.read()

# Get version from version file or default to 0.1.0
version = "0.1.0"
if os.path.exists("src/vocalinux/version.py"):
    with open("src/vocalinux/version.py", "r", encoding="utf-8") as f:
        exec(f.read())
        version = locals().get("__version__", "0.1.0")

# Platform-specific dependencies
platform_dependencies = []
if platform.system() == "Linux":
    platform_dependencies.extend([
        "python-xlib",  # For keyboard shortcut handling in X11
        "PyGObject",    # For GTK UI
    ])

setup(
    name="vocalinux",
    version=version,
    description="A seamless voice dictation system for Linux",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Jatin K Malik",
    author_email="jatinkrmalik@gmail.com",
    url="https://github.com/jatinkrmalik/vocalinux",
    project_urls={
        "Bug Tracker": "https://github.com/jatinkrmalik/vocalinux/issues",
        "Documentation": "https://github.com/jatinkrmalik/vocalinux/tree/main/docs",
        "Source Code": "https://github.com/jatinkrmalik/vocalinux",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "vosk>=0.3.45",  # For VOSK API speech recognition
        "pydub>=0.25.1",  # For audio processing
        "pynput>=1.7.6",  # For keyboard/mouse events
        "requests>=2.28.0",  # For downloading models
        "tqdm>=4.64.0",  # For progress bars during downloads
        "numpy>=1.22.0",  # For numerical operations
        "pyaudio>=0.2.13",  # For audio input/output
    ] + platform_dependencies,
    extras_require={
        "whisper": [
            "whisper>=1.1.10", 
            "torch>=2.0.0",
        ],  # Optional Whisper AI support
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",  # For coverage testing
            "pytest-mock>=3.10.0",  # For mocking in tests
            "black>=23.0.0",  # For code formatting
            "isort>=5.12.0",  # For import sorting
            "flake8>=6.0.0",  # For linting
            "pre-commit>=3.0.0",  # For pre-commit hooks
        ],
        "docs": [
            "sphinx>=6.0.0",
            "sphinx-rtd-theme>=1.2.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "vocalinux=vocalinux.main:main",
        ],
        "gui_scripts": [
            "vocalinux-gui=vocalinux.main:main",
        ],
    },
    # Include custom application icons and sounds in the package
    data_files=[
        # System-wide icons for desktop integration
        (
            "share/icons/hicolor/scalable/apps",
            [
                "resources/icons/scalable/vocalinux.svg",
                "resources/icons/scalable/vocalinux-microphone.svg",
                "resources/icons/scalable/vocalinux-microphone-off.svg",
                "resources/icons/scalable/vocalinux-microphone-process.svg",
            ],
        ),
        # Desktop file for application launcher
        ("share/applications", ["vocalinux.desktop"]),
        # Install resources inside the package share directory for runtime discovery
        (
            "share/vocalinux/resources/icons/scalable",
            [
                "resources/icons/scalable/vocalinux.svg",
                "resources/icons/scalable/vocalinux-microphone.svg",
                "resources/icons/scalable/vocalinux-microphone-off.svg",
                "resources/icons/scalable/vocalinux-microphone-process.svg",
            ],
        ),
        (
            "share/vocalinux/resources/sounds",
            [
                "resources/sounds/start_recording.wav",
                "resources/sounds/stop_recording.wav",
                "resources/sounds/error.wav",
            ],
        ),
    ],
    include_package_data=True,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: X11 Applications :: GTK",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Desktop Environment :: Gnome",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
        "Topic :: Text Processing",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",  # Minimum Python version
    zip_safe=False,  # Required for PyGObject applications
)
