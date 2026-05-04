# Linux Distribution Compatibility

## Implementation Status

The cross-distribution compatibility improvements have been implemented in phases:

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 1 | ✅ Complete | Dynamic GI_TYPELIB_PATH detection using pkg-config, multi-arch support, ALSA library fallbacks |
| Phase 2 | ✅ Complete | Enhanced distro detection (Gentoo, Alpine, Void, Solus, Mageia) |
| Phase 3 | ✅ Complete | System dependency checker, improved error messages |
| Phase 4 | ✅ Complete | CI test matrix, pkg-config as core dependency |
| **Phase 5** | ✅ **Complete** | **Fixed remaining hardcoded GI_TYPELIB_PATH values in install.sh and CI workflow** |
| **Phase 6** | ✅ **Complete** | **Added wrapper script verification tests, updated documentation** |
| Phase 7 | 📋 Planned | Flatpak packaging for universal distribution support |
| Phase 8 | 📋 Planned | Snap packaging for Ubuntu Software Store |

## Technical Implementation

### Dynamic GI_TYPELIB_PATH Detection

The installer now uses a robust multi-step approach to detect the correct GI_TYPELIB_PATH across different distributions:

1. **Primary Method**: Uses `pkg-config --variable=typelibdir gobject-introspection-1.0` (most reliable)
2. **Fallback Paths**: Checks common distribution-specific paths in priority order:
   - Ubuntu/Debian multi-arch: `/usr/lib/x86_64-linux-gnu/girepository-1.0`
   - ARM64: `/usr/lib/aarch64-linux-gnu/girepository-1.0`
   - Fedora/RHEL: `/usr/lib64/girepository-1.0`
   - Arch/Generic: `/usr/lib/girepository-1.0`
   - Local installs: `/usr/local/lib/girepository-1.0`

3. **Architecture Support**: Detected paths for x86_64, ARM64, ARMHF, RISC-V, POWER, and s390x

### Wrapper Scripts

The installer creates wrapper scripts (`~/.local/bin/vocalinux` and `~/.local/bin/vocalinux-gui`) that:
- Set the correct `GI_TYPELIB_PATH` environment variable
- Handle input group permissions for Wayland keyboard shortcuts
- Provide seamless cross-distro compatibility

### Desktop Entry

The `.desktop` entry is automatically configured with the detected `GI_TYPELIB_PATH`, ensuring the application launches correctly from the application menu regardless of distribution.

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
PYVER=$(python3 -c 'import sys; print(f"python{sys.version_info.major}{sys.version_info.minor}")')

sudo zypper install -y \
  "${PYVER}-pip" "${PYVER}-gobject" "${PYVER}-gobject-cairo" \
  "${PYVER}-devel" "${PYVER}-virtualenv" \
  gtk3 typelib-1_0-AyatanaAppIndicator3-0_1 libayatana-appindicator3-1 \
  gobject-introspection-devel portaudio-devel pkg-config cmake wget curl unzip \
  xdotool wtype

# Optional: only needed for whisper.cpp Vulkan GPU builds
sudo zypper install -y vulkan-tools vulkan-devel shaderc
```

**Note:** openSUSE Tumbleweed often uses versioned Python package names such as
`python313-devel`. The `-devel` suffix means development headers for compiling
native dependencies; it does **not** mean beta or unstable packages. If
`${PYVER}-virtualenv` is unavailable on your snapshot, try `${PYVER}-venv`.

### Gentoo
```bash
sudo emerge dev-python/pygobject:3 x11-libs/gtk+:3 dev-libs/libappindicator:3 \
  media-libs/portaudio dev-lang/python:3.9
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

## pipx Installation

pipx is a popular tool for installing Python CLI applications in isolated environments. However, **Vocalinux requires system GTK packages** that cannot be installed via pip/pipx.

### Important: Install System Packages First

Before running `pipx install vocalinux`, you **must** install the required system packages:

#### Ubuntu/Debian
```bash
sudo apt install python3-gi gir1.2-gtk-3.0 gir1.2-ayatanaappindicator3-0.1 \
  portaudio19-dev python3-dev pkg-config
```

#### Fedora
```bash
sudo dnf install python3-gobject gtk3 libappindicator-gtk3 \
  portaudio-devel python3-devel pkg-config
```

#### Arch Linux
```bash
sudo pacman -S python-gobject gtk3 libappindicator portaudio pkg-config
```

#### openSUSE
```bash
PYVER=$(python3 -c 'import sys; print(f"python{sys.version_info.major}{sys.version_info.minor}")')

sudo zypper install "${PYVER}-gobject" gtk3 \
  typelib-1_0-AyatanaAppIndicator3-0_1 libayatana-appindicator3-1 \
  portaudio-devel "${PYVER}-devel" pkg-config
```

### pipx Installation Steps

1. **Install system packages** (see above for your distribution)

2. **Install pipx** (if not already installed):
   ```bash
   # Ubuntu/Debian
   sudo apt install pipx
   pipx ensurepath

   # Fedora
   sudo dnf install pipx
   pipx ensurepath

   # Arch Linux
   sudo pacman -S pipx
   pipx ensurepath
   ```

3. **Install Vocalinux**:
   ```bash
   pipx install vocalinux
   ```

4. **Run Vocalinux**:
   ```bash
   vocalinux-gui
   ```

### Why System Packages Are Required

Vocalinux uses GTK3 for its GUI and AppIndicator for the system tray icon. These are system libraries that use GObject Introspection (GI) bindings, which must be installed via your distribution's package manager. The Python packages in pip only provide the Python interface to these libraries - they don't include the actual GTK libraries.

### Troubleshooting pipx Installation

If `vocalinux-gui` fails to start:

1. **Check for missing system packages** - The error message will indicate which packages are missing
2. **Verify GI_TYPELIB_PATH** - In rare cases, you may need to set this environment variable:
   ```bash
   export GI_TYPELIB_PATH=/usr/lib/x86_64-linux-gnu/girepository-1.0
   vocalinux-gui
   ```

### Recommended Alternative

For the best experience with automatic dependency handling, use the official installer:
```bash
curl -fsSL https://raw.githubusercontent.com/jatinkrmalik/vocalinux/main/install.sh | bash
```

This installer automatically detects your distribution and installs all required system packages.

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

### Autostart Compatibility

Vocalinux uses **XDG autostart desktop entries** for "Start on Login".

- Desktop-session autostart file location:
  - `$XDG_CONFIG_HOME/autostart/vocalinux.desktop`, or
  - `~/.config/autostart/vocalinux.desktop` (fallback)
- This launches Vocalinux as a user GUI app after login.
- Vocalinux does **not** create a `systemd` service/unit for this feature.

Practical caveat:

- Mainstream desktop environments generally honor XDG autostart.
- Minimal/custom WM sessions may need an explicit autostart manager or WM startup hook.

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
