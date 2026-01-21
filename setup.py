#!/usr/bin/env python3
"""
Vocalinux - A seamless voice dictation system for Linux

This setup.py is maintained for backwards compatibility with older pip versions
and editable installs. The primary configuration is in pyproject.toml.
"""

import os
import sys

from setuptools import find_packages, setup

# Check Python version
MIN_PYTHON_VERSION = (3, 8)
if sys.version_info < MIN_PYTHON_VERSION:
    sys.exit(
        f"Error: Vocalinux requires Python {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]} or higher"
    )


def get_version():
    """Get version from version.py file."""
    version = "0.3.0-alpha"
    version_file = os.path.join(
        os.path.dirname(__file__), "src", "vocalinux", "version.py"
    )
    if os.path.exists(version_file):
        with open(version_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("__version__"):
                    version = line.split("=")[1].strip().strip('"').strip("'")
                    break
    return version


def get_long_description():
    """Get long description from README."""
    readme_path = os.path.join(os.path.dirname(__file__), "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


# Core dependencies
INSTALL_REQUIRES = [
    "vosk>=0.3.45",
    "pydub>=0.25.1",
    "pynput>=1.7.6",
    "requests>=2.28.0",
    "tqdm>=4.64.0",
    "numpy>=1.22.0",
    "pyaudio>=0.2.13",
    "python-xlib",
    "PyGObject",
]

# Optional dependencies
EXTRAS_REQUIRE = {
    "whisper": [
        "openai-whisper>=20231117",
        "torch>=2.0.0",
        "torchaudio>=2.0.0",
    ],
    "dev": [
        "pytest>=7.0.0",
        "pytest-cov>=4.0.0",
        "pytest-mock>=3.10.0",
        "black>=23.0.0",
        "isort>=5.12.0",
        "flake8>=6.0.0",
        "pre-commit>=3.0.0",
        "mypy>=1.0.0",
    ],
    "docs": [
        "sphinx>=6.0.0",
        "sphinx-rtd-theme>=1.2.0",
    ],
}

setup(
    name="vocalinux",
    version=get_version(),
    description="A seamless voice dictation system for Linux",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    author="Jatin K Malik",
    author_email="jatinkrmalik@gmail.com",
    url="https://github.com/jatinkrmalik/vocalinux",
    project_urls={
        "Bug Tracker": "https://github.com/jatinkrmalik/vocalinux/issues",
        "Documentation": "https://github.com/jatinkrmalik/vocalinux/tree/main/docs",
        "Source Code": "https://github.com/jatinkrmalik/vocalinux",
        "Changelog": "https://github.com/jatinkrmalik/vocalinux/releases",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=INSTALL_REQUIRES,
    extras_require=EXTRAS_REQUIRE,
    entry_points={
        "console_scripts": [
            "vocalinux=vocalinux.main:main",
        ],
        "gui_scripts": [
            "vocalinux-gui=vocalinux.main:main",
        ],
    },
    data_files=[
        (
            "share/icons/hicolor/scalable/apps",
            [
                "resources/icons/scalable/vocalinux.svg",
                "resources/icons/scalable/vocalinux-microphone.svg",
                "resources/icons/scalable/vocalinux-microphone-off.svg",
                "resources/icons/scalable/vocalinux-microphone-process.svg",
            ],
        ),
        ("share/applications", ["vocalinux.desktop"]),
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
        "Programming Language :: Python :: 3.12",
        "Topic :: Desktop Environment :: Gnome",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
        "Topic :: Text Processing",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
    zip_safe=False,
)
