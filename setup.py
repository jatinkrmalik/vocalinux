#!/usr/bin/env python3
import os

from setuptools import find_packages, setup

# This package requires several system dependencies that must be installed manually:
# For PyAudio: portaudio19-dev (on Ubuntu/Debian)
# For PyGObject: libgirepository1.0-dev, libcairo2-dev, pkg-config, python3-dev

setup(
    name="vocalinux",
    version="0.1.0",
    description="A seamless voice dictation system for Linux",
    author="@jatinkrmaik",
    author_email="jatinkrmalik@gmail.com",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "vosk",  # For VOSK API speech recognition
        "pydub",  # For audio processing
        "python-xlib",  # For keyboard shortcut handling in X11
        "pynput",  # For keyboard/mouse events
        "PyGObject",  # For GTK UI
        "requests",  # For downloading models
        "tqdm",  # For progress bars during downloads
        "numpy",  # For numerical operations
        "pyaudio",  # For audio input/output
    ],
    extras_require={
        "whisper": ["whisper", "torch"],  # Optional Whisper AI support
        "dev": [
            "pytest",
            "pytest-cov",  # Add this for coverage testing
            "black",
            "isort",
            "flake8",
            "pre-commit",  # For pre-commit hooks
        ],
    },
    entry_points={
        "console_scripts": [
            "vocalinux=vocalinux.main:main",
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
        "Topic :: Desktop Environment :: Gnome",
    ],
    python_requires=">=3.8",  # Updated minimum Python version
)
