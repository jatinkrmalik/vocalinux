# Installation Guide

This guide provides detailed instructions for installing Vocalinux on Linux systems.

## Quick Start

### One-liner Installation (Recommended)

```bash
curl -fsSL https://raw.githubusercontent.com/jatinkrmalik/vocalinux/main/install.sh | bash -s -- --tag=v0.4.1-alpha
```

> **Note**: Installs v0.4.1-alpha. For other versions, check [GitHub Releases](https://github.com/jatinkrmalik/vocalinux/releases).

That's it! The installer handles everything automatically, including Whisper AI support.

> ⏱️ **Note**: Installation takes ~5-10 minutes due to Whisper AI dependencies.

### From Source

```bash
git clone https://github.com/jatinkrmalik/vocalinux.git && cd vocalinux && ./install.sh
```

## System Requirements

| Requirement | Details |
|-------------|---------|
| **Operating System** | Ubuntu 22.04+ (recommended), Debian 11+, Fedora 38+, Arch Linux |
| **Python** | 3.8 or newer |
| **Display Server** | X11 or Wayland |
| **Hardware** | Microphone for speech input |
| **Disk Space** | ~500MB (including speech models) |
| **RAM** | 4GB minimum, 8GB recommended for Whisper |

## Installation Options

### Standard Installation

```bash
# Clone the repository
git clone https://github.com/jatinkrmalik/vocalinux.git
cd vocalinux

# Run the installer
./install.sh
```

### Installation with Whisper Support

Whisper provides better accuracy but requires more resources:

```bash
./install.sh --with-whisper
```

### Development Installation

For contributing or development work:

```bash
./install.sh --dev
```

This installs additional tools: pytest, black, isort, flake8, pre-commit.

### All Installer Options

```bash
./install.sh --help

Options:
  --dev            Install in development mode with all dev dependencies
  --test           Run tests after installation
  --venv-dir=PATH  Specify custom virtual environment directory (default: venv)
  --skip-models    Skip downloading VOSK models during installation
  --with-whisper   Install Whisper AI support (default in curl install)
  --no-whisper     Skip Whisper installation (faster, VOSK only)
  -y, --yes        Non-interactive mode (accept defaults)
  --help           Show this help message
```

## What the Installer Does

1. **Detects your Linux distribution** and installs appropriate system packages
2. **Creates a Python virtual environment** with system site-packages access
3. **Installs the Vocalinux package** and all dependencies
4. **Downloads speech recognition models** (Whisper tiny model by default, VOSK as fallback)
5. **Installs desktop integration** (icons, .desktop file)
6. **Creates activation script** for easy environment activation

## Running Vocalinux

After installation:

```bash
# If installed via curl (and ~/.local/bin is in PATH):
vocalinux

# Or run directly:
~/.local/share/vocalinux/venv/bin/vocalinux

# If installed from source:
source venv/bin/activate
vocalinux
```

### Command Line Options

```bash
vocalinux --help              # Show all options
vocalinux --debug             # Enable debug logging
vocalinux --engine whisper    # Use Whisper AI engine (default)
vocalinux --engine vosk       # Use VOSK engine
vocalinux --model tiny        # Use tiny model (default, fastest)
vocalinux --model small       # Use small model
vocalinux --model medium      # Use medium model
vocalinux --model large       # Use large model
vocalinux --wayland           # Force Wayland compatibility mode
```

## Directory Structure

Vocalinux follows the [XDG Base Directory Specification](https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html):

| Directory | Purpose |
|-----------|---------|
| `~/.config/vocalinux/` | Configuration files |
| `~/.local/share/vocalinux/` | Application data, speech models |
| `~/.local/share/applications/` | Desktop entry |
| `~/.local/share/icons/hicolor/scalable/apps/` | Application icons |

## Manual Installation

If you prefer manual installation or the automatic installer doesn't work:

### 1. Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install -y \
    python3-pip python3-venv python3-dev \
    python3-gi python3-gi-cairo \
    gir1.2-gtk-3.0 \
    libgirepository1.0-dev portaudio19-dev \
    wget curl unzip

# For appindicator (system tray icon):
# - On older Ubuntu/Debian versions:
sudo apt install -y gir1.2-appindicator3-0.1
# - On Debian 13+ (trixie) or newer Ubuntu versions:
sudo apt install -y gir1.2-ayatanaappindicator3-0.1

# For X11
sudo apt install -y xdotool

# For Wayland
sudo apt install -y wtype
```

**Fedora:**
```bash
sudo dnf install -y \
    python3-pip python3-devel python3-virtualenv \
    python3-gobject gtk3 libappindicator-gtk3 \
    gobject-introspection-devel portaudio-devel \
    wget curl unzip xdotool
```

**Arch Linux:**
```bash
sudo pacman -S --noconfirm \
    python-pip python-gobject gtk3 \
    libappindicator-gtk3 gobject-introspection \
    python-cairo portaudio python-virtualenv \
    wget curl unzip xdotool
```

### 2. Create Virtual Environment

```bash
cd vocalinux
python3 -m venv venv --system-site-packages
source venv/bin/activate
pip install --upgrade pip setuptools wheel
```

### 3. Install Package

```bash
# Standard installation
pip install .

# With Whisper support
pip install ".[whisper]"

# Development mode
pip install -e ".[dev]"
```

### 4. Set Up Desktop Integration

```bash
# Create directories
mkdir -p ~/.config/vocalinux
mkdir -p ~/.local/share/vocalinux/models
mkdir -p ~/.local/share/applications
mkdir -p ~/.local/share/icons/hicolor/scalable/apps

# Install desktop entry
cp vocalinux.desktop ~/.local/share/applications/
VENV_PATH=$(realpath venv/bin/vocalinux)
sed -i "s|^Exec=vocalinux|Exec=$VENV_PATH|" ~/.local/share/applications/vocalinux.desktop

# Install icons
cp resources/icons/scalable/*.svg ~/.local/share/icons/hicolor/scalable/apps/

# Update icon cache
gtk-update-icon-cache -f -t ~/.local/share/icons/hicolor
```

## Troubleshooting

### Virtual Environment Issues

**Symptom:** "command not found: vocalinux"

**Solution:**
```bash
# Make sure you've activated the environment
source activate-vocalinux.sh

# Or activate directly
source venv/bin/activate
```

### Audio Input Problems

**Symptom:** "No audio detected" or microphone not working

**Solutions:**
1. Check system audio settings
2. Run `arecord -l` to list audio devices
3. Try with debug mode: `vocalinux --debug`
4. Check microphone permissions

### GTK/AppIndicator Errors

**Symptom:** "No module named gi" or AppIndicator errors

**Solution:**
```bash
# Reinstall GTK dependencies
sudo apt install python3-gi python3-gi-cairo

# For appindicator (system tray icon) - try one of these:
sudo apt install gir1.2-appindicator3-0.1  # For older Debian/Ubuntu
# OR
sudo apt install gir1.2-ayatanaappindicator3-0.1  # For Debian 13+ or newer Ubuntu

# Recreate venv with system packages
rm -rf venv
python3 -m venv venv --system-site-packages
source venv/bin/activate
pip install -e .
```

### Text Injection Not Working

**Symptom:** Recognized text doesn't appear in applications

**Solutions:**

For X11:
```bash
sudo apt install xdotool
# Test: xdotool type "hello"
```

For Wayland:
```bash
sudo apt install wtype
# Test: wtype "hello"
```

### Model Download Fails

**Symptom:** Can't download speech models

**Solution:**
```bash
# Models will auto-download on first run
# Or manually download:
mkdir -p ~/.local/share/vocalinux/models
cd ~/.local/share/vocalinux/models
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip
```

Model names with more language and size variety can be found in [VOSK Models](https://alphacephei.com/vosk/models) page.

### Icons Not Displaying

**Symptom:** Tray icon missing or generic

**Solution:**
```bash
# Refresh icon cache
gtk-update-icon-cache -f -t ~/.local/share/icons/hicolor

# Restart the application
```

## Uninstallation

### Using the Uninstaller

```bash
./uninstall.sh
```

Options:
- `--keep-config` - Keep configuration files
- `--keep-data` - Keep application data (models, etc.)

### Manual Uninstallation

```bash
# Remove application files
rm -rf venv
rm -f activate-vocalinux.sh

# Remove user data
rm -rf ~/.config/vocalinux
rm -rf ~/.local/share/vocalinux
rm -f ~/.local/share/applications/vocalinux.desktop
rm -f ~/.local/share/icons/hicolor/scalable/apps/vocalinux*.svg

# Update icon cache
gtk-update-icon-cache -f -t ~/.local/share/icons/hicolor
```

## Updating Vocalinux

Already have Vocalinux installed? See the [Update Guide](UPDATE.md) for instructions on upgrading to the latest version.

Quick update command:
```bash
curl -fsSL https://raw.githubusercontent.com/jatinkrmalik/vocalinux/main/install.sh | bash -s -- --tag=v0.4.1-alpha
```

## Getting Help

- 📖 [User Guide](USER_GUIDE.md)
- 📖 [Update Guide](UPDATE.md)
- 🐛 [Report Issues](https://github.com/jatinkrmalik/vocalinux/issues)
- 💬 [Discussions](https://github.com/jatinkrmalik/vocalinux/discussions)
