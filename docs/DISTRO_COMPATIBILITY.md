# Linux Distribution Compatibility

## Officially Supported Distributions

These distributions are tested and known to work well with Vocalinux:

| Distribution | Version | Status | Notes |
|--------------|---------|--------|-------|
| Ubuntu | 22.04+ | ✅ Full Support | Primary target, most thoroughly tested |
| Debian | 11+, Testing | ✅ Full Support | Well tested, use Ayatana AppIndicator on Debian 11+ |
| Fedora | 39+ | ✅ Good Support | Uses lib64 paths, fully supported |
| Arch Linux | Rolling | ✅ Good Support | Community tested, rolling release compatible |
| openSUSE | Tumbleweed | ✅ Good Support | Good support with zypper package manager |

## Experimental Support

These distributions may work but have known limitations or are less tested:

| Distribution | Status | Known Issues |
|--------------|--------|--------------|
| Gentoo | ⚠️ Experimental | No package manager support, manual install required. Packages are compiled from source which takes longer. |
| Alpine Linux | ⚠️ Experimental | Uses musl libc (not glibc). Some Python packages may not have pre-built wheels and may need to be compiled. |
| Void Linux | ⚠️ Experimental | Untested, manual install required. Uses xbps package manager. |
| Solus | ⚠️ Experimental | Untested, manual install required. Uses eopkg package manager. |
| Mageia | ⚠️ Experimental | Untested, uses dnf/urpmi package managers. |
| Linux Mint | ✅ Good Support | Based on Ubuntu, inherits Ubuntu compatibility |
| Pop!_OS | ✅ Good Support | Based on Ubuntu, inherits Ubuntu compatibility |
| elementary OS | ✅ Good Support | Based on Ubuntu, inherits Ubuntu compatibility |
| Zorin OS | ✅ Good Support | Based on Ubuntu, inherits Ubuntu compatibility |
| Manjaro | ✅ Good Support | Based on Arch, inherits Arch compatibility |
| EndeavourOS | ✅ Good Support | Based on Arch, inherits Arch compatibility |

## Not Supported

These distributions are known to be incompatible:

| Distribution | Status | Reason |
|--------------|--------|--------|
| NixOS | ❌ Not Supported | Completely different filesystem layout (/nix/store), incompatible with standard installer |

## Requirements by Distribution

### Ubuntu/Debian-based
```bash
sudo apt install -y python3-gi gir1.2-gtk-3.0 gir1.2-gdkpixbuf-2.0 \
  portaudio19-dev python3-dev python3-venv pkg-config
```

**Note for Debian 11+:** Use `gir1.2-ayatanaappindicator3-0.1` instead of `gir1.2-appindicator3-0.1`

### Fedora/RHEL-based
```bash
sudo dnf install -y python3-gobject gtk3-devel gobject-introspection-devel \
  portaudio-devel python3-devel python3-virtualenv pkg-config
```

### Arch Linux-based
```bash
sudo pacman -S --needed python-gobject gtk3 gobject-introspection \
  portaudio python pkg-config
```

### openSUSE
```bash
sudo zypper install -y python3-gobject python3-gobject-cairo gtk3 \
  gobject-introspection-devel portaudio-devel python3-devel \
  python3-virtualenv pkg-config
```

### Gentoo
```bash
sudo emerge dev-python/pygobject:3 x11-libs/gtk+:3 dev-libs/libappindicator:3 \
  media-libs/portaudio dev-lang/python:3.8
```

**Note:** Gentoo compiles packages from source, which will take longer.

### Alpine Linux
```bash
sudo apk add py3-gobject3 py3-pip gtk+3.0 py3-cairo portaudio-dev \
  py3-virtualenv pkgconf
```

**Note:** Alpine uses musl libc. Some Python packages may need to be compiled from source.

### Void Linux
```bash
sudo xbps-install -Sy python3-pip python3-gobject gtk+3 libappindicator \
  gobject-introspection portaudio-devel python3-devel pkg-config
```

### Solus
```bash
sudo eopkg install python3-pip python3-gobject gtk3 libappindicator \
  gobject-introspection-devel portaudio-devel python3-virtualenv pkg-config
```

### Mageia
```bash
sudo dnf install -y python3-gobject gtk3-devel gobject-introspection-devel \
  portaudio-devel python3-devel python3-virtualenv pkg-config
# or
sudo urpmi -y python3-gobject gtk3-devel gobject-introspection-devel \
  portaudio-devel python3-devel python3-virtualenv pkg-config
```

## Text Injection Tools

Vocalinux requires text injection tools to work with X11 or Wayland:

### For X11
- **xdotool**: Required for X11 sessions

### For Wayland
- **wtype**: Recommended for Wayland native sessions
- **ydotool**: Universal alternative that works with both X11 and Wayland
- **xdotool**: May work via XWayland fallback

### Installation by Distribution
```bash
# Ubuntu/Debian/Fedora/Arch/openSUSE
sudo apt install xdotool wtype     # Ubuntu/Debian
sudo dnf install xdotool wtype     # Fedora
sudo pacman -S xdotool wtype       # Arch
sudo zypper install xdotool wtype  # openSUSE
```

## Manual Installation

For unsupported or experimental distributions:

1. **Run the dependency checker:**
   ```bash
   bash scripts/check-system-deps.sh
   ```

2. **Install missing dependencies** using your package manager based on the checker output

3. **Run the installer with --skip-system-deps:**
   ```bash
   ./install.sh --skip-system-deps
   ```

4. **Or install from source in a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -e .[whisper]
   ```

## Desktop Environment Compatibility

| Desktop Environment | Status | Notes |
|---------------------|--------|-------|
| GNOME | ✅ Full Support | Primary target, uses AppIndicator |
| KDE Plasma | ✅ Full Support | Works with AppIndicator |
| Xfce | ✅ Full Support | Works with AppIndicator |
| Cinnamon | ✅ Full Support | Works with AppIndicator |
| MATE | ✅ Full Support | Works with AppIndicator |
| LXQt | ✅ Full Support | Works with AppIndicator |
| sway | ✅ Good Support | Wayland native, uses wtype |
| i3 | ✅ Good Support | X11, uses xdotool |
| Hyprland | ⚠️ Experimental | Wayland, may need wtype configuration |

## Display Server

| Display Server | Status | Notes |
|----------------|--------|-------|
| X11 | ✅ Full Support | Uses xdotool for text injection |
| Wayland | ✅ Full Support | Uses wtype (native) or xdotool (XWayland) |
| XWayland | ✅ Full Support | Automatically detected, falls back to xdotool if needed |

## Architecture Support

| Architecture | Status | Notes |
|--------------|--------|-------|
| x86_64 (AMD64) | ✅ Full Support | Primary target |
| arm64 (AArch64) | ✅ Good Support | Tested on Raspberry Pi, ARM64 servers |
| armhf | ⚠️ Experimental | Limited testing |
| riscv64 | ⚠️ Experimental | Limited testing, may need to compile dependencies |

## Reporting Issues

When reporting issues, please include:

1. **Distribution information:**
   ```bash
   cat /etc/os-release
   ```

2. **Desktop environment:**
   ```bash
   echo $XDG_CURRENT_DESKTOP
   echo $SESSION_TYPE
   ```

3. **Dependency checker output:**
   ```bash
   bash scripts/check-system-deps.sh
   ```

4. **Python version:**
   ```bash
   python3 --version
   ```

5. **Error messages or logs:**
   - Any error messages from the installer
   - Output from running `vocalinux-gui` from terminal
   - Relevant journal logs if applicable

6. **Steps to reproduce:**
   - What you were trying to do
   - What happened instead
   - Expected behavior

## Testing Checklist

Use this checklist when testing on a new distribution:

### Pre-Install
- [ ] Run dependency checker: `bash scripts/check-system-deps.sh`
- [ ] Note missing packages
- [ ] Check desktop environment
- [ ] Check display server (X11/Wayland)

### Installation
- [ ] Run installer: `./install.sh`
- [ ] Check for errors during installation
- [ ] Verify virtual environment was created
- [ ] Check wrapper scripts exist

### Post-Install
- [ ] Launch from terminal: `~/.local/bin/vocalinux-gui`
- [ ] Launch from application menu
- [ ] Verify tray icon appears
- [ ] Test keyboard shortcuts (Ctrl+Alt+M by default)
- [ ] Test audio recording
- [ ] Test text injection in different applications
- [ ] Test Settings dialog opens correctly
- [ ] Test model download if using Whisper

### Known Issues to Watch For
- AppIndicator not showing in tray
- Audio device not detected
- Text injection not working
- Model download failures
- Permission errors with udev/input

## Contributing Compatibility Fixes

If you successfully get Vocalinux working on an unsupported or experimental distribution:

1. Test thoroughly using the checklist above
2. Document any distribution-specific requirements
3. Submit a PR with:
   - Distribution detection logic (if needed)
   - Package installation commands
   - Any patches or workarounds required
   - Update to this compatibility document

## See Also

- [Installation Guide](../README.md#installation)
- [Manual Installation](MANUAL_INSTALL.md)
- [Troubleshooting](TROUBLESHOOTING.md)
- [GitHub Issue Tracker](https://github.com/jatinkrmalik/vocalinux/issues)
