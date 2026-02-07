# Cross-Distribution Compatibility Fix Plan

## Overview

This plan breaks down the fixes into **15 specific, actionable tasks** ordered by priority and dependency. Each task can be completed independently.

---

## Phase 1: Critical Path Fixes (Days 1-3)

### Task 1: Fix GI_TYPELIB_PATH Detection (CRITICAL)

**File:** `install.sh` (lines 1082, 1100, 1335)

**Problem:**
```bash
# Current (BROKEN)
export GI_TYPELIB_PATH=/usr/lib/girepository-1.0
```

**Solution:**
```bash
# Add function to detect typelib path dynamically
detect_typelib_path() {
    # Try pkg-config first
    if command -v pkg-config >/dev/null 2>&1; then
        local path=$(pkg-config --variable=typelibdir gobject-introspection-1.0 2>/dev/null)
        if [ -d "$path" ]; then
            echo "$path"
            return 0
        fi
    fi

    # Fallback to common paths
    for path in \
        /usr/lib/x86_64-linux-gnu/girepository-1.0 \
        /usr/lib/aarch64-linux-gnu/girepository-1.0 \
        /usr/lib/arm-linux-gnueabihf/girepository-1.0 \
        /usr/lib64/girepository-1.0 \
        /usr/lib/girepository-1.0 \
        /usr/local/lib/girepository-1.0; do
        if [ -d "$path" ]; then
            echo "$path"
            return 0
        fi
    done

    # Ultimate fallback
    echo "/usr/lib/girepository-1.0"
    return 1
}

# Use it in wrapper scripts
GI_TYPELIB_PATH=$(detect_typelib_path)
export GI_TYPELIB_PATH
```

**Acceptance Criteria:**
- [ ] Function added to `install.sh`
- [ ] Used in all 3 locations (wrapper scripts)
- [ ] Tested on: Ubuntu x86_64, Ubuntu arm64, Fedora
- [ ] Falls back gracefully if path doesn't exist

**Estimated time:** 30 minutes

---

### Task 2: Fix vocalinux.desktop GI_TYPELIB_PATH (CRITICAL)

**File:** `vocalinux.desktop`

**Problem:**
```desktop
# Current (BROKEN)
Exec=env GI_TYPELIB_PATH=/usr/lib/girepository-1.0 ~/.local/bin/vocalinux-gui
```

**Solution:** Remove the hardcoded path - wrapper script already sets it
```desktop
# Fixed
Exec=~/.local/bin/vocalinux-gui
```

**Acceptance Criteria:**
- [ ] Hardcoded GI_TYPELIB_PATH removed from desktop file
- [ ] Desktop entry still works after installation
- [ ] Application launches from application menu

**Estimated time:** 10 minutes

---

### Task 3: Add ALSA Library Fallback (HIGH)

**File:** `src/vocalinux/speech_recognition/recognition_manager.py` (lines 23-50)

**Problem:**
```python
# Current (BROKEN)
asound = ctypes.CDLL("libasound.so.2")
```

**Solution:**
```python
def _setup_alsa_error_handler():
    """Set up an error handler to suppress ALSA warnings."""
    try:
        # Try multiple library name variations
        for lib_name in ['libasound.so.2', 'libasound.so', 'asound']:
            try:
                asound = ctypes.CDLL(lib_name)
                # Define error handler type
                ERROR_HANDLER_FUNC = ctypes.CFUNCTYPE(
                    None, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p,
                    ctypes.c_int, ctypes.c_char_p,
                )
                def _error_handler(filename, line, function, err, fmt):
                    pass
                _alsa_error_handler = ERROR_HANDLER_FUNC(_error_handler)
                asound.snd_lib_error_set_handler(_alsa_error_handler)
                logger.debug(f"ALSA error handler setup using {lib_name}")
                return _alsa_error_handler
            except OSError:
                continue
        logger.debug("ALSA library not found, skipping error handler setup")
        return None
    except Exception:
        return None
```

**Acceptance Criteria:**
- [ ] Tries multiple library names
- [ ] Logs which library was found
- [ ] Doesn't crash if ALSA not available
- [ ] Tested on systems with different ALSA versions

**Estimated time:** 20 minutes

---

### Task 4: Dynamic Model Path Detection (HIGH)

**File:** `src/vocalinux/speech_recognition/recognition_manager.py` (lines 220-225)

**Problem:**
```python
# Current (LIMITED)
SYSTEM_MODELS_DIRS = [
    "/usr/local/share/vocalinux/models",
    "/usr/share/vocalinux/models",
]
```

**Solution:**
```python
def _get_system_model_paths() -> list:
    """Get system-wide model paths based on distro standards."""
    paths = []

    # XDG standard paths
    xdg_data = os.environ.get('XDG_DATA_DIRS', '/usr/local/share:/usr/share')
    for base in xdg_data.split(':'):
        paths.append(os.path.join(base, 'vocalinux', 'models'))

    # Distro-specific paths
    try:
        with open('/etc/os-release', 'r') as f:
            os_release = f.read()
            if any(id in os_release for id in ['fedora', 'rhel', 'centos', 'rocky', 'almalinux']):
                paths.append('/usr/lib64/vocalinux/models')
    except (IOError, OSError):
        pass

    return paths

# Use at module level
SYSTEM_MODELS_DIRS = _get_system_model_paths()
MODELS_DIR = os.path.expanduser("~/.local/share/vocalinux/models")
```

**Acceptance Criteria:**
- [ ] Function created to detect paths dynamically
- [ ] Respects XDG_DATA_DIRS
- [ ] Adds Fedora-specific paths when appropriate
- [ ] Returns list of valid paths

**Estimated time:** 30 minutes

---

### Task 5: Fix Resource Manager Paths (MEDIUM)

**File:** `src/vocalinux/utils/resource_manager.py` (lines 47-61)

**Problem:** Hardcoded fallback paths don't cover all distributions

**Solution:** Enhance the candidates list with more paths:
```python
def _find_resources_dir(self) -> str:
    """Find the resources directory regardless of how the application is executed."""
    module_dir = Path(__file__).parent.absolute()

    # Enhanced list of candidate paths
    candidates = [
        # For direct repository execution
        module_dir.parent.parent.parent / "resources",
        # For installed package (distro-specific)
        Path(sys.prefix) / "share" / "vocalinux" / "resources",
        # Some distros use lib64
        Path("/usr/local/share/vocalinux/resources"),
        Path("/usr/share/vocalinux/resources"),
        Path("/usr/local/lib/vocalinux/resources"),
        Path("/usr/lib/vocalinux/resources"),
        Path("/usr/lib64/vocalinux/resources"),
        # Flatpak
        Path("/app/share/vocalinux/resources"),
    ]

    # Log and return first existing
    for candidate in candidates:
        logger.debug(f"Checking: {candidate} (exists: {candidate.exists()})")
        if candidate.exists():
            logger.info(f"Found resources: {candidate}")
            return str(candidate)

    # Default fallback
    default = str(candidates[0])
    logger.warning(f"Resources not found, using default: {default}")
    return default
```

**Acceptance Criteria:**
- [ ] Additional paths added to candidates
- [ ] lib64 paths included for Fedora/RHEL
- [ ] Flatpak path included
- [ ] Logs all checked paths for debugging

**Estimated time:** 15 minutes

---

## Phase 2: Package Manager Improvements (Days 4-5)

### Task 6: Create Package Mapping File (HIGH)

**New File:** `scripts/distro-package-map.yaml`

**Solution:**
```yaml
# Package name mapping for different distributions
system_packages:
  # GTK3 and PyGObject
  gtk3:
    ubuntu: ["python3-gi", "gir1.2-gtk-3.0", "gir1.2-gdkpixbuf-2.0"]
    debian: ["python3-gi", "gir1.2-gtk-3.0", "gir1.2-gdkpixbuf-2.0"]
    fedora: ["python3-gobject", "gtk3", "gobject-introspection-devel"]
    arch: ["python-gobject", "gtk3"]
    opensuse: ["python3-gobject", "gtk3", "gobject-introspection-devel"]
    gentoo: ["dev-python/pygobject:3", "x11-libs/gtk+:3"]
    alpine: ["py3-gobject3", "gtk+3.0"]

  # AppIndicator / Ayatana AppIndicator
  appindicator:
    ubuntu: ["gir1.2-appindicator3-0.1"]  # Deprecated, fallback to ayatana
    debian_11: ["gir1.2-ayatanaappindicator3-0.1"]
    debian_12_plus: ["gir1.2-ayatanaappindicator3-0.1"]
    fedora: ["libappindicator-gtk3"]
    arch: ["libappindicator-gtk3"]
    opensuse: ["libappindicator-gtk3"]

  # PortAudio
  portaudio:
    ubuntu: ["portaudio19-dev"]
    debian: ["portaudio19-dev"]
    fedora: ["portaudio-devel"]
    arch: ["portaudio"]
    opensuse: ["portaudio-devel"]
    gentoo: ["media-libs/portaudio"]
    alpine: ["portaudio-dev"]

  # Python development
  python_dev:
    ubuntu: ["python3-dev", "python3-venv"]
    debian: ["python3-dev", "python3-venv"]
    fedora: ["python3-devel", "python3-virtualenv"]
    arch: ["python"]
    opensuse: ["python3-devel", "python3-virtualenv"]

  # Text injection tools
  xdotool:
    ubuntu: ["xdotool"]
    debian: ["xdotool"]
    fedora: ["xdotool"]
    arch: ["xdotool"]
    opensuse: ["xdotool"]

  wtype:
    ubuntu: ["wtype"]
    debian: ["wtype"]
    fedora: ["wtype"]
    arch: ["wtype"]
    opensuse: ["wtype"]

  ydotool:
    ubuntu: ["ydotool"]
    debian: ["ydotool"]
    fedora: ["ydotool"]
    arch: ["ydotool"]
    opensuse: ["ydotool"]

# Command to install packages for each package manager
install_commands:
  apt: "sudo apt install -y {packages}"
  dnf: "sudo dnf install -y {packages}"
  yum: "sudo yum install -y {packages}"
  pacman: "sudo pacman -S --noconfirm {packages}"
  zypper: "sudo zypper install -y {packages}"
  emerge: "sudo emerge {packages}"
  apk: "sudo apk add {packages}"
  xbps: "sudo xbps-install -y {packages}"
  eopkg: "sudo eopkg install -y {packages}"
```

**Acceptance Criteria:**
- [ ] YAML file created
- [ ] All current packages mapped
- [ ] At least 8 distros covered
- [ ] Install commands defined

**Estimated time:** 45 minutes

---

### Task 7: Enhanced Distro Detection (HIGH)

**File:** `install.sh` (modify `detect_distro()` function, lines 190-217)

**Current:** Only handles ubuntu, debian, fedora, arch, suse

**Solution:** Add more distros:
```bash
detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        DISTRO_NAME="$NAME"
        DISTRO_ID="$ID"
        DISTRO_VERSION="$VERSION_ID"
        DISTRO_FAMILY="unknown"

        # Determine distribution family
        if [[ "$ID" == "ubuntu" || "$ID_LIKE" == *"ubuntu"* || "$ID" == "pop" || "$ID" == "linuxmint" || "$ID" == "elementary" || "$ID" == "zorin" ]]; then
            DISTRO_FAMILY="ubuntu"
        elif [[ "$ID" == "debian" || "$ID_LIKE" == *"debian"* ]]; then
            DISTRO_FAMILY="debian"
        elif [[ "$ID" == "fedora" || "$ID_LIKE" == *"fedora"* || "$ID" == "rhel" || "$ID" == "centos" || "$ID" == "rocky" || "$ID" == "almalinux" ]]; then
            DISTRO_FAMILY="fedora"
        elif [[ "$ID" == "arch" || "$ID_LIKE" == *"arch"* || "$ID" == "manjaro" || "$ID" == "endeavouros" ]]; then
            DISTRO_FAMILY="arch"
        elif [[ "$ID" == "opensuse" || "$ID_LIKE" == *"suse"* ]]; then
            DISTRO_FAMILY="suse"
        elif [[ "$ID" == "gentoo" ]]; then
            DISTRO_FAMILY="gentoo"
        elif [[ "$ID" == "alpine" ]]; then
            DISTRO_FAMILY="alpine"
        elif [[ "$ID" == "void" ]]; then
            DISTRO_FAMILY="void"
        elif [[ "$ID" == "solus" ]]; then
            DISTRO_FAMILY="solus"
        elif [[ "$ID" == "mageia" ]]; then
            DISTRO_FAMILY="mageia"
        else
            DISTRO_FAMILY="unknown"
        fi

        print_info "Detected: $DISTRO_NAME $DISTRO_VERSION ($DISTRO_FAMILY family)"
        return 0
    else
        print_error "Could not detect Linux distribution (missing /etc/os-release)"
        return 1
    fi
}
```

**Acceptance Criteria:**
- [ ] Gentoo detection added
- [ ] Alpine detection added
- [ ] Void detection added
- [ ] Solus detection added
- [ ] Mageia detection added
- [ ] Unknown distro fallback still works

**Estimated time:** 20 minutes

---

### Task 8: Add Package Manager Support for New Distros (HIGH)

**File:** `install.sh` (modify `install_system_dependencies()`, lines 463-606)

**Add to case statement:**
```bash
gentoo)
    print_info "Gentoo detected. Installing dependencies..."
    print_warning "Gentoo uses emerge. This may take longer as packages are compiled."

    # Check for required packages
    MISSING_PACKAGES=""
    for pkg in dev-python/pygobject x11-libs/gtk+:3 dev-libs/libappindicator:3 media-libs/portaudio; do
        if ! emerge --list-files "$pkg" >/dev/null 2>&1; then
            MISSING_PACKAGES="$MISSING_PACKAGES $pkg"
        fi
    done

    if [ -n "$MISSING_PACKAGES" ]; then
        print_info "Installing packages:$MISSING_PACKAGES"
        sudo emerge $MISSING_PACKAGES || { print_error "Failed to install dependencies"; exit 1; }
    fi
    ;;

alpine)
    print_info "Alpine Linux detected."
    print_warning "Alpine uses musl libc. Some Python packages may not have pre-built wheels."

    for pkg in py3-gobject3 gtk+3.0 py3-pip portaudio-dev; do
        if ! apk info -e "$pkg" >/dev/null 2>&1; then
            MISSING_PACKAGES="$MISSING_PACKAGES $pkg"
        fi
    done

    if [ -n "$MISSING_PACKAGES" ]; then
        sudo apk add $MISSING_PACKAGES || { print_error "Failed to install dependencies"; exit 1; }
    fi
    ;;

void)
    print_info "Void Linux detected."

    for pkg in python3-gobject gtk+3 python3-pip portaudio-devel; do
        if ! xbps-query -S "$pkg" >/dev/null 2>&1; then
            MISSING_PACKAGES="$MISSING_PACKAGES $pkg"
        fi
    done

    if [ -n "$MISSING_PACKAGES" ]; then
        sudo xbps-install -Sy $MISSING_PACKAGES || { print_error "Failed to install dependencies"; exit 1; }
    fi
    ;;

solus)
    print_info "Solus detected."

    for pkg in python3-gobject gtk3 python3-pip portaudio-devel; do
        if ! eopkg info "$pkg" >/dev/null 2>&1; then
            MISSING_PACKAGES="$MISSING_PACKAGES $pkg"
        fi
    done

    if [ -n "$MISSING_PACKAGES" ]; then
        sudo eopkg install $MISSING_PACKAGES || { print_error "Failed to install dependencies"; exit 1; }
    fi
    ;;

*)
    print_error "Unsupported distribution family: $DISTRO_FAMILY"
    print_info "Please install dependencies manually:"
    print_info "- Python 3.8+, pip, venv"
    print_info "- PyGObject (GTK3 bindings)"
    print_info "- PortAudio development libraries"
    print_info "- xdotool (X11) or wtype/ydotool (Wayland)"
    ;;
```

**Acceptance Criteria:**
- [ ] Gentoo (emerge) support added
- [ ] Alpine (apk) support added
- [ ] Void (xbps) support added
- [ ] Solus (eopkg) support added
- [ ] Clear error message for truly unsupported distros

**Estimated time:** 1 hour

---

## Phase 3: Better Error Handling & Docs (Day 6)

### Task 9: Create System Dependency Checker (MEDIUM)

**New File:** `scripts/check-system-deps.sh`

**Solution:**
```bash
#!/bin/bash
# Check for system dependencies regardless of distro
# Returns helpful error messages with install commands

check_deps() {
    MISSING=0
    WARNINGS=0

    echo "Checking Vocalinux system dependencies..."
    echo ""

    # Check for Python 3.8+
    if command -v python3 >/dev/null 2>&1; then
        PY_VERSION=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
        echo "✓ Python $PY_VERSION"

        if [ "$(echo "$PY_VERSION" | cut -d. -f1)" -lt 3 ] || \
           [ "$(echo "$PY_VERSION" | cut -d. -f2)" -lt 8 ]; then
            echo "  ✗ Python 3.8+ required, found $PY_VERSION"
            MISSING=1
        fi
    else
        echo "✗ Python 3 not found"
        MISSING=1
    fi

    # Check for pkg-config
    if command -v pkg-config >/dev/null 2>&1; then
        echo "✓ pkg-config"
    else
        echo "✗ pkg-config not found"
        MISSING=1
    fi

    # Check for GTK3
    if pkg-config --exists gtk+-3.0 2>/dev/null; then
        GTK_VERSION=$(pkg-config --modversion gtk+-3.0)
        echo "✓ GTK3 $GTK_VERSION"
    else
        echo "✗ GTK3 development files not found"
        MISSING=1
    fi

    # Check for PyGObject
    if pkg-config --exists gobject-introspection-1.0 2>/dev/null; then
        echo "✓ GObject Introspection"
        GI_TYPELIB_PATH=$(pkg-config --variable=typelibdir gobject-introspection-1.0 2>/dev/null)
        echo "  Typelib path: $GI_TYPELIB_PATH"
    else
        echo "✗ GObject Introspection not found"
        MISSING=1
    fi

    # Check for PortAudio
    if pkg-config --exists portaudio-2.0 2>/dev/null; then
        echo "✓ PortAudio"
    else
        echo "⚠ PortAudio development files not found (required for audio)"
        MISSING=1
    fi

    # Check for text injection tools
    echo ""
    echo "Text injection tools (at least one required):"

    if command -v xdotool >/dev/null 2>&1; then
        echo "✓ xdotool (X11)"
    else
        echo "  xdotool not found (X11)"
    fi

    if command -v wtype >/dev/null 2>&1; then
        echo "✓ wtype (Wayland)"
    else
        echo "  wtype not found (Wayland)"
    fi

    if command -v ydotool >/dev/null 2>&1; then
        echo "✓ ydotool (Wayland universal)"
    else
        echo "  ydotool not found (Wayland)"
    fi

    # Summary
    echo ""
    echo "=" "=" "=" "=" "="
    if [ $MISSING -eq 0 ]; then
        echo "✓ All critical dependencies found!"
        return 0
    else
        echo "✗ Some dependencies are missing"
        echo ""
        echo "Install based on your distribution:"
        echo ""
        echo "Ubuntu/Debian:"
        echo "  sudo apt install python3-gi gir1.2-gtk-3.0 portaudio19-dev python3-dev pkg-config"
        echo ""
        echo "Fedora/RHEL:"
        echo "  sudo dnf install python3-gobject gtk3-devel portaudio-devel python3-devel pkg-config"
        echo ""
        echo "Arch:"
        echo "  sudo pacman -S python-gobject gtk3 portaudio python pkg-config"
        return 1
    fi
}

check_deps
```

**Acceptance Criteria:**
- [ ] Script created and executable
- [ ] Checks all critical dependencies
- [ ] Provides distro-specific install commands
- [ ] Returns proper exit codes
- [ ] Can be run standalone

**Estimated time:** 45 minutes

---

### Task 10: Better Unsupported Distro Message (MEDIUM)

**File:** `install.sh` (around line 590)

**Solution:**
```bash
*)
    print_error "Unsupported distribution family: $DISTRO_FAMILY"
    print_info ""
    print_info "Your distribution ($DISTRO_NAME) is not officially supported."
    print_info "However, you can still install Vocalinux manually:"
    print_info ""
    print_info "1. Run the dependency checker:"
    print_info "   bash scripts/check-system-deps.sh"
    print_info ""
    print_info "2. Install missing dependencies using your package manager"
    print_info ""
    print_info "3. Run the installer with --skip-system-deps:"
    print_info "   ./install.sh --skip-system-deps"
    print_info ""
    print_info "4. Or install from source in a virtual environment:"
    print_info "   python3 -m venv venv"
    print_info "   source venv/bin/activate"
    print_info "   pip install -e .[whisper]"
    print_info ""
    print_info "For manual installation instructions, see:"
    print_info "  https://github.com/jatinkrmalik/vocalinux/wiki/Manual-Installation"
    print_info ""
    if [[ "$NON_INTERACTIVE" != "yes" ]]; then
        read -p "Continue anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    ;;
```

**Acceptance Criteria:**
- [ ] Clear message for unsupported distros
- [ ] References dependency checker script
- [ ] Provides manual installation option
- [ ] Includes link to wiki/docs

**Estimated time:** 15 minutes

---

### Task 11: Create Distro Compatibility Documentation (MEDIUM)

**New File:** `docs/DISTRO_COMPATIBILITY.md`

**Template:**
```markdown
# Linux Distribution Compatibility

## Officially Supported Distributions

These distributions are tested and known to work well:

| Distribution | Version | Status | Notes |
|--------------|---------|--------|-------|
| Ubuntu | 22.04+ | ✅ Full Support | Primary target |
| Debian | 11+, Testing | ✅ Full Support | Well tested |
| Fedora | 39+ | ✅ Good Support | Minor issues |
| Arch Linux | Rolling | ✅ Good Support | Community tested |
| openSUSE | Tumbleweed | ⚠️ Partial | Some issues known |

## Experimental Support

These distributions may work but have known limitations:

| Distribution | Status | Known Issues |
|--------------|--------|--------------|
| Gentoo | ⚠️ Experimental | No package manager support, manual install required |
| Alpine | ⚠️ Experimental | musl libc issues, no pre-built wheels |
| Void Linux | ⚠️ Experimental | Untested, manual install required |
| Solus | ⚠️ Experimental | Untested, manual install required |
| NixOS | ❌ Not Supported | Incompatible filesystem layout |

## Manual Installation

For unsupported or experimental distributions, see [Manual Installation Guide](MANUAL_INSTALL.md).

## Reporting Issues

When reporting issues, please include:
- Distribution name and version
- Desktop environment
- Output of `bash scripts/check-system-deps.sh`
...
```

**Acceptance Criteria:**
- [ ] Documentation created
- [ ] Compatibility matrix included
- [ ] Known issues documented
- [ ] Link to manual install guide

**Estimated time:** 30 minutes

---

## Phase 4: Testing & Polish (Day 7)

### Task 12: Add pkg-config to Core Dependencies (LOW)

**File:** `install.sh`, `pyproject.toml`, `setup.py`

**Solution:** Add pkg-config as a system dependency requirement

**Acceptance Criteria:**
- [ ] pkg-config added to dependency list
- [ ] Error message if pkg-config missing
- [ ] Documentation updated

**Estimated time:** 10 minutes

---

### Task 13: Update README with Distro Info (LOW)

**File:** `README.md` (lines 210-216)

**Add to Requirements section:**
```markdown
## Requirements

- **OS**: Linux (tested on Ubuntu 22.04+, Debian 11+, Fedora 39+, Arch Linux)
- **Python**: 3.8 or newer
- **Display**: X11 or Wayland
- **Hardware**: Microphone for voice input

**Note:** See [DISTRO_COMPATIBILITY.md](docs/DISTRO_COMPATIBILITY.md) for distribution-specific information.
```

**Acceptance Criteria:**
- [ ] README updated with tested distros
- [ ] Link to compatibility docs
- [ ] Accurate information

**Estimated time:** 10 minutes

---

### Task 14: Create Test Matrix for CI (MEDIUM)

**File:** `.github/workflows/test-matrix.yml`

**Add multi-distro testing:**
```yaml
name: Distro Test Matrix

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        container:
          - ubuntu:22.04
          - ubuntu:24.04
          - debian:12
          - fedora:39
          - archlinux:latest
    container:
      image: ${{ matrix.container }}

    steps:
      - uses: actions/checkout@v3
      - name: Run dependency checker
        run: bash scripts/check-system-deps.sh
      - name: Test import
        run: python3 -c "import sys; sys.path.insert(0, 'src'); from vocalinux import main"
```

**Acceptance Criteria:**
- [ ] CI workflow created
- [ ] Tests on multiple containers
- [ ] Runs dependency checker
- [ ] Tests basic import

**Estimated time:** 30 minutes

---

### Task 15: Integration Testing Checklist (LOW)

**Create:** `tests/distro-checklist.md`

```markdown
# Distro Testing Checklist

Use this checklist when testing on a new distribution.

## Pre-Install
- [ ] Run dependency checker
- [ ] Note missing packages
- [ ] Check desktop environment

## Installation
- [ ] Run installer
- [ ] Check for errors
- [ ] Verify venv created
- [ ] Check wrapper scripts

## Post-Install
- [ ] Launch from terminal
- [ ] Launch from application menu
- [ ] Test tray icon appears
- [ ] Test keyboard shortcuts
- [ ] Test audio recording
- [ ] Test text injection
- [ ] Test Settings dialog

## Known Issues
(Record any issues found)
```

**Acceptance Criteria:**
- [ ] Checklist created
- [ ] Covers all major features
- [ ] Can be used for testing

**Estimated time:** 15 minutes

---

## Implementation Order

**Week 1:**
1. Task 1: GI_TYPELIB_PATH (30 min)
2. Task 2: Desktop file (10 min)
3. Task 3: ALSA fallback (20 min)
4. Task 4: Model paths (30 min)
5. Task 5: Resource paths (15 min)

**Week 2:**
6. Task 6: Package mapping (45 min)
7. Task 7: Distro detection (20 min)
8. Task 8: New package managers (1 hour)

**Week 3:**
9. Task 9: Dep checker (45 min)
10. Task 10: Error messages (15 min)
11. Task 11: Documentation (30 min)
12. Task 12: pkg-config dep (10 min)
13. Task 13: README update (10 min)
14. Task 14: CI matrix (30 min)
15. Task 15: Test checklist (15 min)

**Total estimated time: ~8-10 hours of work**

---

## Tracking

- [ ] Task 1: GI_TYPELIB_PATH detection
- [ ] Task 2: Fix desktop file
- [ ] Task 3: ALSA library fallback
- [ ] Task 4: Dynamic model paths
- [ ] Task 5: Resource manager paths
- [ ] Task 6: Package mapping YAML
- [ ] Task 7: Enhanced distro detection
- [ ] Task 8: New package manager support
- [ ] Task 9: System dependency checker
- [ ] Task 10: Better error messages
- [ ] Task 11: Distro compatibility docs
- [ ] Task 12: pkg-config dependency
- [ ] Task 13: README updates
- [ ] Task 14: CI test matrix
- [ ] Task 15: Testing checklist
