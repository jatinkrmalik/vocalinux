# <img src="https://github.com/user-attachments/assets/56dabe5c-5c65-44d5-a36a-429c9fea0719" width="50" height="50"> Vocalinux 

[![Vocalinux CI](https://github.com/jatinkrmalik/vocalinux/workflows/Vocalinux%20CI/badge.svg)](https://github.com/jatinkrmalik/vocalinux/actions?query=workflow%3A%22Vocalinux+CI%22)
[![codecov](https://codecov.io/gh/jatinkrmalik/vocalinux/branch/main/graph/badge.svg)](https://codecov.io/gh/jatinkrmalik/vocalinux)
[![Status: Early Development](https://img.shields.io/badge/Status-Early%20Development-orange)](https://github.com/jatinkrmalik/vocalinux)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg)](https://github.com/jatinkrmalik/vocalinux/issues)
[![GitHub issues](https://img.shields.io/github/issues/jatinkrmalik/vocalinux)](https://github.com/jatinkrmalik/vocalinux/issues)
[![GitHub release](https://img.shields.io/github/v/release/jatinkrmalik/vocalinux?include_prereleases)](https://github.com/jatinkrmalik/vocalinux/releases)

![Vocalinux Users](https://github.com/user-attachments/assets/e3d8dd16-3d4f-408c-b899-93d85e98b107)

A seamless voice dictation system for Linux, comparable to the built-in solutions on macOS and Windows.

## Overview

Vocalinux provides a user-friendly speech-to-text solution for Linux users with:

- Activation via double-tap Ctrl keyboard shortcut
- Real-time transcription with minimal latency
- Universal compatibility across applications
- Offline operation for privacy and reliability
- Visual indicators for microphone status
- Audio feedback for recognition status

## Quick Start

### Prerequisites

- Ubuntu 22.04 or newer (may work on other Linux distributions)
- Python 3.8 or newer
- X11 or Wayland desktop environment

### Installation

```bash
# Clone the repository
git clone https://github.com/jatinkrmalik/vocalinux.git
cd vocalinux

# Run the installer script
./install.sh
```

The installer will set up everything you need, including system dependencies and a Python virtual environment.

For detailed installation instructions and options, see [docs/INSTALL.md](docs/INSTALL.md).

### Running Vocalinux

After installation:

```bash
# Activate the virtual environment
source activate-vocalinux.sh

# Run Vocalinux
vocalinux
```

## Usage

### Voice Dictation

1. Double-tap the Ctrl key to start recording
2. Speak clearly into your microphone
3. Double-tap Ctrl again or pause speaking to stop recording

### Voice Commands

| Command | Action |
|---------|--------|
| "new line" | Inserts a line break |
| "period" | Types a period (.) |
| "comma" | Types a comma (,) |
| "question mark" | Types a question mark (?) |
| "delete that" | Deletes the last sentence |
| "capitalize" | Capitalizes the next word |

For a complete user guide, see [docs/USER_GUIDE.md](docs/USER_GUIDE.md).

## Configuration

Configuration is stored in `~/.config/vocalinux/config.json`. You can customize:

- Recognition engine (VOSK or Whisper)
- Model size (small, medium, large)
- Keyboard shortcuts
- Audio feedback
- UI behavior
- And more

## Features

### Custom Icons

Vocalinux includes custom icons for system trays and application launchers that visually indicate:
- Microphone inactive state
- Microphone active state
- Speech processing state

### Custom Sounds

Audio feedback is provided for:
- Start of recording
- End of recording
- Error conditions

You can customize these sounds by replacing the files in `resources/sounds/`.

## Advanced Usage

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

## Documentation

- [Installation Guide](docs/INSTALL.md) - Detailed installation instructions
- [User Guide](docs/USER_GUIDE.md) - Complete user documentation
- [Contributing](CONTRIBUTING.md) - Development setup and contribution guidelines

## Roadmap

Future development plans include:

1. ~~Custom icon design~~ ✅ (Implemented in v0.1.0)
2. Graphical settings dialog
3. Advanced voice commands for specific applications
4. Multi-language support
5. Better integration with popular applications
6. Improved model management
7. Customizable keyboard shortcuts via GUI
8. More audio feedback options

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for development setup instructions and contribution guidelines.

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.
