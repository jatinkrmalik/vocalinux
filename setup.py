#!/usr/bin/env python3
from setuptools import setup, find_packages

setup(
    name="vocalinux",
    version="0.1.0",
    description="A seamless voice dictation system for Linux",
    author="Vocalinux Team",
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
        "numpy" # For numerical operations
    ],
    extras_require={
        "whisper": ["whisper", "torch"],  # Optional Whisper AI support
        "dev": [
            "pytest",
            "pytest-cov",  # Add this for coverage testing
            "black",
            "isort",
            "flake8",
        ],
    },
    entry_points={
        "console_scripts": [
            "vocalinux=main:main",
        ],
    },
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
