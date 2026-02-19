# Updating Vocalinux

This guide explains how to update Vocalinux to the latest version.

## What's New in v0.6.3-beta

### 🐛 Bug Fixes

- **Fixed #220**: Installer default tag now points to correct version
- **Fixed #221**: Add missing `psutil` dependency for fresh installs
- **Fixed #219**: Suppress `[BLANK_AUDIO]` tokens in whisper.cpp output
- **Fixed #204**: Resolve PyAudio `paInt16` attribute error on audio device reconnection
- **Fixed #205**: Ensure whisper module is properly installed with `--auto` flag

### 🔧 Improvements

- **Process Check & Interactive Prompts** - Installer now detects and prompts to stop running Vocalinux before updating
- **Command Processor Fix** - No more leading space on first speech transcription
- **Better Multi-Distro Installation** - Improved Vulkan shader package detection

See the [full changelog](https://github.com/jatinkrmalik/vocalinux/releases/tag/v0.6.3-beta).

---

## Quick Update

### If You Installed via curl (Recommended)

Simply re-run the installation command:

```bash
curl -fsSL https://raw.githubusercontent.com/jatinkrmalik/vocalinux/v0.6.3-beta/install.sh | bash
```

The installer will:
- ✅ Detect and stop any running Vocalinux processes
- ✅ Update your existing installation
- ✅ Preserve your configuration and models
- ✅ Install any new dependencies

### If You Installed from Source

```bash
cd vocalinux
git fetch origin
git checkout v0.6.3-beta
./install.sh
```

Or to get the latest development version:

```bash
cd vocalinux
git pull origin main
./install.sh
```

---

## Checking Your Current Version

```bash
python3 -c "import vocalinux; print(vocalinux.version.__version__)"
```

---

## Troubleshooting

### Update Issues?

If your update doesn't go smoothly, try a clean reinstall:

```bash
# Uninstall (keeps your config and models by default)
./uninstall.sh --keep-config --keep-data

# Or uninstall completely
./uninstall.sh

# Reinstall fresh
curl -fsSL https://raw.githubusercontent.com/jatinkrmalik/vocalinux/v0.6.3-beta/install.sh | bash
```

### Old Version Still Running

```bash
# Kill any running instances
pkill -f vocalinux

# Start fresh
vocalinux
```

### Missing Dependencies

If you see dependency errors:

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3-gi python3-gi-cairo gir1.2-gtk-3.0

# Fedora
sudo dnf install -y python3-gobject gtk3

# Arch
sudo pacman -S python-gobject gtk3
```

---

## Need Help?

- 📖 [Installation Guide](INSTALL.md)
- 🐛 [Report Issues](https://github.com/jatinkrmalik/vocalinux/issues)
- 💬 [Discussions](https://github.com/jatinkrmalik/vocalinux/discussions)
