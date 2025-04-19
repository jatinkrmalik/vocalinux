# Installation Guide

This guide provides instructions for installing and setting up Vocalinux.

## Requirements

- Ubuntu 22.04 or newer
- Python 3.6 or newer
- Dependencies for speech recognition and text injection

## Basic Installation

### 1. Install System Dependencies

```bash
# Required system dependencies for PyAudio and PyGObject
sudo apt install portaudio19-dev libgirepository1.0-dev libcairo2-dev pkg-config python3-dev

# For X11 environments
sudo apt install xdotool python3-pip python3-gi gir1.2-appindicator3-0.1

# For Wayland environments
sudo apt install wtype python3-pip python3-gi gir1.2-appindicator3-0.1
# OR alternatively for Wayland
sudo apt install ydotool python3-pip python3-gi gir1.2-appindicator3-0.1
```

### 2. Clone the Repository

```bash
git clone https://github.com/jatinkrmalik/vocalinux.git
cd vocalinux
```

### 3. Install Python Dependencies

```bash
# Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Basic installation
pip install --upgrade pip
pip install .

# With Whisper support (requires more resources)
pip install ".[whisper]"

# For development
pip install ".[dev]"
```

### 4. Run the Application

```bash
# If using virtual environment, make sure it's activated
source venv/bin/activate

# Basic usage
vocalinux

# With debug logging
vocalinux --debug

# With Whisper instead of VOSK
vocalinux --engine whisper

# Force Wayland mode
vocalinux --wayland
```

## Advanced Installation

### Custom Model Sizes

By default, a small model will be downloaded and used. You can use larger models for improved accuracy:

```bash
vocalinux --model medium
# or
vocalinux --model large
```

Note that larger models require more RAM and may have longer initialization times, but provide better recognition accuracy.

## Troubleshooting

### Build errors related to PyAudio or PyGObject

If you encounter errors like `portaudio.h: No such file or directory` or issues with GTK/GObject, make sure you've installed all the required system dependencies:

```bash
sudo apt install portaudio19-dev libgirepository1.0-dev libcairo2-dev pkg-config python3-dev
```

### No audio input detected

- Check that your microphone is connected and working
- Verify your system audio settings
- Run with `--debug` flag to see detailed logs

### Text injection not working

- For X11: Ensure xdotool is installed
- For Wayland: Ensure wtype or ydotool is installed
- Some applications may have security measures that prevent text injection

### Recognition is inaccurate

- Try a larger model size (`--model medium` or `--model large`)
- Ensure your microphone is positioned correctly
- Speak clearly and at a moderate pace
