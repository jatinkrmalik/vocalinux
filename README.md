# <img src="https://github.com/user-attachments/assets/56dabe5c-5c65-44d5-a36a-429c9fea0719" width="30" height="30"> Vocalinux

#### Voice-to-text for Linux, finally done right!

<!-- Project Status -->
[![Status: Alpha](https://img.shields.io/badge/Status-Alpha-orange)](https://github.com/jatinkrmalik/vocalinux)
[![GitHub release](https://img.shields.io/github/v/release/jatinkrmalik/vocalinux?include_prereleases)](https://github.com/jatinkrmalik/vocalinux/releases)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)


<!-- Build & Quality -->
[![Vocalinux CI](https://github.com/jatinkrmalik/vocalinux/workflows/Vocalinux%20CI/badge.svg)](https://github.com/jatinkrmalik/vocalinux/actions)
[![Platform: Linux](https://img.shields.io/badge/platform-Linux-lightgrey)](https://github.com/jatinkrmalik/vocalinux)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Made with GTK](https://img.shields.io/badge/Made%20with-GTK-green)](https://www.gtk.org/)
[![codecov](https://codecov.io/gh/jatinkrmalik/vocalinux/branch/main/graph/badge.svg)](https://codecov.io/gh/jatinkrmalik/vocalinux)

<!-- Tech & Community -->
[![GitHub stars](https://img.shields.io/github/stars/jatinkrmalik/vocalinux)](https://github.com/jatinkrmalik/vocalinux/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/jatinkrmalik/vocalinux)](https://github.com/jatinkrmalik/vocalinux/network)
[![GitHub watchers](https://img.shields.io/github/watchers/jatinkrmalik/vocalinux)](https://github.com/jatinkrmalik/vocalinux/watchers)
[![Last commit](https://img.shields.io/github/last-commit/jatinkrmalik/vocalinux)](https://github.com/jatinkrmalik/vocalinux/commits)
[![Commit activity](https://img.shields.io/github/commit-activity/m/jatinkrmalik/vocalinux)](https://github.com/jatinkrmalik/vocalinux/commits)
[![Contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![GitHub issues](https://img.shields.io/github/issues/jatinkrmalik/vocalinux)](https://github.com/jatinkrmalik/vocalinux/issues)

![Vocalinux Users](https://github.com/user-attachments/assets/e3d8dd16-3d4f-408c-b899-93d85e98b107)

**A seamless free open-source private voice dictation system for Linux**, comparable to the built-in solutions on macOS and Windows.

> 🎉 **Alpha Release!**
>
> We're excited to share Vocalinux with the community.
> Try it out and [let us know what you think](https://github.com/jatinkrmalik/vocalinux/issues)!

---

## ✨ Features

- 🎤 **Double-tap Ctrl** to start/stop voice dictation
- ⚡ **Real-time transcription** with minimal latency
- 🌎 **Universal compatibility** across all Linux applications
- 🔒 **Offline operation** for privacy and reliability (with VOSK)
- 🤖 **Optional Whisper AI** support for enhanced accuracy
- 🎨 **System tray integration** with visual status indicators
- 🔊 **Audio feedback** for recording status
- ⚙️ **Graphical settings** dialog for easy configuration

## 🚀 Quick Install

### One-liner Installation (Recommended)

```bash
curl -fsSL https://raw.githubusercontent.com/jatinkrmalik/vocalinux/main/install.sh | bash
```

This will:
- Clone the repository to `~/.local/share/vocalinux-install`
- Install all system dependencies
- Set up a virtual environment in `~/.local/share/vocalinux/venv`
- Install **both VOSK and Whisper AI** speech engines
- Create a symlink at `~/.local/bin/vocalinux`
- Download the default **Whisper tiny** speech model (~75MB)

> ⏱️ **Note**: Installation takes ~5-10 minutes due to Whisper AI dependencies (PyTorch with CUDA support, ~2.3GB).

**Whisper with CPU-only PyTorch (no NVIDIA GPU needed):**
```bash
curl -fsSL https://raw.githubusercontent.com/jatinkrmalik/vocalinux/main/install.sh | bash -s -- --whisper-cpu
```
This installs Whisper with CPU-only PyTorch (~200MB instead of ~2.3GB). Works great for systems without NVIDIA GPU.

**For low-RAM systems (8GB or less) - VOSK only:**
```bash
curl -fsSL https://raw.githubusercontent.com/jatinkrmalik/vocalinux/main/install.sh | bash -s -- --no-whisper
```
This skips Whisper installation entirely and configures VOSK as the default engine.

### Alternative: Install from Source

```bash
# Clone the repository
git clone https://github.com/jatinkrmalik/vocalinux.git
cd vocalinux

# Run the installer (will prompt for Whisper)
./install.sh

# Or with Whisper support
./install.sh --with-whisper
```

The installer handles everything: system dependencies, Python environment, speech models, and desktop integration.

### After Installation

```bash
# If ~/.local/bin is in your PATH (recommended):
vocalinux

# Or activate the virtual environment first:
source ~/.local/bin/activate-vocalinux.sh
vocalinux

# Or run directly:
~/.local/share/vocalinux/venv/bin/vocalinux
```

Or launch it from your application menu!

### Uninstall

```bash
# If installed via curl:
curl -fsSL https://raw.githubusercontent.com/jatinkrmalik/vocalinux/main/uninstall.sh | bash

# If installed from source:
./uninstall.sh
```

## 📋 Requirements

- **OS**: Ubuntu 22.04+ (other Linux distros may work)
- **Python**: 3.8 or newer
- **Display**: X11 or Wayland
- **Hardware**: Microphone for voice input

## 🎙️ Usage

### Voice Dictation

1. **Double-tap Ctrl** to start recording
2. Speak clearly into your microphone
3. **Double-tap Ctrl** again (or pause speaking) to stop

### Voice Commands

| Command | Action |
|---------|--------|
| "new line" | Inserts a line break |
| "period" / "full stop" | Types a period (.) |
| "comma" | Types a comma (,) |
| "question mark" | Types a question mark (?) |
| "exclamation mark" | Types an exclamation mark (!) |
| "delete that" | Deletes the last sentence |
| "capitalize" | Capitalizes the next word |

### Command Line Options

```bash
vocalinux --help              # Show all options
vocalinux --debug             # Enable debug logging
vocalinux --engine whisper    # Use Whisper AI engine
vocalinux --model medium      # Use medium-sized model
vocalinux --wayland           # Force Wayland mode
```

## ⚙️ Configuration

Configuration is stored in `~/.config/vocalinux/config.json`:

```json
{
  "speech_recognition": {
    "engine": "vosk",
    "model_size": "small",
    "vad_sensitivity": 3,
    "silence_timeout": 2.0
  }
}
```

You can also configure settings through the graphical Settings dialog (right-click the tray icon).

## 🔧 Development Setup

```bash
# Clone and install in dev mode
git clone https://github.com/jatinkrmalik/vocalinux.git
cd vocalinux
./install.sh --dev

# Activate environment
source venv/bin/activate

# Run tests
pytest

# Run from source with debug
python -m vocalinux.main --debug
```

## 📁 Project Structure

```
vocalinux/
├── src/vocalinux/           # Main application code
│   ├── speech_recognition/  # Speech recognition engines
│   ├── text_injection/      # Text injection (X11/Wayland)
│   ├── ui/                  # GTK UI components
│   └── utils/               # Utility functions
├── tests/                   # Test suite
├── resources/               # Icons and sounds
├── docs/                    # Documentation
└── web/                     # Website source
```

## 📖 Documentation

- [Installation Guide](docs/INSTALL.md) - Detailed installation instructions
- [User Guide](docs/USER_GUIDE.md) - Complete user documentation
- [Contributing](CONTRIBUTING.md) - Development setup and contribution guidelines

## 🗺️ Roadmap

- [x] ~~Custom icon design~~ ✅
- [x] ~~Graphical settings dialog~~ ✅
- [x] ~~Whisper AI support~~ ✅
- [ ] Multi-language support
- [ ] Application-specific commands
- [ ] Debian/Ubuntu package (.deb)
- [ ] Improved Wayland support
- [ ] Voice command customization

## 🤝 Contributing

We welcome contributions! Whether it's bug reports, feature requests, or code contributions, please check out our [Contributing Guide](CONTRIBUTING.md).

### Quick Links

- 🐛 [Report a Bug](https://github.com/jatinkrmalik/vocalinux/issues/new?template=bug_report.md)
- 💡 [Request a Feature](https://github.com/jatinkrmalik/vocalinux/issues/new?template=feature_request.md)
- 💬 [Discussions](https://github.com/jatinkrmalik/vocalinux/discussions)


## ⭐ Support

If you find Vocalinux useful, please consider:
- ⭐ Starring this repository
- 🐛 Reporting bugs you encounter
- 📖 Improving documentation
- 🔀 Contributing code

## 📜 License

This project is licensed under the **GNU General Public License v3.0** - see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  Made with ❤️ for the Linux community
</p>
