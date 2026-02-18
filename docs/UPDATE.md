# Updating Vocalinux

This guide explains how to update Vocalinux to the latest version.

## What's New in v0.6.2-beta

### 🐛 Bug Fixes

- **Fixed #221**: Add missing `psutil` dependency - Fresh installs now work correctly (pywhispercpp requires psutil internally)
- **Fixed #219**: Suppress `[BLANK_AUDIO]` tokens in whisper.cpp output - Cleaner transcription results
- **Fixed #204**: Resolve PyAudio `paInt16` attribute error on audio device reconnection
- **Fixed #205**: Ensure whisper module is properly installed with `--auto` flag

### 🔧 Improvements

- **Better Multi-Distro Installation** - Improved Vulkan shader package detection and installation for Ubuntu, Debian, Fedora, Arch, and more
- **CI Improvements** - Fixed nightly build tag cleanup and older release deletion

See the [full changelog](https://github.com/jatinkrmalik/vocalinux/releases/tag/v0.6.2-beta).

---

## Previous Versions

### v0.6.2-beta

- **Interactive Backend Selection**: Choose between GPU (Vulkan/CUDA) or CPU backend
- **Enhanced Welcome Message**: Redesigned end-of-installation experience
- **Simplified Install Commands**: No more `--tag` parameter needed
- **Better GPU Support**: Fixed Vulkan development library detection

### v0.6.0-beta

- **whisper.cpp as default engine**: Fast, works with any GPU via Vulkan
- **Multi-language support**: Auto-detect language with manual override
- **System tray indicator**: Better desktop integration
- **Wayland support**: Full compatibility with modern Linux desktops

---

## Quick Update (Recommended)

### If You Installed via curl (One-liner)

Simply re-run the installation command with the new version tag:

```bash
curl -fsSL https://raw.githubusercontent.com/jatinkrmalik/vocalinux/v0.6.2-beta/install.sh | bash
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
git checkout v0.6.2-beta
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
curl -fsSL https://raw.githubusercontent.com/jatinkrmalik/vocalinux/v0.6.2-beta/install.sh | bash
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
git checkout v0.6.2-beta

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

## What's New in v0.6.2-beta

### 🚀 Major Feature: whisper.cpp is Now Default!

This release brings **whisper.cpp** as the new default speech recognition engine—a game-changing upgrade!

**Key Improvements:**
- **⚡ 10x faster installation** — No more 2.3GB PyTorch downloads (~1-2 min vs ~5-10 min)
- **🎮 Universal GPU support** — Works with AMD, Intel, and NVIDIA via Vulkan (not just NVIDIA CUDA)
- **💾 Smaller footprint** — Tiny model is only ~39MB vs ~75MB
- **🔥 Better performance** — C++ optimized inference with true multi-threading (no Python GIL)
- **🌍 99+ languages** with automatic language detection

**Additional Improvements:**
- **Interactive installer**: Choose between 3 engines (whisper.cpp, Whisper, VOSK)
- **Hardware auto-detection**: Automatically detects your GPU and recommends optimal settings
- **Enhanced logging**: Comprehensive debug info for whisper.cpp troubleshooting
- **Better documentation**: Updated all docs to reflect whisper.cpp as the new default

See the [full changelog](https://github.com/jatinkrmalik/vocalinux/releases/tag/v0.6.2-beta).

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
curl -fsSL https://raw.githubusercontent.com/jatinkrmalik/vocalinux/v0.6.2-beta/install.sh | bash
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
