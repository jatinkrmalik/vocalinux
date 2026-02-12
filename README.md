# <img src="https://github.com/user-attachments/assets/56dabe5c-5c65-44d5-a36a-429c9fea0719" width="30" height="30"> Vocalinux

#### Voice-to-text for Linux, finally done right!

<!-- Project Status -->
[![Status: Beta](https://img.shields.io/badge/Status-Beta-blue)](https://github.com/jatinkrmalik/vocalinux)
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

**A seamless free open-source private voice dictation system for Linux**, comparable to built-in solutions on macOS and Windows.

## 📚 What's New in v0.6.0-beta

We're excited to announce our first **Beta release**! Vocalinux has evolved significantly with the biggest change yet: **whisper.cpp is now the default speech recognition engine**, bringing massive improvements to speed, compatibility, and ease of installation.

### 🚀 Major Change: whisper.cpp is Now Default!

**Why this is a game-changer:**
- **⚡ 10x faster installation** - No more 2.3GB PyTorch downloads (was ~5-10 min, now ~1-2 min)
- **🎮 Universal GPU support** - Works with AMD, Intel, and NVIDIA via Vulkan (not just NVIDIA CUDA)
- **💾 Smaller footprint** - Tiny model is only ~39MB vs ~75MB Whisper
- **🔥 Better performance** - C++ optimized inference with multi-threading
- **🐍 No Python GIL** - True parallel processing for faster transcription

### 🐛 Critical Bug Fixes
- Fixed text escaping issues (apostrophes and quotes no longer have backslash escapes)
- Fixed stop sound being transcribed as "thank you"
- Fixed missing spaces after punctuation when transcribing again

### ✨ Key New Features
- **🤖 whisper.cpp integration** - High-performance C++ speech recognition with Vulkan GPU acceleration
- **📦 Interactive installer** - Choose between 3 engines: whisper.cpp (recommended), Whisper, or VOSK
- **🔧 Hardware auto-detection** - Automatically detects your GPU and recommends optimal settings
- **Customizable keyboard shortcuts** - Configure your own activation shortcuts via GUI
- **Modern GNOME HIG settings dialog** - Complete UI overhaul following GNOME design guidelines
- **Pleasant audio feedback** - Gliding tones replace harsh beeps
- **Better Wayland support** - Native keyboard shortcuts without XWayland

### 🔧 Quality Improvements
- **80%+ test coverage** - Comprehensive test suite across all modules
- **Microphone reconnection** - Automatic recovery when microphone disconnects
- **Audio buffer management** - Prevents memory issues during long recordings
- **Enhanced logging** - Comprehensive debug info for whisper.cpp troubleshooting

---

> 🎉 **Beta Release with whisper.cpp!**
>
> We're excited to share Vocalinux Beta with the community!
> whisper.cpp brings **10x faster installation** and **universal GPU support**.
> See "What's New" above for details.

---

## ✨ Features

- 🎤 **Double-tap Ctrl** to start/stop voice dictation
- ⚡ **Real-time transcription** with minimal latency
- 🌎 **Universal compatibility** across all Linux applications
- 🔒 **100% Offline operation** for privacy and reliability
- 🤖 **whisper.cpp by default** - High-performance C++ speech recognition
- 🎮 **Universal GPU support** - Vulkan acceleration for AMD, Intel, and NVIDIA
- 🎨 **System tray integration** with visual status indicators
- 🔊 **Pleasant audio feedback** - smooth gliding tones, headphone-friendly
- ⚙️ **Graphical settings** dialog for easy configuration
- 📦 **3 engine choices** - whisper.cpp (default), OpenAI Whisper, or VOSK

## 📸 Screenshots

Here are some screenshots showcasing Vocalinux in action:

<table>
  <tr>
    <td align="center">
      <img src="resources/screenshots/00-transcription.png" alt="Transcription in Action" width="350"><br>
      <em>Real-time voice-to-text transcription</em>
    </td>
    <td align="center">
      <img src="resources/screenshots/02-system-tray.png" alt="System Tray" width="350"><br>
      <em>System tray with listening indicator</em>
    </td>
  </tr>
  <tr>
    <td align="center">
      <img src="resources/screenshots/05-about-view.png" alt="About View" width="350"><br>
      <em>About view with version info</em>
    </td>
    <td align="center">
      <img src="resources/screenshots/03-log-viewer.png" alt="Log Viewer" width="350"><br>
      <em>Log viewer for debugging</em>
    </td>
  </tr>
  <tr>
    <td colspan="2" align="center">
      <img src="resources/screenshots/04-features-overview.png" alt="Features Overview" width="500"><br>
      <em>Overview of key features and configuration options with annotations</em>
    </td>
  </tr>
</table>

## 🚀 Quick Install

### Interactive Install (Recommended)

Our new interactive installer guides you through setup with intelligent hardware detection:

```bash
curl -fsSL raw.githubusercontent.com/jatinkrmalik/vocalinux/main/install.sh -o /tmp/vl.sh && bash /tmp/vl.sh --tag=v0.6.0-beta
```

**Choose your engine:**
1. **whisper.cpp** ⭐ (Recommended) - Fast, works with any GPU via Vulkan
2. **Whisper** (OpenAI) - PyTorch-based, NVIDIA GPU only
3. **VOSK** - Lightweight, works on older systems

The installer will:
- **Auto-detect your hardware** (GPU, RAM, Vulkan support)
- **Recommend the best engine** for your system
- **Download the appropriate model** (~39MB for whisper.cpp tiny)
- **Install in ~1-2 minutes** (vs 5-10 min with old Whisper)

> **Note**: Installs v0.6.0-beta. For other versions, check [GitHub Releases](https://github.com/jatinkrmalik/vocalinux/releases).

### Installation Options

**Default (whisper.cpp - recommended):**
```bash
curl -fsSL raw.githubusercontent.com/jatinkrmalik/vocalinux/main/install.sh -o /tmp/vl.sh && bash /tmp/vl.sh --tag=v0.6.0-beta
```
Fastest installation (~1-2 min), universal GPU support via Vulkan.

**Whisper (OpenAI) - if you prefer PyTorch:**
```bash
curl -fsSL raw.githubusercontent.com/jatinkrmalik/vocalinux/main/install.sh -o /tmp/vl.sh && bash /tmp/vl.sh --tag=v0.6.0-beta --engine=whisper
```
NVIDIA GPU only (~5-10 min, downloads PyTorch + CUDA).

**VOSK only - for low-RAM systems:**
```bash
curl -fsSL raw.githubusercontent.com/jatinkrmalik/vocalinux/main/install.sh -o /tmp/vl.sh && bash /tmp/vl.sh --tag=v0.6.0-beta --engine=vosk
```
Lightweight option (~40MB), works on systems with 4GB RAM.

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

## 📚 What's New in v0.6.0-beta

We're excited to announce our first **Beta release** featuring **whisper.cpp as the default engine** - a massive upgrade that brings 10x faster installation and universal GPU support!

### 🚀 Major Change: whisper.cpp is Now Default!

**What makes whisper.cpp special:**
- **⚡ 10x faster installation** - No more 2.3GB PyTorch downloads (installation now takes ~1-2 min instead of 5-10 min)
- **🎮 Universal GPU support** - Works with AMD, Intel, and NVIDIA via Vulkan (not just NVIDIA CUDA like OpenAI Whisper)
- **💾 Smaller footprint** - Tiny model is only ~39MB vs ~75MB for Whisper
- **🔥 Better performance** - C++ optimized inference with true multi-threading (no Python GIL)
- **🌍 99+ languages** with automatic language detection

### 🐛 Critical Bug Fixes
- Fixed text escaping issues (apostrophes and quotes no longer have backslash escapes)
- Fixed stop sound being transcribed as "thank you"
- Fixed missing spaces after punctuation when transcribing again

### ✨ Key New Features
- **🤖 whisper.cpp integration** - High-performance C++ speech recognition with Vulkan GPU acceleration
- **📦 Interactive installer** - Choose between 3 engines: whisper.cpp (recommended), Whisper, or VOSK
- **🔧 Hardware auto-detection** - Automatically detects your GPU and recommends optimal settings
- **Customizable keyboard shortcuts** - Configure your own activation shortcuts via GUI
- **Modern GNOME HIG settings dialog** - Complete UI overhaul following GNOME design guidelines
- **Pleasant audio feedback** - Gliding tones replace harsh beeps
- **Better Wayland support** - Native keyboard shortcuts without XWayland

### 🔧 Quality Improvements
- **80%+ test coverage** - Comprehensive test suite across all modules
- **Microphone reconnection** - Automatic recovery when microphone disconnects
- **Audio buffer management** - Prevents memory issues during long recordings
- **Enhanced logging** - Comprehensive debug info for whisper.cpp troubleshooting

For a complete list of changes, see the release notes.

## 📋 Requirements

- **OS**: Linux (tested on Ubuntu 22.04+, Debian 11+, Fedora 39+, Arch Linux, openSUSE Tumbleweed)
- **Python**: 3.8 or newer
- **Display**: X11 or Wayland
- **Hardware**: Microphone for voice input

**Note:** See [Distribution Compatibility](docs/DISTRO_COMPATIBILITY.md) for distribution-specific information and experimental support for Gentoo, Alpine, Void, Solus, and more.

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
vocalinux --help                  # Show all options
vocalinux --debug                 # Enable debug logging
vocalinux --engine whisper_cpp    # Use whisper.cpp engine (default)
vocalinux --engine whisper        # Use OpenAI Whisper engine
vocalinux --engine vosk           # Use VOSK engine
vocalinux --model medium          # Use medium-sized model
vocalinux --wayland               # Force Wayland mode
```

## ⚙️ Configuration

Configuration is stored in `~/.config/vocalinux/config.json`:

```json
{
  "speech_recognition": {
    "engine": "whisper_cpp",
    "model_size": "tiny",
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
├── src/vocalinux/                 # Main application code
│   ├── speech_recognition/        # Speech recognition engines (VOSK, Whisper, whisper.cpp)
│   │   └── recognition_manager.py # Unified engine interface
│   ├── text_injection/            # Text injection (X11/Wayland)
│   ├── ui/                        # GTK UI components
│   └── utils/                     # Utility functions
│       ├── whispercpp_model_info.py   # whisper.cpp model metadata & hardware detection
│       └── vosk_model_info.py         # VOSK model metadata
├── tests/                         # Test suite
├── scripts/                       # Development utilities
│   └── generate_sounds.py         # Sound generation script
├── resources/                     # Icons and sounds
├── docs/                          # Documentation
└── web/                           # Website source
```

## 📖 Documentation

- [Installation Guide](docs/INSTALL.md) - Detailed installation instructions
- [Update Guide](docs/UPDATE.md) - How to update Vocalinux
- [User Guide](docs/USER_GUIDE.md) - Complete user documentation
- [Contributing](CONTRIBUTING.md) - Development setup and contribution guidelines

## 🔊 Sound Customization

Vocalinux uses smooth, pleasant gliding tones for audio feedback:

- **Start**: Ascending F4→A4 (0.6s) - positive, uplifting
- **Stop**: Descending A4→F4 (0.6s) - resolves completion
- **Error**: Lower descending E4→C4 (0.7s) - gentle but noticeable

All sounds use pure sine waves with smoothstep interpolation for buttery smooth pitch transitions - perfect for headphone use!

### Regenerate Sounds

To modify or regenerate the notification sounds:

```bash
python scripts/generate_sounds.py
```

This script generates all three sounds using the same smooth glide algorithm. You can edit the frequencies, durations, and amplitudes in the script to customize the sounds to your preference.

## 🗺️ Roadmap

- [x] ~~Custom icon design~~ ✅
- [x] ~~Graphical settings dialog~~ ✅
- [x] ~~Whisper AI support~~ ✅
- [x] ~~Multi-language support (FR, DE, RU)~~ ✅
- [x] ~~whisper.cpp integration (default engine)~~ ✅
- [x] ~~Vulkan GPU support~~ ✅
- [ ] In-app update mechanism
- [ ] Application-specific commands
- [ ] Debian/Ubuntu package (.deb)
- [x] ~~Improved Wayland support~~ ✅
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
