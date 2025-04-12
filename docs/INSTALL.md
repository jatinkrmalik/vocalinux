# Installation Guide

This guide provides instructions for installing and setting up Vocalinux.

## System Requirements

- Operating System: Ubuntu 22.04 or newer (may work on other Linux distributions)
- Python: 3.8 or newer
- Desktop Environment: X11 or Wayland
- Dependencies:
  - For audio: PortAudio, PulseAudio
  - For keyboard shortcuts: X11 libraries, libinput (optional)
  - For text injection: xdotool (X11) or wtype/ydotool (Wayland)

## Installation Methods

### Automated Installation (Recommended)

The easiest way to install Vocalinux is using the provided installation script:

1. Clone the repository:
   ```bash
   git clone https://github.com/vocalinux/vocalinux.git
   cd vocalinux
   ```

2. Run the installer script:
   ```bash
   ./install.sh
   ```

3. Follow the on-screen instructions.

The installer will:
- Install required system dependencies
- Set up a Python virtual environment
- Install Python package dependencies
- Configure the application
- Create desktop entry and icon
- Download speech recognition models

### Manual Installation

If you prefer to install manually:

1. Install system dependencies:
   ```bash
   sudo apt update
   sudo apt install -y python3-pip python3-venv portaudio19-dev libinput-dev libxtst-dev libx11-dev xdotool python3-gi gir1.2-appindicator3-0.1
   ```

2. For Wayland users, install a text injection tool:
   ```bash
   # Either wtype
   sudo apt install -y wtype
   # Or ydotool
   sudo apt install -y ydotool
   ```

3. Clone the repository:
   ```bash
   git clone https://github.com/vocalinux/vocalinux.git
   cd vocalinux
   ```

4. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

5. Install the package:
   ```bash
   pip install -e .
   ```

6. Create necessary directories:
   ```bash
   mkdir -p ~/.local/share/vocalinux/icons
   mkdir -p ~/.local/share/vocalinux/models
   mkdir -p ~/.config/vocalinux
   ```

7. Install the desktop entry:
   ```bash
   cp vocalinux.desktop ~/.local/share/applications/
   ```

8. Install the icon:
   ```bash
   mkdir -p ~/.local/share/icons/hicolor/scalable/apps/
   # Assuming there's an icon file
   cp resources/icons/vocalinux.svg ~/.local/share/icons/hicolor/scalable/apps/
   ```

## Post-Installation

After installation, you'll need to download the speech recognition model (if the installer didn't do this automatically):

1. For VOSK:
   - Visit https://alphacephei.com/vosk/models
   - Download a model (e.g., `vosk-model-small-en-us-0.15`)
   - Extract the model to `~/.local/share/vocalinux/models/`

2. For Whisper:
   - The model will be downloaded automatically on first use

## Starting the Application

You can start Vocalinux in several ways:

1. From the application menu:
   - Look for "Vocalinux" in your applications

2. From the command line:
   ```bash
   vocalinux
   ```

3. With specific options:
   ```bash
   # Debug mode
   vocalinux --debug
   
   # Use a specific engine
   vocalinux --engine whisper
   
   # Use a specific model size
   vocalinux --model medium
   ```

## Troubleshooting

### Application Doesn't Start

- Check if all dependencies are installed:
  ```bash
  cd vocalinux
  pip install -e .
  ```

### No Audio Input

- Check your microphone is connected and working:
  ```bash
  arecord -l  # List recording devices
  ```

- Verify permissions:
  ```bash
  groups $USER  # Should include 'audio'
  ```

### Text Not Injecting

- For X11, ensure xdotool is installed:
  ```bash
  sudo apt install xdotool
  ```

- For Wayland, ensure wtype or ydotool is installed:
  ```bash
  sudo apt install wtype
  # or
  sudo apt install ydotool
  ```

- Try running with explicit Wayland mode:
  ```bash
  vocalinux --wayland
  ```

### Speech Recognition Not Working

- Verify model installation:
  ```bash
  ls -la ~/.local/share/vocalinux/models/
  ```

- Try a different model size:
  ```bash
  vocalinux --model small
  ```

- Try a different engine:
  ```bash
  vocalinux --engine whisper
  ```

## Uninstallation

To uninstall Vocalinux:

1. Remove the desktop entry:
   ```bash
   rm ~/.local/share/applications/vocalinux.desktop
   ```

2. Remove the icon:
   ```bash
   rm ~/.local/share/icons/hicolor/scalable/apps/vocalinux.svg
   ```

3. Remove the data directories:
   ```bash
   rm -rf ~/.local/share/vocalinux
   rm -rf ~/.config/vocalinux
   ```

4. If you installed in a virtual environment, delete it:
   ```bash
   rm -rf /path/to/vocalinux/venv
   ```