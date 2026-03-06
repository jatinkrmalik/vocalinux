# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com).

## [Unreleased]

### Added

- Minimum 2-key validation in `ShortcutCaptureWidget._finalize_capture()`
- Custom keyboard shortcut capture widget in settings dialog
- Flexible key parsing system in `base.py`: `parse_keys()`, `format_shortcut_display()`, `is_preset_shortcut()`, `is_double_tap_shortcut()`, `is_combo_shortcut()`, `is_valid_key_name()`
- `MODIFIER_KEYS` and `SPECIAL_KEYS` validation sets for key name validation
- `PRESET_SHORTCUTS` dict (with backward-compatible `SUPPORTED_SHORTCUTS` alias)
- Tests for flexible shortcut system (`TestFlexibleShortcuts`)
- evdev backend: key code mappings for letters, F-keys, digits, and special keys (`LETTER_KEY_CODES`, `FKEY_CODES`, `DIGIT_KEY_CODES`, `SPECIAL_KEY_CODES`)
- evdev backend: `resolve_evdev_codes()` to resolve key names to evdev key codes
- evdev backend: `device_has_key()` generalized key capability check
- evdev backend: combo shortcut support (all keys held simultaneously)

### Fixed

- Escape `format_shortcut_display()` output with `GLib.markup_escape_text()` in all `set_markup()` calls in settings dialog (defense-in-depth against config tampering)

### Changed

- evdev backend: refactored `_handle_key_event` into `_handle_double_tap_event` and `_handle_combo_event`
- evdev backend: `is_available()` now validates all keys in combo shortcuts across devices
- evdev backend: `device_has_modifier_key()` now delegates to `device_has_key()`
