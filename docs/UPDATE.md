# Updating Vocalinux

This guide explains how to update Vocalinux to the latest version.

## What's New in v0.10.1-beta

> **Note:** Real-time streaming transcription support is currently under active development and is
> available as an **experimental** toggle in Settings. It is disabled by default while architecture
> and model-specific behavior continue to be refined.

### 🚀 Highlights

| Feature | Description |
|---------|-------------|
| **🖼️ Tray Resource Reliability** | Bundled package resources now prevent missing system tray icons |
| **🧠 Engine Switch Safety** | Recognition now stops before engine changes to avoid segfaults |
| **⌨️ Keyboard Layout Preservation** | XKB layout is preserved when activating the Vocalinux IBus engine |
| **🪟 Settings Dialog Compatibility** | Added an explicit Close button for improved WM interoperability |
| **⚡ Suspend/Resume Recovery** | App now automatically recovers speech recognition and keyboard shortcuts after system suspend/resume |
| **🎤 Push-to-Talk Reliability** | Fixed premature transcription triggering on silence during push-to-talk mode |

### ✨ Scope

- **Patch-focused release** — No new feature surface; this version is dedicated to stability and compatibility fixes
- **Desktop reliability hardening** — Improved behavior across tray, engine switching, settings dialog actions, and keyboard layout handling
- **Suspend/Resume stability** — New D-Bus handler ensures app survives system sleep cycles

### 🐛 Bug Fixes

- **#349 / #354**: Bundle resources in package to fix missing system tray icons
- **#350 / #355**: Stop recognition before switching engines to prevent segfaults
- **#323 / #356**: Add Close button to settings dialog for WM compatibility
- **#292 / #343**: Preserve XKB layout when activating Vocalinux IBus engine
- **#359**: Prevent premature transcription during push-to-talk silence
- **#367 / #369**: Auto-recover speech recognition after system resume via new suspend handler
- **#371**: Restart keyboard shortcut backend after system resume
- **#372**: Delay keyboard restart to allow USB device re-enumeration after resume

### 🔧 Improvements

- Bumped npm/yarn dependency group across the web workspace (#346)
- Bumped `brace-expansion` in development dependencies (#357)
- Disabled copy-to-clipboard by default in Settings (#370)

See the [full changelog](https://github.com/jatinkrmalik/vocalinux/releases/tag/v0.10.1-beta).

---

## What's New in v0.9.0-beta

### 🚀 Highlights

| Feature | Description |
|---------|-------------|
| **⌨️ Left/Right Modifier Keys** | Choose Left Ctrl vs Right Ctrl (etc.) as your shortcut trigger |
| **🔔 Sound Effects Toggle** | Enable or disable audio feedback from the Settings dialog |
| **📋 Wayland Clipboard Fallback** | Automatic clipboard copy when virtual keyboard injection isn't available |
| **🛠️ Installation Polish** | Better pipx/Debian guidance and headless display detection |

### ✨ New Features

- **Left/Right Modifier Key Distinction** — Shortcuts now support `Left Ctrl`, `Right Alt`, etc., with grouped UI in Settings
- **Sound Effects Toggle** — New Audio Settings toggle to silence start/stop/error sounds
- **Clipboard Fallback for Wayland** — Auto-copies text via `wl-copy`/`xclip` when injection unavailable (KDE Plasma etc.)
- **Display Availability Check** — Graceful error message when running in headless environments

### 🐛 Bug Fixes

- **#308**: Distinguish left vs right modifier keys (evdev + pynput backends)
- **#307**: Remove unwanted leading space when starting a new transcription session
- **#305**: Pass configured shortcut mode to `KeyboardShortcutManager` on startup
- **#299**: Add clipboard fallback for Wayland compositors without virtual keyboard support
- **#289**: Improve Debian/pipx installation error messages and cross-distro dependency guidance

### 🔧 Improvements

- **Grouped shortcut selector** — Settings dropdown now organises shortcuts by Either/Left/Right side
- **pipx documentation** — New `DISTRO_COMPATIBILITY.md` section for pipx users

See the [full changelog](https://github.com/jatinkrmalik/vocalinux/releases/tag/v0.9.0-beta).

---

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
curl -fsSL https://raw.githubusercontent.com/jatinkrmalik/vocalinux/main/install.sh | bash
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
git checkout v0.10.1-beta
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
curl -fsSL https://raw.githubusercontent.com/jatinkrmalik/vocalinux/main/install.sh | bash
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
