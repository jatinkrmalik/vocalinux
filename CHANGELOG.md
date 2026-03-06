# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com).

## [Unreleased]

### Added

- Custom keyboard shortcut support: users can now bind any key combination (e.g., Super+Ctrl, Ctrl+D, F5) as their voice typing shortcut
- "Custom..." option in the shortcut dropdown that reveals a live key capture widget
- ShortcutCaptureWidget: press "Change", then press desired keys to record a shortcut; ESC to cancel
- Arbitrary key combo support in both pynput (X11) and evdev (Wayland) backends
- Flexible key parsing system (`parse_keys()`, `format_shortcut_display()`, `is_preset_shortcut()`)
- Full evdev key code mappings for letters, F-keys, digits, and special keys

### Changed

- Keyboard shortcuts manager now accepts any valid key combination, not just the three presets
- evdev backend refactored to handle both double-tap presets and held-combo shortcuts
- Settings dialog uses `PRESET_SHORTCUTS` for dropdown population with "Custom..." as fourth option

### Fixed

- Escape shortcut display names in GTK markup calls (defense-in-depth against config tampering)
- Validate minimum 2 keys for custom shortcuts in capture widget
- Fix mode change not applied when using custom shortcut (dropdown ID "custom" was passed instead of actual shortcut string)
