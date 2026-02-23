# Updating Vocalinux

This guide explains how to update Vocalinux to the latest version.

## What's New in v0.7.0-beta

### 🚀 Highlights

| Feature | Description |
|---------|-------------|
| **🖥️ Autostart Support** | Launch Vocalinux automatically on desktop session startup |
| **⚙️ Tabbed Settings** | Completely redesigned settings dialog with organized tabs |
| **🎮 Intel GPU Detection** | Automatically detects incompatible Intel GPUs and falls back to CPU |
| **🔒 Single Instance** | Prevents multiple Vocalinux instances from running simultaneously |

### ✨ New Features

- **Autostart on Login** — Added XDG autostart support via settings dialog and system tray
- **Tabbed Settings Dialog** — Reorganized settings into Speech Engine, Recognition, Text Injection, Audio Feedback, and General tabs
- **Intel GPU Compatibility Detection** — Detects incompatible Intel GPUs and automatically falls back to CPU processing
- **Multiple Instance Prevention** — Shows notification and exits if Vocalinux is already running
- **Evdev Device Management** — Automatically removes disconnected input devices to prevent CPU spin

### 🐛 Bug Fixes

- **#254**: Improved GPU detection to avoid false positives on systems without dev libraries
- **#251**: Skip IBus setup when daemon is not running, enable fallback to other methods
- **#243**: Prevent `dnf check-update` from exiting script on Fedora
- **#240**: Raise exception on IBus setup failure to enable automatic fallback
- **#234**: Removed leading space from first speech transcription
- **#242/#253**: Removed disconnected evdev devices to prevent CPU spin

### 🔧 Improvements

- **Web SEO Enhancements** — Added 7 new optimized pages for organic traffic
- **Mobile Responsiveness** — Improved mobile and tablet layout for the website
- **Better Fedora Support** — Fixed dnf check-update behavior
- **Improved Device Handling** — More robust handling of input device connections/disconnections

See the [full changelog](https://github.com/jatinkrmalik/vocalinux/releases/tag/v0.7.0-beta).

---

## Quick Update

### If You Installed via curl (Recommended)

Simply re-run the installation command:

```bash
curl -fsSL https://raw.githubusercontent.com/jatinkrmalik/vocalinux/v0.7.0-beta/install.sh | bash
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
git checkout v0.7.0-beta
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
curl -fsSL https://raw.githubusercontent.com/jatinkrmalik/vocalinux/v0.7.0-beta/install.sh | bash
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
