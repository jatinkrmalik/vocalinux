# Installation Guide

This guide provides instructions for installing and setting up Vocalinux.

## Requirements

- Ubuntu 22.04 or newer
- Python 3.6 or newer
- Dependencies for speech recognition and text injection

## Basic Installation

### 1. Install System Dependencies

```bash
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
# Basic installation
pip3 install --user .

# With Whisper support (requires more resources)
pip3 install --user ".[whisper]"

# For development
pip3 install --user ".[dev]"
```

### 4. Run the Application

```bash
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