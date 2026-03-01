# Updating Vocalinux

This guide explains how to update Vocalinux to the latest version.

## What's New in v0.8.0-beta

### 🚀 Highlights

| Feature | Description |
|---------|-------------|
| **🎤 Push-to-Talk Mode** | Hold the shortcut key to speak, release to stop |
| **⚙️ Voice Commands Toggle** | Enable or disable voice commands, with VOSK auto-enable in auto mode |
| **⌨️ Shortcut Reliability** | Improved callback lifecycle and mode switching stability |
| **🧠 Input Compatibility** | Better IBus detection and audio device/channel compatibility |

### ✨ New Features

- **Push-to-Talk Shortcut Mode** — Added hold-to-speak mode alongside double-tap toggle mode
- **Mode-aware Shortcut UI** — Updated settings text and behavior for toggle vs push-to-talk workflows
- **Voice Commands Optional** — Voice commands can be disabled, with automatic enable behavior for VOSK

### 🐛 Bug Fixes

- **#277**: Detect active IBus input method before using IBus injection
- **#275**: Detect and use device-supported channel count
- **#268**: Prevent GTK startup dialog crash on Fedora
- **#261**: Resolve text injection issues for better reliability
- **#259**: Prevent recognition thread state flicker
- **#262/#263**: Auto-detect audio sample rate for better hardware compatibility

### 🔧 Improvements

- **Web SEO Enhancements** — Added 8 additional optimized pages for discoverability
- **Homepage Refresh** — Updated voice-themed visual polish on the web landing page

See the [full changelog](https://github.com/jatinkrmalik/vocalinux/releases/tag/v0.8.0-beta).

---

## Quick Update

### If You Installed via curl (Recommended)

Simply re-run the installation command:

```bash
curl -fsSL https://raw.githubusercontent.com/jatinkrmalik/vocalinux/v0.8.0-beta/install.sh | bash
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
git checkout v0.8.0-beta
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
curl -fsSL https://raw.githubusercontent.com/jatinkrmalik/vocalinux/v0.8.0-beta/install.sh | bash
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
