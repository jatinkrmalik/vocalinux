# Updating Vocalinux

This guide explains how to update Vocalinux to the latest version.

## Quick Update (Recommended)

### If You Installed via curl (One-liner)

Simply re-run the installation command with the new version tag:

```bash
curl -fsSL https://raw.githubusercontent.com/jatinkrmalik/vocalinux/main/install.sh | bash -s -- --tag=v0.5.0-beta
```

The installer will:
- Update your existing installation
- Preserve your configuration and models
- Install any new dependencies

> **Note**: The installer automatically detects and updates existing installations.

### If You Installed from Source

```bash
cd vocalinux
git fetch origin
git checkout v0.5.0-beta
./install.sh
```

Or to always get the latest main branch:

```bash
cd vocalinux
git pull origin main
./install.sh
```

---

## Detailed Update Methods

### Method 1: Reinstall via Installer (Easiest)

The installer handles everything automatically:

```bash
# From the repo (if you have it cloned)
cd vocalinux
./install.sh --tag=v0.4.1-alpha

# Or via curl (for any installation)
curl -fsSL https://raw.githubusercontent.com/jatinkrmalik/vocalinux/main/install.sh | bash -s -- --tag=v0.5.0-beta
```

**What gets preserved:**
- Your configuration at `~/.config/vocalinux/`
- Your speech models at `~/.local/share/vocalinux/models/`
- Your custom settings and preferences

### Method 2: Manual Update (Advanced)

If you prefer manual control over the update process:

```bash
# 1. Navigate to your vocalinux directory
cd vocalinux

# 2. Pull the latest changes
git fetch origin
git checkout v0.5.0-beta

# 3. Activate your virtual environment
source venv/bin/activate

# 4. Update the package
pip install --upgrade .

# 5. Exit and restart
exit
vocalinux
```

---

## Checking Your Current Version

To see which version you have installed:

```bash
# Check the package version
python3 -c "import vocalinux; print(vocalinux.version.__version__)"

# Or check from the repo
git describe --tags
```

---

## What's New in v0.5.0-beta

- **Customizable keyboard shortcuts**: Configure your own activation shortcuts via GUI
- **Modern settings dialog**: Redesigned with GNOME HIG styling
- **Improved audio feedback**: Pleasant gliding tones for recording status
- **Enhanced Wayland support**: Better keyboard shortcut handling on Wayland
- **Microphone reconnection**: Automatic reconnection when microphone disconnects
- **80%+ test coverage**: Comprehensive test suite for reliability
- **Interactive installer**: Smart hardware detection and guided installation

See the [full changelog](https://github.com/jatinkrmalik/vocalinux/releases/tag/v0.5.0-beta).

---

## Previous Versions

### v0.4.1-alpha

- **Language selector UI**: Choose from 10 languages with auto-detection support for Whisper
- **App drawer launch fix**: Desktop entry now works when installing from local repo
- **Better commit handling**: Fixed error with special characters in commit messages
- **Improved update mechanism**: Corrected git fetch syntax for tag-based updates

### v0.4.0-alpha

- **Multi-language support**: French, German, and Russian
- **Debian 13+ compatibility**: Fixed appindicator package issues
- **Python 3.12+ support**: Improved venv handling
- **Better install script**: Tag-based version selection

---

## Troubleshooting

### Update Won't Install

**Symptom:** Installation fails during update

**Solution:** Run the uninstaller first, then reinstall:

```bash
# Keep your config and models
./uninstall.sh --keep-config --keep-data

# Reinstall
curl -fsSL https://raw.githubusercontent.com/jatinkrmalik/vocalinux/main/install.sh | bash -s -- --tag=v0.5.0-beta
```

### Old Version Still Running

**Symptom:** After update, old version is still active

**Solution:** Fully exit and restart:

```bash
# Kill any running instances
pkill -f vocalinux

# Start fresh
vocalinux
```

### Dependencies Changed

**Symptom:** New version has different system dependencies

**Solution:** The installer handles this, but if you see errors:

```bash
sudo apt update
sudo apt install -y python3-gi python3-gi-cairo gir1.2-gtk-3.0
```

---

## Automatic Updates (Coming Soon)

We're working on an in-app update mechanism. For now, please use the manual update methods above.

To check if a new version is available:

```bash
# Check latest release
curl -s https://api.github.com/repos/jatinkrmalik/vocalinux/releases/latest | grep "tag_name"
```

---

## Need Help?

- 📖 [Installation Guide](INSTALL.md)
- 📖 [User Guide](USER_GUIDE.md)
- 🐛 [Report Issues](https://github.com/jatinkrmalik/vocalinux/issues)
- 💬 [Discussions](https://github.com/jatinkrmalik/vocalinux/discussions)
