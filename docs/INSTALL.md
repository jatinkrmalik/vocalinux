# Installation Guide

This guide provides detailed instructions for installing Vocalinux on Linux systems.

## System Requirements

- **Operating System**: Ubuntu 22.04 or newer (may work on other Linux distributions)
- **Python**: Version 3.8 or newer
- **Display Server**: X11 or Wayland desktop environment
- **Hardware**: Microphone for speech input

## Standard Installation

The recommended way to install Vocalinux is using the provided installation script:

```bash
# Clone the repository
git clone https://github.com/jatinkrmalik/vocalinux.git
cd vocalinux

# Run the installer script
./install.sh
```

### What the Installer Does

The installation script:
1. Installs required system dependencies
2. Creates a Python virtual environment
3. Configures application directories
4. Installs custom icons and desktop entries
5. Sets up everything you need to run Vocalinux

### Installation Options

The installer script supports several options:

```bash
# See all available options
./install.sh --help

# Specify a custom virtual environment directory
./install.sh --venv-dir=custom_venv_name
```

## Running Vocalinux

After installation, you need to activate the virtual environment before using Vocalinux:

```bash
# Activate the virtual environment
source activate-vocalinux.sh

# Run Vocalinux
vocalinux
```

You can also launch Vocalinux from your application menu.

## Command Line Options

Vocalinux supports several command-line options:

```bash
# With debugging enabled
vocalinux --debug

# With a specific speech recognition engine
vocalinux --engine whisper

# With a specific model size
vocalinux --model medium

# Force Wayland compatibility mode
vocalinux --wayland
```

## Directory Structure

Vocalinux follows the [XDG Base Directory Specification](https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html) and stores files in these locations:

- `~/.config/vocalinux/` - Configuration files
- `~/.local/share/vocalinux/` - Application data (models, etc.)
- `~/.local/share/applications/` - Desktop entry
- `~/.local/share/icons/hicolor/scalable/apps/` - System-wide icons

## Manual Installation

If you prefer to install manually:

### 1. Install System Dependencies

```bash
# Required system dependencies
sudo apt update
sudo apt install -y python3-pip python3-gi python3-gi-cairo gir1.2-gtk-3.0 \
    gir1.2-appindicator3-0.1 libgirepository1.0-dev python3-dev portaudio19-dev python3-venv

# For X11 environments
sudo apt install -y xdotool

# For Wayland environments
sudo apt install -y wtype
```

### 2. Set Up Python Environment

```bash
# Create a virtual environment
python3 -m venv venv --system-site-packages
source venv/bin/activate

# Update pip and setuptools
pip install --upgrade pip setuptools wheel
```

### 3. Install Python Package

```bash
# Basic installation
pip install .

# With Whisper support (requires more resources)
pip install ".[whisper]"
```

### 4. Install Icons and Desktop Entry

```bash
# Define XDG directories
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/vocalinux"
DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/vocalinux"
DESKTOP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
ICON_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor/scalable/apps"

# Create necessary directories
mkdir -p "$CONFIG_DIR"
mkdir -p "$DATA_DIR/models"
mkdir -p "$DESKTOP_DIR"
mkdir -p "$ICON_DIR"

# Copy desktop entry and update to use the venv
cp vocalinux.desktop "$DESKTOP_DIR/"
VENV_SCRIPT_PATH="$(realpath venv/bin/vocalinux)"
sed -i "s|^Exec=vocalinux|Exec=$VENV_SCRIPT_PATH|" "$DESKTOP_DIR/vocalinux.desktop"

# Copy icons
cp resources/icons/scalable/vocalinux.svg "$ICON_DIR/"
cp resources/icons/scalable/vocalinux-microphone.svg "$ICON_DIR/"
cp resources/icons/scalable/vocalinux-microphone-off.svg "$ICON_DIR/"
cp resources/icons/scalable/vocalinux-microphone-process.svg "$ICON_DIR/"

# Update icon cache
gtk-update-icon-cache -f -t "${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor" 2>/dev/null || true
```

## Troubleshooting

### Virtual Environment Issues

If you encounter problems with the virtual environment:
- Ensure you've activated it with `source activate-vocalinux.sh`
- If you get "command not found" errors, verify the virtual environment has been properly created

### Audio Input Problems

- Check that your microphone is connected and working
- Verify your system audio settings
- Run with `--debug` flag to see detailed logs

### Text Injection Issues

- For X11: Ensure xdotool is installed
- For Wayland: Ensure wtype is installed
- Some applications may have security measures that prevent text injection

### Icons Not Displaying

- Run `gtk-update-icon-cache -f -t ~/.local/share/icons/hicolor` to refresh the icon cache
- Ensure the SVG icons are properly installed in the correct directory

### Recognition Accuracy

- Try a larger model size (`--model medium` or `--model large`)
- Ensure your microphone is positioned correctly
- Speak clearly and at a moderate pace

## Uninstallation

To uninstall Vocalinux:

1. Remove the application directories:
   ```bash
   rm -rf ~/.config/vocalinux
   rm -rf ~/.local/share/vocalinux
   rm ~/.local/share/applications/vocalinux.desktop
   rm ~/.local/share/icons/hicolor/scalable/apps/vocalinux*.svg
   ```

2. Update the icon cache:
   ```bash
   gtk-update-icon-cache -f -t ~/.local/share/icons/hicolor
   ```

3. Remove the cloned repository and virtual environment (if you wish).
