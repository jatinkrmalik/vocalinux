# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com).

## [Unreleased]

### Added

- Flexible key parsing system in `base.py`: `parse_keys()`, `format_shortcut_display()`, `is_preset_shortcut()`, `is_double_tap_shortcut()`, `is_combo_shortcut()`, `is_valid_key_name()`
- `MODIFIER_KEYS` and `SPECIAL_KEYS` validation sets for key name validation
- `PRESET_SHORTCUTS` dict (with backward-compatible `SUPPORTED_SHORTCUTS` alias)
- Tests for flexible shortcut system (`TestFlexibleShortcuts`)
