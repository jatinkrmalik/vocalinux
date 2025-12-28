# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- TBD

## [0.2.0-alpha] - 2024-12-28

### 🎉 First Alpha Release!

This is the first public alpha release of Vocalinux. We're excited to share it with the community!

### Added
- **Modern packaging**: Added `pyproject.toml` for PEP 517/518 compliant builds
- **About section**: Settings dialog now shows version, open source info, and author credits
- **GitHub templates**: Bug report and feature request issue templates
- **Pull request template**: Standardized PR process
- **Improved CI/CD pipeline**: 
  - Test matrix for Python 3.8, 3.10, 3.11
  - Better release workflow with version verification
  - Streamlined workflow conditions
- **One-liner installation**: Easy install command in README
- **Comprehensive documentation**: Updated README, CONTRIBUTING, and docs

### Changed
- Version bumped to 0.2.0-alpha
- Updated copyright year to 2025
- Simplified GitHub Actions workflow (removed complex path filtering)
- Updated action versions (checkout@v4, setup-python@v5, etc.)

### Fixed
- Various CI pipeline issues with conditional job execution

## [0.1.0] - 2024-11-15

### Added
- Initial release
- Double-tap Ctrl keyboard shortcut for voice dictation
- VOSK speech recognition engine with offline support
- Optional Whisper AI engine for enhanced accuracy
- Real-time transcription with minimal latency
- System tray integration with status indicators
- Audio feedback for recording status
- Voice commands (new line, period, comma, etc.)
- X11 and Wayland text injection support
- Graphical settings dialog
- Custom application icons
- Desktop entry for application launcher
- Comprehensive installation script
- Uninstall script
- User and developer documentation

### Technical Details
- Python 3.8+ support
- GTK3 UI with AppIndicator
- PyAudio for audio capture
- pynput for keyboard shortcuts
- XDG Base Directory compliance
- Virtual environment isolation

---

[Unreleased]: https://github.com/jatinkrmalik/vocalinux/compare/v0.2.0-alpha...HEAD
[0.2.0-alpha]: https://github.com/jatinkrmalik/vocalinux/compare/v0.1.0...v0.2.0-alpha
[0.1.0]: https://github.com/jatinkrmalik/vocalinux/releases/tag/v0.1.0
