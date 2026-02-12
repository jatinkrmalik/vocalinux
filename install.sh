#!/bin/bash
# Vocalinux Installer
# This script installs the Vocalinux application and its dependencies

set -e  # Exit on error

# Function to display colored output
print_info() {
    echo -e "\e[1;34m[INFO]\e[0m $1"
}

print_success() {
    echo -e "\e[1;32m[SUCCESS]\e[0m $1"
}

print_error() {
    echo -e "\e[1;31m[ERROR]\e[0m $1"
}

print_warning() {
    echo -e "\e[1;33m[WARNING]\e[0m $1"
}

# Parse command line arguments
INSTALL_MODE="user"
RUN_TESTS="no"
DEV_MODE="no"
VENV_DIR="venv"
SKIP_MODELS="no"
WITH_WHISPER="no"
WHISPER_CPU="no"
NO_WHISPER_EXPLICIT="no"
NON_INTERACTIVE="no"
INTERACTIVE_MODE="yes"  # Default to interactive mode
AUTO_MODE="no"
HAS_NVIDIA_GPU="unknown"
GPU_NAME=""
GPU_MEMORY=""
HAS_VULKAN="no"
VULKAN_DEVICE=""

# Detect if running non-interactively (e.g., via curl | bash)
# Interactive mode is now default, so only auto-detect non-interactive for curl pipes
if [ ! -t 0 ]; then
    # When piped via curl, we'll still try to be interactive if possible
    # User can force non-interactive with --auto
    INTERACTIVE_MODE="ask"
fi

while [[ $# -gt 0 ]]; do
    case $1 in
        --dev)
            DEV_MODE="yes"
            shift
            ;;
        --test)
            RUN_TESTS="yes"
            shift
            ;;
        --venv-dir=*)
            VENV_DIR="${1#*=}"
            shift
            ;;
        --skip-models)
            SKIP_MODELS="yes"
            shift
            ;;
        --engine=*)
            SELECTED_ENGINE="${1#*=}"
            shift
            ;;
        --interactive|-i)
            INTERACTIVE_MODE="yes"
            shift
            ;;
        --tag=*)
            INSTALL_TAG="${1#*=}"
            shift
            ;;
        --auto)
            AUTO_MODE="yes"
            INTERACTIVE_MODE="no"
            NON_INTERACTIVE="yes"
            shift
            ;;
        --help)
            echo "Vocalinux Installer"
            echo ""
            echo "Usage: $0 [options]"
            echo ""
            echo "Installation Modes:"
            echo "  (no flags)       Interactive mode - guided setup with recommendations"
            echo "  --auto           Automatic mode - install with defaults (whisper.cpp)"
            echo "  --auto --engine=whisper   Auto mode with specific engine"
            echo ""
            echo "Options:"
            echo "  --interactive, -i  Force interactive mode (default)"
            echo "  --auto           Non-interactive automatic installation"
            echo "  --engine=NAME    Speech engine: whisper_cpp (default), whisper, vosk"
            echo "  --dev            Install in development mode with all dev dependencies"
            echo "  --test           Run tests after installation"
            echo "  --venv-dir=PATH  Specify custom virtual environment directory"
            echo "  --skip-models    Skip downloading speech models during installation"
            echo "  --tag=TAG        Install specific release tag (default: v0.4.1-alpha)"
            echo "  --help           Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                           # Interactive mode (recommended)"
            echo "  $0 --auto                    # Auto-install with whisper.cpp"
            echo "  $0 --auto --engine=vosk      # Auto-install VOSK only"
            echo "  $0 --dev --test              # Dev mode with tests"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help to see available options"
            exit 1
            ;;
    esac
done

# If dev mode is enabled, automatically run tests
if [[ "$DEV_MODE" == "yes" ]]; then
    RUN_TESTS="yes"
fi

# Display ASCII art banner
cat << "EOF"

  ▗▖  ▗▖ ▗▄▖  ▗▄▄▖ ▗▄▖ ▗▖   ▗▄▄▄▖▗▖  ▗▖▗▖ ▗▖▗▖  ▗▖
  ▐▌  ▐▌▐▌ ▐▌▐▌   ▐▌ ▐▌▐▌     █  ▐▛▚▖▐▌▐▌ ▐▌ ▝▚▞▘
  ▐▌  ▐▌▐▌ ▐▌▐▌   ▐▛▀▜▌▐▌     █  ▐▌ ▝▜▌▐▌ ▐▌  ▐▌
   ▝▚▞▘ ▝▚▄▞▘▝▚▄▄▖▐▌ ▐▌▐▙▄▄▖▗▄█▄▖▐▌  ▐▌▝▚▄▞▘▗▞▘▝▚▖

                    Voice Dictation for Linux

EOF

print_info "Vocalinux Installer"
print_info "=============================="
echo ""

# Default to installing from latest stable release instead of main branch
INSTALL_TAG="${INSTALL_TAG:-v0.4.1-alpha}"

# Check if running from within the vocalinux repo or remotely (via curl)
REPO_URL="https://github.com/jatinkrmalik/vocalinux.git"
INSTALL_DIR=""
CLEANUP_ON_EXIT="no"

if [ -f "setup.py" ] || [ -f "pyproject.toml" ]; then
    # Running from within the repo
    INSTALL_DIR="$(pwd)"
    print_info "Running from local repository: $INSTALL_DIR"
    # Convert VENV_DIR to absolute path for wrapper scripts
    VENV_DIR="$INSTALL_DIR/$VENV_DIR"
else
    # Running remotely (e.g., via curl | bash)
    print_info "Installing Vocalinux version: ${INSTALL_TAG}"
    INSTALL_DIR="$HOME/.local/share/vocalinux-install"
    mkdir -p "$INSTALL_DIR"

    if [ -d "$INSTALL_DIR/.git" ]; then
        print_info "Updating existing clone..."
        cd "$INSTALL_DIR"
        git fetch origin "tag" "$INSTALL_TAG"
        git reset --hard "$INSTALL_TAG"
    else
        rm -rf "$INSTALL_DIR"
        git clone --depth 1 --branch "$INSTALL_TAG" "$REPO_URL" "$INSTALL_DIR" || {
            print_error "Failed to clone Vocalinux repository"
            exit 1
        }
        cd "$INSTALL_DIR"
    fi
    CLEANUP_ON_EXIT="yes"
    print_info "Repository cloned to: $INSTALL_DIR"

    # When running remotely, install venv to user's home directory
    VENV_DIR="$HOME/.local/share/vocalinux/venv"
fi

# Change to install directory
cd "$INSTALL_DIR"

print_info "Using virtual environment: $VENV_DIR"
[[ "$DEV_MODE" == "yes" ]] && print_info "Installing in development mode"
[[ "$RUN_TESTS" == "yes" ]] && print_info "Tests will be run after installation"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_error "Please do not run this script as root or with sudo."
    exit 1
fi

# Detect Linux distribution and version
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
        fi

        print_info "Detected: $DISTRO_NAME $DISTRO_VERSION ($DISTRO_FAMILY family)"
        return 0
    else
        print_error "Could not detect Linux distribution (missing /etc/os-release)"
        return 1
    fi
}

# Check minimum required version for Ubuntu-based systems
check_ubuntu_version() {
    local MIN_VERSION="18.04"
    if [[ "$DISTRO_FAMILY" == "ubuntu" ]]; then
        if [[ $(echo -e "$DISTRO_VERSION\n$MIN_VERSION" | sort -V | head -n1) == "$MIN_VERSION" || "$DISTRO_VERSION" == "$MIN_VERSION" ]]; then
            return 0
        else
            print_error "This application requires Ubuntu $MIN_VERSION or newer. Detected: $DISTRO_VERSION"
            return 1
        fi
    fi
    return 0
}

# Detect NVIDIA GPU presence
detect_nvidia_gpu() {
    # Check if nvidia-smi command exists and can successfully query GPU
    if command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi >/dev/null 2>&1; then
        # Extract GPU information for user feedback
        GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -n1)
        GPU_MEMORY=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader 2>/dev/null | head -n1)
        HAS_NVIDIA_GPU="yes"
        return 0
    else
        HAS_NVIDIA_GPU="no"
        return 1
    fi
}

# Detect Vulkan support for whisper.cpp
detect_vulkan() {
    # Check for vulkaninfo command
    if command -v vulkaninfo >/dev/null 2>&1; then
        local vulkan_output=$(vulkaninfo --summary 2>/dev/null | head -20)
        if [ -n "$vulkan_output" ]; then
            HAS_VULKAN="yes"
            # Try to extract GPU name
            VULKAN_DEVICE=$(echo "$vulkan_output" | grep -i "deviceName" | head -1 | cut -d'=' -f2 | xargs)
            if [ -z "$VULKAN_DEVICE" ]; then
                VULKAN_DEVICE="Vulkan-compatible GPU"
            fi
            return 0
        fi
    fi
    HAS_VULKAN="no"
    return 1
}

# Detect hardware and recommend best engine
get_engine_recommendation() {
    detect_nvidia_gpu || true
    detect_vulkan || true
    
    # Get RAM info
    local TOTAL_RAM_GB=$(free -g 2>/dev/null | awk '/^Mem:/{print $2}' || echo "0")
    
    if [[ "$HAS_NVIDIA_GPU" == "yes" ]]; then
        # NVIDIA GPU detected - whisper.cpp can use CUDA
        echo "whisper_cpp:✓:NVIDIA GPU detected ($GPU_NAME) - Best performance with whisper.cpp"
    elif [[ "$HAS_VULKAN" == "yes" ]]; then
        # Non-NVIDIA GPU with Vulkan support
        echo "whisper_cpp:✓:$VULKAN_DEVICE detected - Great performance with whisper.cpp Vulkan"
    elif [ "$TOTAL_RAM_GB" -ge 8 ]; then
        # No GPU but decent RAM
        echo "whisper_cpp:✓:No GPU detected, but ${TOTAL_RAM_GB}GB RAM - whisper.cpp CPU mode"
    else
        # Low RAM, no GPU
        echo "vosk:⚠:Low RAM (${TOTAL_RAM_GB}GB) and no GPU - VOSK recommended for best performance"
    fi
}

# Detect GI_TYPELIB_PATH for cross-distro compatibility
detect_typelib_path() {
    # Try pkg-config first (most reliable)
    if command -v pkg-config >/dev/null 2>&1; then
        local path=$(pkg-config --variable=typelibdir gobject-introspection-1.0 2>/dev/null)
        if [ -n "$path" ] && [ -d "$path" ]; then
            echo "$path"
            return 0
        fi
    fi

    # Fallback to common distribution-specific paths
    # Order matters: more specific paths first
    for path in \
        /usr/lib/x86_64-linux-gnu/girepository-1.0 \
        /usr/lib/aarch64-linux-gnu/girepository-1.0 \
        /usr/lib/arm-linux-gnueabihf/girepository-1.0 \
        /usr/lib/riscv64-linux-gnu/girepository-1.0 \
        /usr/lib/powerpc64le-linux-gnu/girepository-1.0 \
        /usr/lib/s390x-linux-gnu/girepository-1.0 \
        /usr/lib64/girepository-1.0 \
        /usr/lib/girepository-1.0 \
        /usr/local/lib/girepository-1.0 \
        /usr/local/lib64/girepository-1.0; do
        if [ -d "$path" ]; then
            echo "$path"
            return 0
        fi
    done

    # Ultimate fallback - will cause issues if wrong, but at least we try
    echo "/usr/lib/girepository-1.0"
    return 1
}

# Print section header for interactive mode
clear_screen() {
    if [ -t 1 ] && command -v clear >/dev/null 2>&1 && [ -n "${TERM:-}" ]; then
        clear >/dev/null 2>&1 || true
    fi
}

print_header() {
    local title="$1"
    echo ""
    echo "============================================================"
    echo "  $title"
    echo "============================================================"
}

# Function to run interactive guided installation
run_interactive_install() {
    clear_screen
    cat << "EOF"

                 Interactive Installation Guide
                 ===============================

EOF

    echo "Welcome! This guided installation will help you set up Vocalinux"
    echo "with the best options for your system."
    echo ""
    echo "All speech engines are 100% offline, local, and private."
    echo "Your voice data never leaves your computer."
    echo ""

    # Step 1: Detect and display system info
    print_header "Step 1: Your System"
    echo "Detected: $DISTRO_NAME $DISTRO_VERSION"
    
    # Get hardware recommendation
    local RECOMMENDATION=$(get_engine_recommendation)
    local RECOMMENDED_ENGINE=$(echo "$RECOMMENDATION" | cut -d':' -f1)
    local RECOMMENDED_ICON=$(echo "$RECOMMENDATION" | cut -d':' -f2)
    local RECOMMENDED_REASON=$(echo "$RECOMMENDATION" | cut -d':' -f3-)
    
    echo "Hardware: $RECOMMENDED_REASON"
    echo ""

    # Step 2: Choose speech recognition engine
    print_header "Step 2: Choose Speech Recognition Engine"
    echo ""
    echo "  ┌─────────────────────────────────────────────────────────────┐"
    echo "  │  1. WHISPER.CPP  ★ RECOMMENDED                              │"
    echo "  │     • Fastest, most accurate, works with any GPU            │"
    echo "  │     • Supports NVIDIA (CUDA), AMD, Intel (Vulkan)           │"
    echo "  │     • CPU-only mode available for older systems             │"
    echo "  │     • Models: tiny (39MB) to large (1.5GB)                  │"
    echo "  │     • 99+ languages with auto-detection                     │"
    echo "  └─────────────────────────────────────────────────────────────┘"
    echo ""
    echo "  ┌─────────────────────────────────────────────────────────────┐"
    echo "  │  2. WHISPER (OpenAI)                                        │"
    echo "  │     • PyTorch-based, high accuracy                          │"
    echo "  │     • Only supports NVIDIA GPUs (CUDA)                      │"
    echo "  │     • Larger download (~2GB with CUDA)                      │"
    echo "  │     • Good for development/research                         │"
    echo "  └─────────────────────────────────────────────────────────────┘"
    echo ""
    echo "  ┌─────────────────────────────────────────────────────────────┐"
    echo "  │  3. VOSK                                                    │"
    echo "  │     • Lightweight and fast                                  │"
    echo "  │     • Works on older/low-RAM systems                        │"
    echo "  │     • ~40MB download                                        │"
    echo "  │     • Good for basic dictation needs                        │"
    echo "  └─────────────────────────────────────────────────────────────┘"
    echo ""
    
    # Show recommendation
    case "$RECOMMENDED_ENGINE" in
        whisper_cpp)
            echo "  → Recommendation: whisper.cpp (best performance for your hardware)"
            DEFAULT_CHOICE="1"
            ;;
        vosk)
            echo "  → Recommendation: VOSK (lightweight option for your system)"
            DEFAULT_CHOICE="3"
            ;;
        *)
            echo "  → Recommendation: whisper.cpp (best overall experience)"
            DEFAULT_CHOICE="1"
            ;;
    esac
    echo ""

    read -p "Choose engine [1-3] (default: $DEFAULT_CHOICE): " ENGINE_CHOICE
    ENGINE_CHOICE=${ENGINE_CHOICE:-$DEFAULT_CHOICE}

    case "$ENGINE_CHOICE" in
        1)
            SELECTED_ENGINE="whisper_cpp"
            ENGINE_DISPLAY="Whisper.cpp (Recommended)"
            ;;
        2)
            SELECTED_ENGINE="whisper"
            ENGINE_DISPLAY="Whisper (OpenAI)"
            ;;
        3)
            SELECTED_ENGINE="vosk"
            ENGINE_DISPLAY="VOSK (Lightweight)"
            ;;
        *)
            SELECTED_ENGINE="whisper_cpp"
            ENGINE_DISPLAY="Whisper.cpp (Recommended)"
            ;;
    esac

    # Step 3: Model download preference
    print_header "Step 3: Model Download"
    echo ""
    echo "Speech recognition models can be downloaded now or later."
    echo ""
    echo "  1. Download now (recommended)"
    echo "     • Faster first run - ready to use immediately"
    echo "     • Offline capable right after install"
    echo ""
    echo "  2. Download later"
    echo "     • Smaller initial install"
    echo "     • Models download automatically on first use"
    echo ""

    read -p "Download models now? [1-2] (default: 1): " MODELS_CHOICE
    MODELS_CHOICE=${MODELS_CHOICE:-1}

    if [[ "$MODELS_CHOICE" == "2" ]]; then
        SKIP_MODELS="yes"
        MODELS_DISPLAY="Download on first use"
    else
        MODELS_DISPLAY="Download now (recommended)"
    fi

    # Summary
    print_header "Installation Summary"
    echo ""
    echo "  Speech Engine: $ENGINE_DISPLAY"
    echo "  Models: $MODELS_DISPLAY"
    echo "  Install Location: ${INSTALL_DIR:-\$HOME/.local/share/vocalinux}"
    echo ""
    read -p "Press Enter to continue with installation, or Ctrl+C to cancel..."
    echo ""
}

# Detect distribution
detect_distro

# Check compatibility
if [[ "$DISTRO_FAMILY" != "ubuntu" ]]; then
    print_warning "This installer is primarily designed for Ubuntu-based systems. Your system: $DISTRO_NAME"
    print_warning "The application may still work, but you might need to install dependencies manually."
    if [[ "$NON_INTERACTIVE" == "yes" ]]; then
        print_info "Non-interactive mode: continuing anyway..."
    else
        read -p "Do you want to continue anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
else
    # Check version for Ubuntu-based systems
    if ! check_ubuntu_version; then
        if [[ "$NON_INTERACTIVE" == "yes" ]]; then
            print_info "Non-interactive mode: continuing anyway..."
        else
            read -p "Do you want to continue anyway? (y/n) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
    fi
fi

# Handle installation mode selection
if [[ "$INTERACTIVE_MODE" == "ask" ]]; then
    # Running via curl pipe but we have a terminal - ask user preference
    echo ""
    echo "Installation Mode:"
    echo "  1. Interactive (recommended) - guided setup with recommendations"
    echo "  2. Automatic - quick install with defaults (whisper.cpp)"
    echo ""
    read -p "Choose mode [1-2] (default: 1): " MODE_CHOICE
    MODE_CHOICE=${MODE_CHOICE:-1}
    
    if [[ "$MODE_CHOICE" == "2" ]]; then
        AUTO_MODE="yes"
        INTERACTIVE_MODE="no"
        NON_INTERACTIVE="yes"
    else
        INTERACTIVE_MODE="yes"
        NON_INTERACTIVE="no"
    fi
    echo ""
fi

# Run interactive installation if selected
if [[ "$INTERACTIVE_MODE" == "yes" ]]; then
    # Check if we have a TTY (required for interactive mode)
    if [ ! -t 0 ]; then
        print_error "Interactive mode requires a terminal (TTY)."
        print_error "Please run from a terminal, or use automatic mode:"
        print_error "  curl -fsSL https://raw.githubusercontent.com/jatinkrmalik/vocalinux/main/install.sh | bash -s -- --auto"
        exit 1
    fi

    # Run interactive installation
    run_interactive_install
fi

# Set default engine for auto/non-interactive mode
if [[ "$NON_INTERACTIVE" == "yes" ]] && [[ -z "$SELECTED_ENGINE" ]]; then
    # Default to whisper.cpp for best performance
    SELECTED_ENGINE="whisper_cpp"
    print_info "Automatic mode: Installing with whisper.cpp (default engine)"
    print_info "For other engines, use: --engine=whisper or --engine=vosk"
    echo ""
fi

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a package is installed (for apt-based systems)
apt_package_installed() {
    dpkg -s "$1" >/dev/null 2>&1
}

# Function to check if a package is installed (for dnf-based systems)
dnf_package_installed() {
    rpm -q "$1" >/dev/null 2>&1
}

# Function to check if a package is installed (for pacman-based systems)
pacman_package_installed() {
    pacman -Q "$1" >/dev/null 2>&1
}

# Function to install system dependencies based on the detected distribution
install_system_dependencies() {
    print_info "Installing system dependencies..."

    # Check for pkg-config first (required for library detection)
    if ! command_exists pkg-config; then
        print_error "pkg-config is not installed but is required for library detection"
        print_info "Please install pkg-config using your package manager:"
        print_info "  Ubuntu/Debian: sudo apt install pkg-config"
        print_info "  Fedora/RHEL: sudo dnf install pkg-config"
        print_info "  Arch: sudo pacman -S pkgconf"
        print_info "  openSUSE: sudo zypper install pkg-config"
        print_info "  Gentoo: sudo emerge pkgconf"
        print_info "  Alpine: sudo apk add pkgconf"
        print_info "  Void: sudo xbps-install -Sy pkg-config"
        print_info "  Solus: sudo eopkg install pkg-config"
        exit 1
    fi

    # Define package names for different distributions
    local APT_PACKAGES_UBUNTU="python3-pip python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-appindicator3-0.1 libgirepository1.0-dev python3-dev build-essential portaudio19-dev python3-venv pkg-config wget curl unzip vulkan-tools"
    local APT_PACKAGES_DEBIAN_BASE="python3-pip python3-gi python3-gi-cairo gir1.2-gtk-3.0 libcairo2-dev python3-dev build-essential portaudio19-dev python3-venv pkg-config wget curl unzip"
    local APT_PACKAGES_DEBIAN_11_12="$APT_PACKAGES_DEBIAN_BASE libgirepository1.0-dev gir1.2-ayatanaappindicator3-0.1"
    local APT_PACKAGES_DEBIAN_13_PLUS="$APT_PACKAGES_DEBIAN_BASE libgirepository-2.0-dev gir1.2-ayatanaappindicator3-0.1"
    local DNF_PACKAGES="python3-pip python3-gobject gtk3 libappindicator-gtk3 gobject-introspection-devel python3-devel portaudio-devel python3-virtualenv pkg-config wget curl unzip vulkan-tools"
    local PACMAN_PACKAGES="python-pip python-gobject gtk3 libappindicator-gtk3 gobject-introspection python-cairo portaudio python-virtualenv pkg-config wget curl unzip base-devel vulkan-tools"
    local ZYPPER_PACKAGES="python3-pip python3-gobject python3-gobject-cairo gtk3 libappindicator-gtk3 gobject-introspection-devel python3-devel portaudio-devel python3-virtualenv pkg-config wget curl unzip vulkan-tools"
    # Gentoo uses Portage and different package naming convention
    local EMERGE_PACKAGES="dev-python/pygobject:3 x11-libs/gtk+:3 dev-libs/libappindicator:3 media-libs/portaudio dev-lang/python:3.8 pkgconf"
    # Alpine Linux uses apk and has musl libc
    local APK_PACKAGES="py3-gobject3 py3-pip gtk+3.0 py3-cairo portaudio-dev py3-virtualenv pkgconf wget curl unzip"
    # Void Linux uses xbps
    local XBPS_PACKAGES="python3-pip python3-gobject gtk+3 libappindicator gobject-introspection portaudio-devel python3-devel pkg-config wget curl unzip"
    # Solus uses eopkg
    local EOPKG_PACKAGES="python3-pip python3-gobject gtk3 libappindicator gobject-introspection-devel portaudio-devel python3-virtualenv pkg-config wget curl unzip"

    local MISSING_PACKAGES=""
    local INSTALL_CMD=""
    local UPDATE_CMD=""

    case "$DISTRO_FAMILY" in
        ubuntu|debian)
            local APT_PACKAGES="$APT_PACKAGES_UBUNTU"
            if [[ "$DISTRO_FAMILY" == "debian" ]]; then
                local DEBIAN_MAJOR="${DISTRO_VERSION%%.*}"
                if [[ "$DEBIAN_MAJOR" =~ ^[0-9]+$ ]] && [ "$DEBIAN_MAJOR" -ge 13 ]; then
                    APT_PACKAGES="$APT_PACKAGES_DEBIAN_13_PLUS"
                else
                    APT_PACKAGES="$APT_PACKAGES_DEBIAN_11_12"
                fi
            fi

            # Check for missing packages
            for pkg in $APT_PACKAGES; do
                if ! apt_package_installed "$pkg"; then
                    MISSING_PACKAGES="$MISSING_PACKAGES $pkg"
                fi
            done

            if [ -n "$MISSING_PACKAGES" ]; then
                print_info "Installing missing packages:$MISSING_PACKAGES"
                sudo apt update || { print_error "Failed to update package lists"; exit 1; }

                # Handle appindicator package for Ubuntu (old package deprecated in newer releases)
                if echo "$MISSING_PACKAGES" | grep -q "gir1.2-appindicator3-0.1"; then
                    FILTERED_PACKAGES=$(echo "$MISSING_PACKAGES" | sed 's/gir1.2-appindicator3-0.1//' | xargs)

                    if ! sudo apt install -y gir1.2-appindicator3-0.1 2>/dev/null; then
                        print_info "gir1.2-appindicator3-0.1 not available, trying gir1.2-ayatanaappindicator3-0.1..."
                        if ! sudo apt install -y gir1.2-ayatanaappindicator3-0.1; then
                            print_error "Failed to install appindicator package (tried both gir1.2-appindicator3-0.1 and gir1.2-ayatanaappindicator3-0.1)"
                            exit 1
                        fi
                        print_info "Successfully installed gir1.2-ayatanaappindicator3-0.1 (modern replacement)"
                    fi

                    if [ -n "$FILTERED_PACKAGES" ]; then
                        sudo apt install -y $FILTERED_PACKAGES || { print_error "Failed to install dependencies"; exit 1; }
                    fi
                else
                    sudo apt install -y $MISSING_PACKAGES || { print_error "Failed to install dependencies"; exit 1; }
                fi
            else
                print_info "All required packages are already installed."
            fi
            ;;

        fedora)
            # For Fedora/RHEL-based systems
            if command_exists dnf; then
                INSTALL_CMD="sudo dnf install -y"
                UPDATE_CMD="sudo dnf check-update"
            elif command_exists yum; then
                INSTALL_CMD="sudo yum install -y"
                UPDATE_CMD="sudo yum check-update"
            else
                print_error "No supported package manager found (dnf/yum)"
                exit 1
            fi

            # Check for missing packages
            for pkg in $DNF_PACKAGES; do
                if ! dnf_package_installed "$pkg"; then
                    MISSING_PACKAGES="$MISSING_PACKAGES $pkg"
                fi
            done

            if [ -n "$MISSING_PACKAGES" ]; then
                print_info "Installing missing packages:$MISSING_PACKAGES"
                $UPDATE_CMD
                $INSTALL_CMD $MISSING_PACKAGES || { print_error "Failed to install dependencies"; exit 1; }
            else
                print_info "All required packages are already installed."
            fi
            ;;

        arch)
            # For Arch-based systems
            if ! command_exists pacman; then
                print_error "Pacman package manager not found"
                exit 1
            fi

            # Check for missing packages
            for pkg in $PACMAN_PACKAGES; do
                if ! pacman_package_installed "$pkg"; then
                    MISSING_PACKAGES="$MISSING_PACKAGES $pkg"
                fi
            done

            if [ -n "$MISSING_PACKAGES" ]; then
                print_info "Installing missing packages:$MISSING_PACKAGES"
                sudo pacman -Sy
                sudo pacman -S --noconfirm $MISSING_PACKAGES || { print_error "Failed to install dependencies"; exit 1; }
            else
                print_info "All required packages are already installed."
            fi
            ;;

        suse)
            # For openSUSE
            if ! command_exists zypper; then
                print_error "Zypper package manager not found"
                exit 1
            fi

            print_info "Updating package lists and installing dependencies..."
            sudo zypper refresh
            sudo zypper install -y $ZYPPER_PACKAGES || { print_error "Failed to install dependencies"; exit 1; }
            ;;

        gentoo)
            # For Gentoo Linux
            if ! command_exists emerge; then
                print_error "Emerge package manager not found"
                exit 1
            fi

            print_info "Gentoo detected. Installing dependencies..."
            print_warning "Gentoo uses emerge. This may take longer as packages are compiled from source."

            # Check for missing packages
            MISSING_PACKAGES=""
            for pkg in $EMERGE_PACKAGES; do
                # Gentoo uses qlist to check if packages are installed
                if ! qlist -I "$pkg" >/dev/null 2>&1; then
                    MISSING_PACKAGES="$MISSING_PACKAGES $pkg"
                fi
            done

            if [ -n "$MISSING_PACKAGES" ]; then
                print_info "Installing packages:$MISSING_PACKAGES"
                # Update Portage tree first
                sudo emerge --sync || { print_error "Failed to sync Portage tree"; exit 1; }
                # Install missing packages
                sudo emerge $MISSING_PACKAGES || { print_error "Failed to install dependencies"; exit 1; }
            else
                print_info "All required packages are already installed."
            fi
            ;;

        alpine)
            # For Alpine Linux
            if ! command_exists apk; then
                print_error "Apk package manager not found"
                exit 1
            fi

            print_info "Alpine Linux detected."
            print_warning "Alpine uses musl libc. Some Python packages may not have pre-built wheels."

            # Check for missing packages
            MISSING_PACKAGES=""
            for pkg in $APK_PACKAGES; do
                if ! apk info -e "$pkg" >/dev/null 2>&1; then
                    MISSING_PACKAGES="$MISSING_PACKAGES $pkg"
                fi
            done

            if [ -n "$MISSING_PACKAGES" ]; then
                print_info "Installing packages:$MISSING_PACKAGES"
                sudo apk update || { print_error "Failed to update package indexes"; exit 1; }
                sudo apk add $MISSING_PACKAGES || { print_error "Failed to install dependencies"; exit 1; }
            else
                print_info "All required packages are already installed."
            fi
            ;;

        void)
            # For Void Linux
            if ! command_exists xbps; then
                print_error "Xbps package manager not found"
                exit 1
            fi

            print_info "Void Linux detected."

            # Check for missing packages
            MISSING_PACKAGES=""
            for pkg in $XBPS_PACKAGES; do
                if ! xbps-query -S "$pkg" >/dev/null 2>&1; then
                    MISSING_PACKAGES="$MISSING_PACKAGES $pkg"
                fi
            done

            if [ -n "$MISSING_PACKAGES" ]; then
                print_info "Installing packages:$MISSING_PACKAGES"
                sudo xbps-install -Sy $MISSING_PACKAGES || { print_error "Failed to install dependencies"; exit 1; }
            else
                print_info "All required packages are already installed."
            fi
            ;;

        solus)
            # For Solus
            if ! command_exists eopkg; then
                print_error "Eopkg package manager not found"
                exit 1
            fi

            print_info "Solus detected."

            # Check for missing packages
            MISSING_PACKAGES=""
            for pkg in $EOPKG_PACKAGES; do
                if ! eopkg info "$pkg" >/dev/null 2>&1; then
                    MISSING_PACKAGES="$MISSING_PACKAGES $pkg"
                fi
            done

            if [ -n "$MISSING_PACKAGES" ]; then
                print_info "Installing packages:$MISSING_PACKAGES"
                sudo eopkg install $MISSING_PACKAGES || { print_error "Failed to install dependencies"; exit 1; }
            else
                print_info "All required packages are already installed."
            fi
            ;;

        mageia)
            # For Mageia
            if command_exists dnf; then
                INSTALL_CMD="sudo dnf install -y"
                UPDATE_CMD="sudo dnf check-update"
            elif command_exists urpmi; then
                INSTALL_CMD="sudo urpmi --force"
                UPDATE_CMD="sudo urpmi.update -a"
            else
                print_error "No supported package manager found (dnf/urpmi)"
                exit 1
            fi

            # Use similar packages to Fedora/RHEL
            for pkg in $DNF_PACKAGES; do
                # Mageia uses rpm like Fedora
                if ! rpm -q "$pkg" >/dev/null 2>&1; then
                    MISSING_PACKAGES="$MISSING_PACKAGES $pkg"
                fi
            done

            if [ -n "$MISSING_PACKAGES" ]; then
                print_info "Installing missing packages:$MISSING_PACKAGES"
                $UPDATE_CMD 2>/dev/null || true
                $INSTALL_CMD $MISSING_PACKAGES || { print_error "Failed to install dependencies"; exit 1; }
            else
                print_info "All required packages are already installed."
            fi
            ;;

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
            print_info "For more information, see the project wiki:"
            print_info "  https://github.com/jatinkrmalik/vocalinux/wiki"
            print_info ""
            if [[ "$NON_INTERACTIVE" != "yes" ]]; then
                read -p "Continue anyway? (y/n) " -n 1 -r
                echo
                if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                    exit 1
                fi
            else
                print_info "Non-interactive mode: continuing (dependencies may be missing)..."
            fi
            ;;
    esac
}

# Install system dependencies
install_system_dependencies

# Define XDG directories
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/vocalinux"
DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/vocalinux"
DESKTOP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
ICON_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor/scalable/apps"

# Function to detect and install text input tools
install_text_input_tools() {
    # Detect session type more robustly
    local SESSION_TYPE="unknown"

    # Check XDG_SESSION_TYPE first
    if [ -n "$XDG_SESSION_TYPE" ]; then
        SESSION_TYPE="$XDG_SESSION_TYPE"
    # Check for Wayland-specific environment variables
    elif [ -n "$WAYLAND_DISPLAY" ]; then
        SESSION_TYPE="wayland"
    # Check if X server is running
    elif [ -n "$DISPLAY" ] && command_exists xset && xset q &>/dev/null; then
        SESSION_TYPE="x11"
    # Check loginctl if available
    elif command_exists loginctl; then
        SESSION_TYPE=$(loginctl show-session $(loginctl | grep $(whoami) | awk '{print $1}') -p Type | cut -d= -f2)
    fi

    print_info "Detected session type: $SESSION_TYPE"

    # Install appropriate tools based on session type and distribution
    case "$SESSION_TYPE" in
        wayland)
            print_info "Installing Wayland text input tools..."
            case "$DISTRO_FAMILY" in
                ubuntu|debian)
                    if ! apt_package_installed "wtype"; then
                        sudo apt install -y wtype || { print_warning "Failed to install wtype. Text injection may not work properly."; }
                    else
                        print_info "wtype is already installed."
                    fi
                    ;;
                fedora)
                    if command_exists dnf && ! dnf_package_installed "wtype"; then
                        sudo dnf install -y wtype || { print_warning "Failed to install wtype. Text injection may not work properly."; }
                    elif command_exists yum && ! rpm -q wtype &>/dev/null; then
                        sudo yum install -y wtype || { print_warning "Failed to install wtype. Text injection may not work properly."; }
                    else
                        print_info "wtype is already installed."
                    fi
                    ;;
                arch)
                    if ! pacman_package_installed "wtype"; then
                        sudo pacman -S --noconfirm wtype || { print_warning "Failed to install wtype. Text injection may not work properly."; }
                    else
                        print_info "wtype is already installed."
                    fi
                    ;;
                suse)
                    sudo zypper install -y wtype || { print_warning "Failed to install wtype. Text injection may not work properly."; }
                    ;;
                gentoo)
                    if ! qlist -I wtype >/dev/null 2>&1; then
                        sudo emerge wtype || { print_warning "Failed to install wtype. Text injection may not work properly."; }
                    else
                        print_info "wtype is already installed."
                    fi
                    ;;
                alpine)
                    if ! apk info -e wtype >/dev/null 2>&1; then
                        sudo apk add wtype || { print_warning "Failed to install wtype. Text injection may not work properly."; }
                    else
                        print_info "wtype is already installed."
                    fi
                    ;;
                void)
                    if ! xbps-query -S wtype >/dev/null 2>&1; then
                        sudo xbps-install -Sy wtype || { print_warning "Failed to install wtype. Text injection may not work properly."; }
                    else
                        print_info "wtype is already installed."
                    fi
                    ;;
                solus)
                    if ! eopkg info wtype >/dev/null 2>&1; then
                        sudo eopkg install wtype || { print_warning "Failed to install wtype. Text injection may not work properly."; }
                    else
                        print_info "wtype is already installed."
                    fi
                    ;;
                mageia)
                    if command_exists dnf && ! rpm -q wtype >/dev/null 2>&1; then
                        sudo dnf install -y wtype || { print_warning "Failed to install wtype. Text injection may not work properly."; }
                    elif command_exists urpmi && ! rpm -q wtype >/dev/null 2>&1; then
                        sudo urpmi -y wtype || { print_warning "Failed to install wtype. Text injection may not work properly."; }
                    else
                        print_info "wtype is already installed."
                    fi
                    ;;
                *)
                    print_warning "Unsupported distribution for Wayland text input tools."
                    print_warning "Please install 'wtype' manually for Wayland text input support."
                    ;;
            esac

            # Try to install ydotool as additional fallback for Wayland
            # ydotool works better with some compositors (like GNOME) where wtype may fail
            print_info "Attempting to install ydotool for better Wayland compatibility..."
            case "$DISTRO_FAMILY" in
                ubuntu|debian)
                    if ! apt_package_installed "ydotool"; then
                        sudo apt install -y ydotool 2>/dev/null || print_info "ydotool not available in repos (optional)"
                    fi
                    ;;
                fedora)
                    if command_exists dnf; then
                        sudo dnf install -y ydotool 2>/dev/null || print_info "ydotool not available in repos (optional)"
                    fi
                    ;;
                arch)
                    if ! pacman_package_installed "ydotool"; then
                        sudo pacman -S --noconfirm ydotool 2>/dev/null || print_info "ydotool not available in repos (optional)"
                    fi
                    ;;
            esac

            # Add user to input group for ydotool/dotool support
            if ! groups | grep -q '\binput\b'; then
                print_info "Adding $USER to 'input' group for text injection..."
                sudo usermod -aG input "$USER" || print_warning "Failed to add user to input group"
                print_warning "You will need to LOG OUT and back in for text injection to work with ydotool/dotool"
            fi

            # Install udev rule for ydotool/dotool
            if [ ! -f /etc/udev/rules.d/80-dotool.rules ]; then
                print_info "Installing udev rule for input device access..."
                echo 'KERNEL=="uinput", GROUP="input", MODE="0620", OPTIONS+="static_node=uinput"' \
                    | sudo tee /etc/udev/rules.d/80-dotool.rules >/dev/null 2>&1 || print_warning "Failed to install udev rule"
                sudo udevadm control --reload 2>/dev/null || true
                sudo udevadm trigger 2>/dev/null || true
            fi
            ;;

        x11|"")
            print_info "Installing X11 text input tools..."
            case "$DISTRO_FAMILY" in
                ubuntu|debian)
                    if ! apt_package_installed "xdotool"; then
                        sudo apt install -y xdotool || { print_warning "Failed to install xdotool. Text injection may not work properly."; }
                    else
                        print_info "xdotool is already installed."
                    fi
                    ;;
                fedora)
                    if command_exists dnf && ! dnf_package_installed "xdotool"; then
                        sudo dnf install -y xdotool || { print_warning "Failed to install xdotool. Text injection may not work properly."; }
                    elif command_exists yum && ! rpm -q xdotool &>/dev/null; then
                        sudo yum install -y xdotool || { print_warning "Failed to install xdotool. Text injection may not work properly."; }
                    else
                        print_info "xdotool is already installed."
                    fi
                    ;;
                arch)
                    if ! pacman_package_installed "xdotool"; then
                        sudo pacman -S --noconfirm xdotool || { print_warning "Failed to install xdotool. Text injection may not work properly."; }
                    else
                        print_info "xdotool is already installed."
                    fi
                    ;;
                suse)
                    sudo zypper install -y xdotool || { print_warning "Failed to install xdotool. Text injection may not work properly."; }
                    ;;
                gentoo)
                    if ! qlist -I xdotool >/dev/null 2>&1; then
                        sudo emerge xdotool || { print_warning "Failed to install xdotool. Text injection may not work properly."; }
                    else
                        print_info "xdotool is already installed."
                    fi
                    ;;
                alpine)
                    if ! apk info -e xdotool >/dev/null 2>&1; then
                        sudo apk add xdotool || { print_warning "Failed to install xdotool. Text injection may not work properly."; }
                    else
                        print_info "xdotool is already installed."
                    fi
                    ;;
                void)
                    if ! xbps-query -S xdotool >/dev/null 2>&1; then
                        sudo xbps-install -Sy xdotool || { print_warning "Failed to install xdotool. Text injection may not work properly."; }
                    else
                        print_info "xdotool is already installed."
                    fi
                    ;;
                solus)
                    if ! eopkg info xdotool >/dev/null 2>&1; then
                        sudo eopkg install xdotool || { print_warning "Failed to install xdotool. Text injection may not work properly."; }
                    else
                        print_info "xdotool is already installed."
                    fi
                    ;;
                mageia)
                    if command_exists dnf && ! rpm -q xdotool >/dev/null 2>&1; then
                        sudo dnf install -y xdotool || { print_warning "Failed to install xdotool. Text injection may not work properly."; }
                    elif command_exists urpmi && ! rpm -q xdotool >/dev/null 2>&1; then
                        sudo urpmi -y xdotool || { print_warning "Failed to install xdotool. Text injection may not work properly."; }
                    else
                        print_info "xdotool is already installed."
                    fi
                    ;;
                *)
                    print_warning "Unsupported distribution for X11 text input tools."
                    print_warning "Please install 'xdotool' manually for X11 text input support."
                    ;;
            esac
            ;;

        *)
            print_warning "Unknown session type: $SESSION_TYPE"
            print_warning "Installing both Wayland and X11 text input tools for compatibility..."

            # Install both tools based on distribution
            case "$DISTRO_FAMILY" in
                ubuntu|debian)
                    sudo apt install -y xdotool wtype || { print_warning "Failed to install text input tools. Text injection may not work properly."; }
                    ;;
                fedora|mageia)
                    if command_exists dnf; then
                        sudo dnf install -y xdotool wtype || { print_warning "Failed to install text input tools. Text injection may not work properly."; }
                    elif command_exists yum; then
                        sudo yum install -y xdotool wtype || { print_warning "Failed to install text input tools. Text injection may not work properly."; }
                    fi
                    # Mageia also supports urpmi
                    if [[ "$DISTRO_FAMILY" == "mageia" ]] && command_exists urpmi; then
                        sudo urpmi -y xdotool wtype || { print_warning "Failed to install text input tools. Text injection may not work properly."; }
                    fi
                    ;;
                arch)
                    sudo pacman -S --noconfirm xdotool wtype || { print_warning "Failed to install text input tools. Text injection may not work properly."; }
                    ;;
                suse)
                    sudo zypper install -y xdotool wtype || { print_warning "Failed to install text input tools. Text injection may not work properly."; }
                    ;;
                gentoo)
                    sudo emerge xdotool wtype || { print_warning "Failed to install text input tools. Text injection may not work properly."; }
                    ;;
                alpine)
                    sudo apk add xdotool wtype || { print_warning "Failed to install text input tools. Text injection may not work properly."; }
                    ;;
                void)
                    sudo xbps-install -Sy xdotool wtype || { print_warning "Failed to install text input tools. Text injection may not work properly."; }
                    ;;
                solus)
                    sudo eopkg install xdotool wtype || { print_warning "Failed to install text input tools. Text injection may not work properly."; }
                    ;;
                *)
                    print_warning "Unsupported distribution for text input tools."
                    print_warning "Please install 'xdotool' and 'wtype' manually for text input support."
                    ;;
            esac
            ;;
    esac
}

# Install text input tools based on session type
install_text_input_tools

# Create necessary directories
print_info "Creating application directories..."
mkdir -p "$CONFIG_DIR"
mkdir -p "$DATA_DIR/models"
mkdir -p "$DESKTOP_DIR"
mkdir -p "$ICON_DIR"

# Check Python version
check_python_version() {
    local MIN_VERSION="3.8"
    local PYTHON_CMD="python3"

    # Check if python3 command exists
    if ! command_exists python3; then
        print_error "Python 3 is not installed or not in PATH"
        return 1
    fi

    # Get Python version
    local PY_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    print_info "Detected Python version: $PY_VERSION"

    # Compare versions
    if [[ $(echo -e "$PY_VERSION\n$MIN_VERSION" | sort -V | head -n1) == "$MIN_VERSION" || "$PY_VERSION" == "$MIN_VERSION" ]]; then
        return 0
    else
        print_error "This application requires Python $MIN_VERSION or newer. Detected: $PY_VERSION"
        return 1
    fi
}

# Set up virtual environment with error handling
setup_virtual_environment() {
    print_info "Setting up Python virtual environment in $VENV_DIR..."

    # Check if virtual environment already exists
    if [ -d "$VENV_DIR" ] && [ -f "$VENV_DIR/bin/activate" ]; then
        print_warning "Virtual environment already exists in $VENV_DIR"
        if [[ "$NON_INTERACTIVE" == "yes" ]]; then
            # In non-interactive mode, reuse existing venv
            print_info "Non-interactive mode: using existing virtual environment."
            source "$VENV_DIR/bin/activate" || { print_error "Failed to activate virtual environment"; exit 1; }
            return 0
        else
            read -p "Do you want to recreate it? (y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                print_info "Removing existing virtual environment..."
                rm -rf "$VENV_DIR"
            else
                print_info "Using existing virtual environment."
                source "$VENV_DIR/bin/activate" || { print_error "Failed to activate virtual environment"; exit 1; }
                return 0
            fi
        fi
    fi

    # Create virtual environment
    # Use --system-site-packages to access pre-compiled system packages like PyGObject
    # This avoids build failures with Python 3.13+ where PyGObject may not build from source
    python3 -m venv --system-site-packages "$VENV_DIR" || {
        print_error "Failed to create virtual environment. Please check your Python installation."
        exit 1
    }

    # Activate virtual environment
    source "$VENV_DIR/bin/activate" || { print_error "Failed to activate virtual environment"; exit 1; }

    # Update pip and setuptools
    print_info "Updating pip, setuptools, and wheel..."
    pip install --upgrade pip setuptools wheel || { print_error "Failed to update pip, setuptools, and wheel"; exit 1; }

    print_info "Virtual environment activated successfully."
}

# Check Python version
if ! check_python_version; then
    print_warning "Continuing with unsupported Python version. Some features may not work correctly."
fi

# Set up virtual environment
setup_virtual_environment

# Create activation script for users
# Put it in ~/.local/bin when running remotely, or current dir when running locally
if [[ "$CLEANUP_ON_EXIT" == "yes" ]]; then
    ACTIVATION_SCRIPT_DIR="$HOME/.local/bin"
    mkdir -p "$ACTIVATION_SCRIPT_DIR"
else
    ACTIVATION_SCRIPT_DIR="."
fi
ACTIVATION_SCRIPT="$ACTIVATION_SCRIPT_DIR/activate-vocalinux.sh"

cat > "$ACTIVATION_SCRIPT" << EOF
#!/bin/bash
# This script activates the Vocalinux virtual environment
source "$VENV_DIR/bin/activate"
echo "Vocalinux virtual environment activated."
echo "To start the application, run: vocalinux"
EOF
chmod +x "$ACTIVATION_SCRIPT"
print_info "Created activation script: $ACTIVATION_SCRIPT"

# Function to install Python package with error handling and verification
install_python_package() {
    # Create a temporary directory for pip logs
    local PIP_LOG_DIR=$(mktemp -d)
    local PIP_LOG_FILE="$PIP_LOG_DIR/pip_log.txt"

    # Detect GI_TYPELIB_PATH early for cross-distro compatibility
    # This ensures the path is available for both verification and wrapper scripts
    local GI_TYPELIB_DETECTED
    GI_TYPELIB_DETECTED=$(detect_typelib_path)
    print_info "Detected GI_TYPELIB_PATH: $GI_TYPELIB_DETECTED"

    # Function to verify package installation
    verify_package_installed() {
        local PKG_NAME="vocalinux"
        # Use venv python and set GI_TYPELIB_PATH for PyGObject
        # Use the detected path for cross-distro compatibility
        GI_TYPELIB_PATH="$GI_TYPELIB_DETECTED" "$VENV_DIR/bin/python" -c "import $PKG_NAME" 2>/dev/null
        return $?
    }

    if [[ "$DEV_MODE" == "yes" ]]; then
        print_info "Installing Vocalinux in development mode..."

        # Install in development mode with logging
        pip install -e . --log "$PIP_LOG_FILE" || {
            print_error "Failed to install Vocalinux in development mode."
            print_error "Check the pip log for details: $PIP_LOG_FILE"
            return 1
        }

        # Install test dependencies
        print_info "Installing test dependencies..."
        pip install pytest pytest-mock pytest-cov --log "$PIP_LOG_FILE" || {
            print_warning "Failed to install some test dependencies. Tests may not run correctly."
        }

        # Install all optional dependencies for development
        print_info "Installing all optional dependencies for development..."
        pip install ".[whisper,dev]" --log "$PIP_LOG_FILE" || {
            print_warning "Failed to install some optional dependencies."
            print_warning "Some features may not work correctly."
        }
    else
        print_info "Installing Vocalinux..."

        # Install the package with logging (includes pywhispercpp by default)
        pip install . --log "$PIP_LOG_FILE" || {
            print_error "Failed to install Vocalinux."
            print_error "Check the pip log for details: $PIP_LOG_FILE"
            return 1
        }

        # Engine installation logic:
        # - SELECTED_ENGINE is set by interactive mode or --engine flag
        # - Default is whisper_cpp for best performance
        case "${SELECTED_ENGINE:-whisper_cpp}" in
            whisper_cpp)
                print_info ""
                print_info "╔════════════════════════════════════════════════════════╗"
                print_info "║  Installing WHISPER.CPP (Recommended)                  ║"
                print_info "╠════════════════════════════════════════════════════════╣"
                print_info "║  • Fastest speech recognition                          ║"
                print_info "║  • Works with any GPU: NVIDIA, AMD, Intel              ║"
                print_info "║  • Uses Vulkan for GPU acceleration                    ║"
                print_info "║  • CPU-only mode available                             ║"
                print_info "╚════════════════════════════════════════════════════════╝"
                print_info ""
                print_info "whisper.cpp is included by default and ready to use!"
                print_info ""
                
                # Check for GPU acceleration support
                detect_vulkan || true
                if [[ "$HAS_VULKAN" == "yes" ]]; then
                    print_info "✓ Vulkan detected: $VULKAN_DEVICE"
                    print_info "  GPU acceleration will be used automatically"
                elif [[ "$HAS_NVIDIA_GPU" == "yes" ]]; then
                    print_info "✓ NVIDIA GPU detected: $GPU_NAME"
                    print_info "  CUDA acceleration will be used automatically"
                else
                    print_info "ℹ No GPU detected - whisper.cpp will use CPU mode"
                    print_info "  CPU mode is still very fast!"
                fi
                echo ""
                ;;
            
            whisper)
                print_info "Installing Whisper (OpenAI) with PyTorch..."
                print_info "Note: This engine requires NVIDIA GPU for acceleration"
                print_info "      For AMD/Intel GPUs, whisper.cpp is recommended"
                
                # Install PyTorch and whisper
                pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu --log "$PIP_LOG_FILE" || {
                    print_warning "Failed to install PyTorch."
                }
                pip install openai-whisper --log "$PIP_LOG_FILE" || {
                    print_warning "Failed to install Whisper."
                    print_warning "Falling back to VOSK."
                }
                
                # Create config with whisper as default
                local WHISPER_CONFIG="$CONFIG_DIR/config.json"
                if [ ! -f "$WHISPER_CONFIG" ]; then
                    mkdir -p "$CONFIG_DIR"
                    cat > "$WHISPER_CONFIG" << 'WHISPER_CONFIG'
{
    "speech_recognition": {
        "engine": "whisper",
        "model_size": "tiny",
        "vosk_model_size": "small",
        "whisper_model_size": "tiny",
        "whisper_cpp_model_size": "tiny",
        "vad_sensitivity": 3,
        "silence_timeout": 2.0
    },
    "audio": {
        "device_index": null,
        "device_name": null
    },
    "shortcuts": {
        "toggle_recognition": "ctrl+ctrl"
    },
    "ui": {
        "start_minimized": false,
        "show_notifications": true
    },
    "advanced": {
        "debug_logging": false,
        "wayland_mode": false
    }
}
WHISPER_CONFIG
                fi
                ;;
            
            vosk)
                print_info "Installing VOSK (lightweight option)..."
                print_info "VOSK is fast and works well on older systems."
                
                # Create config with vosk as default
                local VOSK_CONFIG_FILE="$CONFIG_DIR/config.json"
                if [ ! -f "$VOSK_CONFIG_FILE" ]; then
                    mkdir -p "$CONFIG_DIR"
                    cat > "$VOSK_CONFIG_FILE" << 'VOSK_CONFIG'
{
    "speech_recognition": {
        "engine": "vosk",
        "model_size": "small",
        "vosk_model_size": "small",
        "whisper_model_size": "tiny",
        "whisper_cpp_model_size": "tiny",
        "vad_sensitivity": 3,
        "silence_timeout": 2.0
    },
    "audio": {
        "device_index": null,
        "device_name": null
    },
    "shortcuts": {
        "toggle_recognition": "ctrl+ctrl"
    },
    "ui": {
        "start_minimized": false,
        "show_notifications": true
    },
    "advanced": {
        "debug_logging": false,
        "wayland_mode": false
    }
}
VOSK_CONFIG
                fi
                ;;
        esac
    fi

    # Verify installation
    if verify_package_installed; then
        print_success "Vocalinux package installed successfully!"
        # Clean up log file if installation was successful
        rm -rf "$PIP_LOG_DIR"

        # GI_TYPELIB_PATH was already detected at the start of install_python_package

        # Create wrapper scripts in ~/.local/bin for easy access
        mkdir -p "$HOME/.local/bin"

        # Create vocalinux wrapper script
        # Uses 'sg input' to run with input group for keyboard shortcuts on Wayland
        # This allows shortcuts to work without logging out after installation
        cat > "$HOME/.local/bin/vocalinux" << WRAPPER_EOF
#!/bin/bash
# Wrapper script for Vocalinux that sets required environment variables
# and applies the 'input' group for keyboard shortcuts on Wayland
export GI_TYPELIB_PATH=$GI_TYPELIB_DETECTED

# Check if user is in input group but current session doesn't have it
if grep -q "^input:.*\b\$(whoami)\b" /etc/group 2>/dev/null && ! groups | grep -q '\binput\b'; then
    # Use sg to run with input group without requiring logout
    exec sg input -c "$VENV_DIR/bin/vocalinux \$*"
else
    exec "$VENV_DIR/bin/vocalinux" "\$@"
fi
WRAPPER_EOF
        chmod +x "$HOME/.local/bin/vocalinux"
        print_info "Created wrapper: ~/.local/bin/vocalinux"

        # Create vocalinux-gui wrapper script
        cat > "$HOME/.local/bin/vocalinux-gui" << WRAPPER_EOF
#!/bin/bash
# Wrapper script for Vocalinux GUI that sets required environment variables
# and applies the 'input' group for keyboard shortcuts on Wayland
export GI_TYPELIB_PATH=$GI_TYPELIB_DETECTED

# Check if user is in input group but current session doesn't have it
if grep -q "^input:.*\b\$(whoami)\b" /etc/group 2>/dev/null && ! groups | grep -q '\binput\b'; then
    # Use sg to run with input group without requiring logout
    exec sg input -c "$VENV_DIR/bin/vocalinux-gui \$*"
else
    exec "$VENV_DIR/bin/vocalinux-gui" "\$@"
fi
WRAPPER_EOF
        chmod +x "$HOME/.local/bin/vocalinux-gui"
        print_info "Created wrapper: ~/.local/bin/vocalinux-gui"

        # Check if ~/.local/bin is in PATH
        if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
            print_warning "~/.local/bin is not in your PATH"
            print_info "Add this line to your ~/.bashrc or ~/.zshrc:"
            print_info '  export PATH="$HOME/.local/bin:$PATH"'
        fi

        return 0
    else
        print_error "Vocalinux package installation verification failed."
        print_error "Check the pip log for details: $PIP_LOG_FILE"
        return 1
    fi
}

# Install Python package
if ! install_python_package; then
    print_error "Failed to install Vocalinux package. Installation cannot continue."
    exit 1
fi

# Function to download and install Whisper tiny model
install_whisper_model() {
    print_info "Installing Whisper tiny model (~75MB)..."

    # Create whisper models directory
    local WHISPER_DIR="$DATA_DIR/models/whisper"
    mkdir -p "$WHISPER_DIR"

    # Whisper tiny model URL and path
    local TINY_MODEL_URL="https://openaipublic.azureedge.net/main/whisper/models/65147644a518d12f04e32d6f3b26facc3f8dd46e5390956a9424a650c0ce22b9/tiny.pt"
    local TINY_MODEL_PATH="$WHISPER_DIR/tiny.pt"

    # Check if model already exists
    if [ -f "$TINY_MODEL_PATH" ]; then
        print_info "Whisper tiny model already exists at $TINY_MODEL_PATH"
        return 0
    fi

    # Check internet connectivity
    if ! command -v wget >/dev/null 2>&1 && ! command -v curl >/dev/null 2>&1; then
        print_warning "Neither wget nor curl found. Cannot download Whisper model."
        print_warning "Model will be downloaded on first application run."
        return 1
    fi

    # Test internet connectivity
    if ! ping -c 1 google.com >/dev/null 2>&1; then
        print_warning "No internet connection detected."
        print_warning "Whisper model will be downloaded on first application run."
        return 1
    fi

    print_info "Downloading Whisper tiny model..."
    print_info "This may take a few minutes depending on your internet connection."

    local TEMP_FILE="$TINY_MODEL_PATH.tmp"

    # Download the model
    if command -v wget >/dev/null 2>&1; then
        if ! wget --progress=bar:force:noscroll -O "$TEMP_FILE" "$TINY_MODEL_URL" 2>&1; then
            print_error "Failed to download Whisper model with wget"
            rm -f "$TEMP_FILE"
            return 1
        fi
    elif command -v curl >/dev/null 2>&1; then
        if ! curl -L --progress-bar -o "$TEMP_FILE" "$TINY_MODEL_URL"; then
            print_error "Failed to download Whisper model with curl"
            rm -f "$TEMP_FILE"
            return 1
        fi
    fi

    # Verify download
    if [ ! -f "$TEMP_FILE" ] || [ ! -s "$TEMP_FILE" ]; then
        print_error "Downloaded model file is empty or missing"
        rm -f "$TEMP_FILE"
        return 1
    fi

    # Move to final location
    mv "$TEMP_FILE" "$TINY_MODEL_PATH"

    # Verify the model file
    if [ -f "$TINY_MODEL_PATH" ]; then
        local MODEL_SIZE=$(du -h "$TINY_MODEL_PATH" | cut -f1)
        print_success "Whisper tiny model installed successfully ($MODEL_SIZE)"

        # Create a marker file to indicate this model was pre-installed
        echo "$(date)" > "$WHISPER_DIR/.vocalinux_preinstalled"

        return 0
    else
        print_error "Whisper model installation failed"
        return 1
    fi
}

# Function to download and install VOSK models
install_vosk_models() {
    print_info "Installing VOSK speech recognition models..."

    # Create models directory
    local MODELS_DIR="$DATA_DIR/models"
    mkdir -p "$MODELS_DIR"

    # Define model information
    local SMALL_MODEL_URL="https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
    local SMALL_MODEL_NAME="vosk-model-small-en-us-0.15"
    local SMALL_MODEL_PATH="$MODELS_DIR/$SMALL_MODEL_NAME"

    # Check if small model already exists
    if [ -d "$SMALL_MODEL_PATH" ]; then
        print_info "Small VOSK model already exists at $SMALL_MODEL_PATH"
        return 0
    fi

    # Check internet connectivity
    if ! command -v wget >/dev/null 2>&1 && ! command -v curl >/dev/null 2>&1; then
        print_warning "Neither wget nor curl found. Cannot download VOSK models."
        print_warning "Models will be downloaded on first application run."
        return 1
    fi

    # Test internet connectivity
    if ! ping -c 1 google.com >/dev/null 2>&1; then
        print_warning "No internet connection detected."
        print_warning "VOSK models will be downloaded on first application run."
        return 1
    fi

    print_info "Downloading small VOSK model (approximately 40MB)..."
    print_info "This may take a few minutes depending on your internet connection."

    local TEMP_ZIP="$MODELS_DIR/$(basename $SMALL_MODEL_URL)"

    # Download the model
    if command -v wget >/dev/null 2>&1; then
        if ! wget --progress=bar:force:noscroll -O "$TEMP_ZIP" "$SMALL_MODEL_URL" 2>&1; then
            print_error "Failed to download VOSK model with wget"
            rm -f "$TEMP_ZIP"
            return 1
        fi
    elif command -v curl >/dev/null 2>&1; then
        if ! curl -L --progress-bar -o "$TEMP_ZIP" "$SMALL_MODEL_URL"; then
            print_error "Failed to download VOSK model with curl"
            rm -f "$TEMP_ZIP"
            return 1
        fi
    fi

    # Verify download
    if [ ! -f "$TEMP_ZIP" ] || [ ! -s "$TEMP_ZIP" ]; then
        print_error "Downloaded model file is empty or missing"
        rm -f "$TEMP_ZIP"
        return 1
    fi

    print_info "Extracting VOSK model..."

    # Extract the model
    if command -v unzip >/dev/null 2>&1; then
        if ! unzip -q "$TEMP_ZIP" -d "$MODELS_DIR"; then
            print_error "Failed to extract VOSK model"
            rm -f "$TEMP_ZIP"
            return 1
        fi
    else
        print_error "unzip command not found. Cannot extract VOSK model."
        rm -f "$TEMP_ZIP"
        return 1
    fi

    # Clean up zip file
    rm -f "$TEMP_ZIP"

    # Verify extraction
    if [ -d "$SMALL_MODEL_PATH" ]; then
        print_success "VOSK small model installed successfully at $SMALL_MODEL_PATH"

        # Set proper permissions
        chmod -R 755 "$SMALL_MODEL_PATH"

        # Create a marker file to indicate this model was pre-installed
        echo "$(date)" > "$SMALL_MODEL_PATH/.vocalinux_preinstalled"

        return 0
    else
        print_error "VOSK model extraction failed - directory not found"
        return 1
    fi
}

# Function to install desktop entry with error handling
install_desktop_entry() {
    print_info "Installing desktop entry..."

    # Check if desktop entry file exists
    if [ ! -f "vocalinux.desktop" ]; then
        print_error "Desktop entry file not found: vocalinux.desktop"
        return 1
    fi

    # Create desktop directory if it doesn't exist
    mkdir -p "$DESKTOP_DIR" || {
        print_error "Failed to create desktop directory: $DESKTOP_DIR"
        return 1
    }

    # Copy desktop entry
    cp vocalinux.desktop "$DESKTOP_DIR/" || {
        print_error "Failed to copy desktop entry to $DESKTOP_DIR"
        return 1
    }

    # Update the desktop entry to use the wrapper script with GI_TYPELIB_PATH
    WRAPPER_SCRIPT="$HOME/.local/bin/vocalinux-gui"
    if [ ! -f "$WRAPPER_SCRIPT" ]; then
        print_warning "Wrapper script not found at $WRAPPER_SCRIPT"
        print_warning "Desktop entry may not work correctly"
    else
        # Update Exec line to include GI_TYPELIB_PATH for PyGObject
        # Use the detected path for cross-distro compatibility
        sed -i "s|^Exec=vocalinux|Exec=env GI_TYPELIB_PATH=$GI_TYPELIB_DETECTED $WRAPPER_SCRIPT|" "$DESKTOP_DIR/vocalinux.desktop" || {
            print_warning "Failed to update desktop entry path"
        }
        print_info "Updated desktop entry to use wrapper script with GI_TYPELIB_PATH"
    fi

    # Make desktop entry executable
    chmod +x "$DESKTOP_DIR/vocalinux.desktop" || {
        print_warning "Failed to make desktop entry executable"
    }

    return 0
}

# Function to install icons with error handling
install_icons() {
    print_info "Installing application icons..."

    # Create icon directory if it doesn't exist
    mkdir -p "$ICON_DIR" || {
        print_error "Failed to create icon directory: $ICON_DIR"
        return 1
    }

    # Check if icons directory exists
    if [ ! -d "resources/icons/scalable" ]; then
        print_warning "Custom icons not found in resources/icons/scalable directory"
        return 1
    fi

    # List of icons to install
    local ICONS=(
        "vocalinux.svg"
        "vocalinux-microphone.svg"
        "vocalinux-microphone-off.svg"
        "vocalinux-microphone-process.svg"
    )

    # Install each icon
    local INSTALLED_COUNT=0
    for icon in "${ICONS[@]}"; do
        if [ -f "resources/icons/scalable/$icon" ]; then
            cp "resources/icons/scalable/$icon" "$ICON_DIR/" || {
                print_warning "Failed to copy icon: $icon"
                continue
            }
            ((INSTALLED_COUNT++))
        else
            print_warning "Icon not found: resources/icons/scalable/$icon"
        fi
    done

    if [ "$INSTALLED_COUNT" -eq "${#ICONS[@]}" ]; then
        print_success "Installed all custom Vocalinux icons"
        return 0
    elif [ "$INSTALLED_COUNT" -gt 0 ]; then
        print_warning "Installed $INSTALLED_COUNT/${#ICONS[@]} custom Vocalinux icons"
        return 0
    else
        print_error "Failed to install any icons"
        return 1
    fi
}

# Function to update icon cache and desktop database
update_icon_cache() {
    print_info "Updating icon cache..."

    # Check if gtk-update-icon-cache command exists
    if command_exists gtk-update-icon-cache; then
        gtk-update-icon-cache -f -t "${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor" 2>/dev/null || {
            print_warning "Failed to update icon cache"
        }
    else
        print_warning "gtk-update-icon-cache command not found, skipping icon cache update"
    fi

    # Update desktop database so the app appears in application menus immediately
    print_info "Updating desktop database..."
    if command_exists update-desktop-database; then
        update-desktop-database "${XDG_DATA_HOME:-$HOME/.local/share}/applications" 2>/dev/null || {
            print_warning "Failed to update desktop database"
        }
    else
        print_warning "update-desktop-database command not found - app may not appear in menu until next login"
    fi
}

# Install desktop entry
install_desktop_entry || print_warning "Desktop entry installation failed"

# Install icons
install_icons || print_warning "Icon installation failed"

# Install Whisper tiny model if Whisper is available
# This is important because Whisper is the default engine in config_manager.py
# We check if Whisper was actually installed (importable) rather than relying on flags
if [ "$SKIP_MODELS" = "no" ]; then
    if "$VENV_DIR/bin/python" -c "import whisper" 2>/dev/null; then
        print_info "Whisper is installed - downloading tiny model (default engine)..."
        install_whisper_model || print_warning "Whisper model download failed - model will be downloaded on first run"
    elif [ "$NO_WHISPER_EXPLICIT" != "yes" ]; then
        # Whisper is not installed but wasn't explicitly disabled
        # This shouldn't happen in normal flow, but warn the user
        print_warning "Whisper not available but is the default engine."
        print_warning "The app will try to download the model on first run."
    else
        print_info "Whisper not installed (VOSK-only mode), skipping Whisper model download"
    fi
else
    print_info "Skipping Whisper model download (--skip-models specified)"
    print_info "Model will be downloaded automatically on first application run"
fi

# Install VOSK models (always useful as fallback, and required for VOSK-only mode)
if [ "$SKIP_MODELS" = "no" ]; then
    install_vosk_models || print_warning "VOSK model installation failed - models will be downloaded on first run"
else
    print_info "Skipping VOSK model installation (--skip-models specified)"
    print_info "Models will be downloaded automatically on first application run"
fi

# Update icon cache
update_icon_cache

# Function to run tests with better error handling
run_tests() {
    print_info "Running tests..."

    # Check if pytest is installed in the virtual environment
    if ! "$VENV_DIR/bin/python" -c "import pytest" &>/dev/null; then
        print_info "Installing pytest and related packages..."
        pip install pytest pytest-mock pytest-cov || {
            print_error "Failed to install pytest. Cannot run tests."
            return 1
        }
    fi

    # Create a directory for test results
    local TEST_RESULTS_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/vocalinux/test_results"
    mkdir -p "$TEST_RESULTS_DIR"
    local TEST_RESULTS_FILE="$TEST_RESULTS_DIR/pytest_$(date +%Y%m%d_%H%M%S).xml"

    print_info "Running tests with pytest..."
    print_info "This may take a few minutes..."

    # Run the tests with pytest and capture output
    local TEST_OUTPUT_FILE=$(mktemp)
    if pytest -v --junitxml="$TEST_RESULTS_FILE" | tee "$TEST_OUTPUT_FILE"; then
        print_success "All tests passed!"
        print_info "Test results saved to: $TEST_RESULTS_FILE"
        rm -f "$TEST_OUTPUT_FILE"
        return 0
    else
        local FAILED_COUNT=$(grep -c "FAILED" "$TEST_OUTPUT_FILE")
        print_error "$FAILED_COUNT tests failed!"
        print_info "Test results saved to: $TEST_RESULTS_FILE"
        print_info "Check the test output for details."
        rm -f "$TEST_OUTPUT_FILE"
        return 1
    fi
}

# Run tests if requested
if [[ "$RUN_TESTS" == "yes" ]]; then
    if run_tests; then
        print_success "Test suite completed successfully."
    else
        print_warning "Test suite completed with failures."
        print_warning "You can still use the application, but some features might not work as expected."
    fi
fi

# Function to verify the installation
verify_installation() {
    print_info "Verifying installation..."
    local ISSUES=0

    # Check if virtual environment exists and is activated
    if [ ! -d "$VENV_DIR" ] || [ ! -f "$VENV_DIR/bin/activate" ]; then
        print_error "Virtual environment not found or incomplete."
        ((ISSUES++))
    fi

    # Check if vocalinux command is available
    if ! command -v vocalinux &>/dev/null && [ ! -f "$VENV_DIR/bin/vocalinux" ]; then
        print_error "Vocalinux command not found."
        ((ISSUES++))
    fi

    # Check if desktop entry is installed
    if [ ! -f "$DESKTOP_DIR/vocalinux.desktop" ]; then
        print_warning "Desktop entry not found. Application may not appear in application menu."
        ((ISSUES++))
    fi

    # Check if icons are installed
    local ICON_COUNT=0
    for icon in vocalinux.svg vocalinux-microphone.svg vocalinux-microphone-off.svg vocalinux-microphone-process.svg; do
        if [ -f "$ICON_DIR/$icon" ]; then
            ((ICON_COUNT++))
        fi
    done

    if [ "$ICON_COUNT" -lt 4 ]; then
        print_warning "Some icons are missing. Application may not display correctly."
        ((ISSUES++))
    fi

    # Check if Python package is importable using venv python
    if ! "$VENV_DIR/bin/python" -c "import vocalinux" &>/dev/null; then
        print_error "Vocalinux Python package cannot be imported."
        ((ISSUES++))
    fi

    # Return the number of issues found
    return $ISSUES
}

# Function to print beautiful welcome message
print_welcome_message() {
    local ISSUES=$1

    clear_screen

    # ASCII art header
    cat << "EOF"

  ▗▖  ▗▖ ▗▄▖  ▗▄▄▖ ▗▄▖ ▗▖   ▗▄▄▄▖▗▖  ▗▖▗▖ ▗▖▗▖  ▗▖
  ▐▌  ▐▌▐▌ ▐▌▐▌   ▐▌ ▐▌▐▌     █  ▐▛▚▖▐▌▐▌ ▐▌ ▝▚▞▘
  ▐▌  ▐▌▐▌ ▐▌▐▌   ▐▛▀▜▌▐▌     █  ▐▌ ▝▜▌▐▌ ▐▌  ▐▌
   ▝▚▞▘ ▝▚▄▞▘▝▚▄▄▖▐▌ ▐▌▐▙▄▄▖▗▄█▄▖▐▌  ▐▌▝▚▄▞▘▗▞▘▝▚▖

                     ✓ Installation Complete!

EOF

    # Success or warning message
    if [ "$ISSUES" -eq 0 ]; then
        print_success "Vocalinux has been installed successfully!"
    else
        print_warning "Installation complete with $ISSUES minor issue(s)"
        print_warning "The application should still work normally."
    fi

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  Getting Started"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "1. Launch Vocalinux from your app menu"
    echo "   Look for 'Vocalinux' in your application launcher."
    echo ""
    echo -e "   Or from terminal: \e[36mvocalinux\e[0m"
    echo ""
    echo "2. Find Vocalinux in your system tray (top bar)"
    echo "   • Click the icon to access settings"
    echo "   • Right-click for options (Quit, Settings, etc.)"
    echo ""
    echo "3. Start dictating!"
    echo -e "   \e[1mDouble-tap Ctrl\e[0m anywhere to start/stop dictation"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  First Run Tips"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "• Speak clearly and at a natural pace"
    echo "• Use voice commands: 'period', 'comma', 'new line', 'delete that'"
    echo "• Both engines are 100% offline - your privacy is protected"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  Need Help?"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "• Report issues: https://github.com/jatinkrmalik/vocalinux/issues"
    echo "• Documentation: https://github.com/jatinkrmalik/vocalinux"
    echo "• Star us on GitHub: ⭐ https://github.com/jatinkrmalik/vocalinux"
    echo ""

    # Installation details (optional, for debugging)
    if [[ "$VERBOSE" == "yes" ]]; then
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "  Installation Details"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo "Virtual environment: $VENV_DIR"
        echo "Desktop entry: $DESKTOP_DIR/vocalinux.desktop"
        echo "Configuration: $CONFIG_DIR"
        echo "Data directory: $DATA_DIR"
        echo ""
    fi
}

# Verify the installation
verify_installation
INSTALL_ISSUES=$?

# Print welcome message
print_welcome_message $INSTALL_ISSUES

print_success "Installation process completed!"
