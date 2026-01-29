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

# Detect if running non-interactively (e.g., via curl | bash)
if [ ! -t 0 ]; then
    NON_INTERACTIVE="yes"
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
        --with-whisper)
            WITH_WHISPER="yes"
            shift
            ;;
        --whisper-cpu)
            WITH_WHISPER="yes"
            WHISPER_CPU="yes"
            shift
            ;;
        --no-whisper)
            WITH_WHISPER="no"
            NO_WHISPER_EXPLICIT="yes"
            NON_INTERACTIVE="yes"  # Skip the prompt
            shift
            ;;
        --tag=*)
            INSTALL_TAG="${1#*=}"
            shift
            ;;
        -y|--yes)
            NON_INTERACTIVE="yes"
            shift
            ;;
        --help)
            echo "Vocalinux Installer"
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --dev            Install in development mode with all dev dependencies"
            echo "  --test           Run tests after installation"
            echo "  --venv-dir=PATH  Specify custom virtual environment directory (default: venv)"
            echo "  --skip-models    Skip downloading VOSK models during installation"
            echo "  --with-whisper   Install Whisper AI support with GPU/CUDA (included by default)"
            echo "  --whisper-cpu    Install Whisper with CPU-only PyTorch (smaller download, works on low-RAM)"
            echo "  --no-whisper     VOSK-only install (skips Whisper entirely, uses VOSK as default)"
            echo "  --tag=TAG        Install specific release tag (default: v0.3.0-alpha)"
            echo "  -y, --yes        Non-interactive mode (accept defaults)"
            echo "  --help           Show this help message"
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

    # Define package names for different distributions
    local APT_PACKAGES="python3-pip python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-appindicator3-0.1 libgirepository1.0-dev python3-dev portaudio19-dev python3-venv wget curl unzip"
    local DNF_PACKAGES="python3-pip python3-gobject gtk3 libappindicator-gtk3 gobject-introspection-devel python3-devel portaudio-devel python3-virtualenv wget curl unzip"
    local PACMAN_PACKAGES="python-pip python-gobject gtk3 libappindicator-gtk3 gobject-introspection python-cairo portaudio python-virtualenv wget curl unzip"
    local ZYPPER_PACKAGES="python3-pip python3-gobject python3-gobject-cairo gtk3 libappindicator-gtk3 gobject-introspection-devel python3-devel portaudio-devel python3-virtualenv wget curl unzip"

    local MISSING_PACKAGES=""
    local INSTALL_CMD=""
    local UPDATE_CMD=""

    case "$DISTRO_FAMILY" in
        ubuntu|debian)
            # Check for missing packages
            for pkg in $APT_PACKAGES; do
                if ! apt_package_installed "$pkg"; then
                    MISSING_PACKAGES="$MISSING_PACKAGES $pkg"
                fi
            done

            if [ -n "$MISSING_PACKAGES" ]; then
                print_info "Installing missing packages:$MISSING_PACKAGES"
                sudo apt update || { print_error "Failed to update package lists"; exit 1; }

                # Handle appindicator package: old package was deprecated in Debian 13+
                # Try the old package first, fall back to gir1.2-ayatanaappindicator3-0.1 if unavailable
                if echo "$MISSING_PACKAGES" | grep -q "gir1.2-appindicator3-0.1"; then
                    # Remove appindicator from the package list for special handling
                    FILTERED_PACKAGES=$(echo "$MISSING_PACKAGES" | sed 's/gir1.2-appindicator3-0.1//' | xargs)

                    # Try to install the old package first (for older Debian/Ubuntu versions)
                    if ! sudo apt install -y gir1.2-appindicator3-0.1 2>/dev/null; then
                        print_info "gir1.2-appindicator3-0.1 not available, trying gir1.2-ayatanaappindicator3-0.1..."
                        if ! sudo apt install -y gir1.2-ayatanaappindicator3-0.1; then
                            print_error "Failed to install appindicator package (tried both gir1.2-appindicator3-0.1 and gir1.2-ayatanaappindicator3-0.1)"
                            exit 1
                        fi
                        print_info "Successfully installed gir1.2-ayatanaappindicator3-0.1 (modern replacement)"
                    fi

                    # Install remaining packages
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

        *)
            print_error "Unsupported distribution family: $DISTRO_FAMILY"
            print_warning "Please install the following dependencies manually:"
            print_warning "- Python 3.8 or newer with pip"
            print_warning "- PyGObject (GTK3 bindings for Python)"
            print_warning "- GTK3 development libraries"
            print_warning "- AppIndicator3 support"
            print_warning "- PortAudio development libraries"
            print_warning "- Python virtual environment support"
            if [[ "$NON_INTERACTIVE" != "yes" ]]; then
                read -p "Press Enter to continue once dependencies are installed, or Ctrl+C to cancel..."
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
                *)
                    print_warning "Unsupported distribution for Wayland text input tools."
                    print_warning "Please install 'wtype' manually for Wayland text input support."
                    ;;
            esac
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
                fedora)
                    if command_exists dnf; then
                        sudo dnf install -y xdotool wtype || { print_warning "Failed to install text input tools. Text injection may not work properly."; }
                    elif command_exists yum; then
                        sudo yum install -y xdotool wtype || { print_warning "Failed to install text input tools. Text injection may not work properly."; }
                    fi
                    ;;
                arch)
                    sudo pacman -S --noconfirm xdotool wtype || { print_warning "Failed to install text input tools. Text injection may not work properly."; }
                    ;;
                suse)
                    sudo zypper install -y xdotool wtype || { print_warning "Failed to install text input tools. Text injection may not work properly."; }
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
    # Note: We don't use --system-site-packages to avoid conflicts with system packages
    # that may be incompatible with Python 3.12+ (e.g., old coverage versions)
    python3 -m venv "$VENV_DIR" || {
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

    # Function to verify package installation
    verify_package_installed() {
        local PKG_NAME="vocalinux"
        # Use venv python and set GI_TYPELIB_PATH for PyGObject
        GI_TYPELIB_PATH=/usr/lib/girepository-1.0 "$VENV_DIR/bin/python" -c "import $PKG_NAME" 2>/dev/null
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

        # Install the package with logging
        pip install . --log "$PIP_LOG_FILE" || {
            print_error "Failed to install Vocalinux."
            print_error "Check the pip log for details: $PIP_LOG_FILE"
            return 1
        }

        # Whisper installation logic:
        # - Default (non-interactive via curl|bash): Install Whisper
        # - --no-whisper flag: Skip Whisper, create config with VOSK as default
        # - Interactive mode: Prompt user
        if [ "$NO_WHISPER_EXPLICIT" = "yes" ]; then
            # User explicitly requested --no-whisper (for low-RAM systems)
            print_info "Skipping Whisper installation (--no-whisper flag)."
            print_info "VOSK will be used as the default speech recognition engine."

            # Create config file with VOSK as default engine
            local CONFIG_FILE="$CONFIG_DIR/config.json"
            if [ ! -f "$CONFIG_FILE" ]; then
                print_info "Creating config with VOSK as default engine..."
                cat > "$CONFIG_FILE" << 'VOSK_CONFIG'
{
    "speech_recognition": {
        "engine": "vosk",
        "model_size": "small",
        "vosk_model_size": "small",
        "whisper_model_size": "tiny",
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
        elif [ "$WHISPER_CPU" = "yes" ]; then
            # CPU-only Whisper installation (smaller download, works on low-RAM systems)
            print_info "Installing Whisper AI with CPU-only PyTorch (~200MB instead of ~2.3GB)..."
            print_info "This is ideal for systems without NVIDIA GPU or with limited RAM."

            # Install CPU-only PyTorch first
            pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu --log "$PIP_LOG_FILE" || {
                print_warning "Failed to install CPU-only PyTorch."
                print_warning "Voice recognition will fall back to VOSK."
            }

            # Install openai-whisper (without its torch dependency since we already installed it)
            pip install openai-whisper --log "$PIP_LOG_FILE" || {
                print_warning "Failed to install Whisper."
                print_warning "Voice recognition will fall back to VOSK."
            }
        elif [ "$WITH_WHISPER" = "yes" ] || [ "$NON_INTERACTIVE" = "yes" ]; then
            # Default: Install Whisper with GPU support (either explicitly requested or non-interactive default)
            print_info "Installing Whisper AI support with GPU/CUDA (~2.3GB download, ~5-10 min)..."
            print_info "This enables high-accuracy speech recognition with GPU acceleration."
            print_info "Tip: Use --whisper-cpu for a smaller download if you don't have an NVIDIA GPU."
            pip install ".[whisper]" --log "$PIP_LOG_FILE" || {
                print_warning "Failed to install Whisper support."
                print_warning "Voice recognition will fall back to VOSK."
            }
        else
            # Interactive mode: Prompt user
            echo ""
            print_info "Whisper AI provides better accuracy but requires more disk space."
            print_info "Options:"
            print_info "  1) Full install with GPU support (~2.3GB) - best if you have NVIDIA GPU"
            print_info "  2) CPU-only install (~200MB) - works on any system, slightly slower"
            print_info "  3) Skip Whisper - use VOSK only"
            read -p "Choose option [1/2/3]: " -n 1 -r
            echo
            if [[ $REPLY == "1" ]]; then
                print_info "Installing Whisper with GPU support (this might take a while)..."
                pip install ".[whisper]" --log "$PIP_LOG_FILE" || {
                    print_warning "Failed to install Whisper support."
                    print_warning "Voice recognition will fall back to VOSK."
                }
            elif [[ $REPLY == "2" ]]; then
                print_info "Installing Whisper with CPU-only PyTorch..."
                pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu --log "$PIP_LOG_FILE" || {
                    print_warning "Failed to install CPU-only PyTorch."
                }
                pip install openai-whisper --log "$PIP_LOG_FILE" || {
                    print_warning "Failed to install Whisper."
                    print_warning "Voice recognition will fall back to VOSK."
                }
            fi
        fi
    fi

    # Verify installation
    if verify_package_installed; then
        print_success "Vocalinux package installed successfully!"
        # Clean up log file if installation was successful
        rm -rf "$PIP_LOG_DIR"

        # Create wrapper scripts in ~/.local/bin for easy access
        mkdir -p "$HOME/.local/bin"

        # Create vocalinux wrapper script
        cat > "$HOME/.local/bin/vocalinux" << WRAPPER_EOF
#!/bin/bash
# Wrapper script for Vocalinux that sets required environment variables
export GI_TYPELIB_PATH=/usr/lib/girepository-1.0
exec "$VENV_DIR/bin/vocalinux" "\$@"
WRAPPER_EOF
        chmod +x "$HOME/.local/bin/vocalinux"
        print_info "Created wrapper: ~/.local/bin/vocalinux"

        # Create vocalinux-gui wrapper script
        cat > "$HOME/.local/bin/vocalinux-gui" << WRAPPER_EOF
#!/bin/bash
# Wrapper script for Vocalinux GUI that sets required environment variables
export GI_TYPELIB_PATH=/usr/lib/girepository-1.0
exec "$VENV_DIR/bin/vocalinux-gui" "\$@"
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
        sed -i "s|^Exec=vocalinux|Exec=env GI_TYPELIB_PATH=/usr/lib/girepository-1.0 $WRAPPER_SCRIPT|" "$DESKTOP_DIR/vocalinux.desktop" || {
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

# Function to update icon cache
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
}

# Install desktop entry
install_desktop_entry || print_warning "Desktop entry installation failed"

# Install icons
install_icons || print_warning "Icon installation failed"

# Install Whisper tiny model (if Whisper was installed)
if [ "$WITH_WHISPER" = "yes" ] || [ "$NON_INTERACTIVE" = "yes" ]; then
    # Check if Whisper is actually installed before downloading model
    if python -c "import whisper" 2>/dev/null; then
        if [ "$SKIP_MODELS" = "no" ]; then
            install_whisper_model || print_warning "Whisper model download failed - model will be downloaded on first run"
        else
            print_info "Skipping Whisper model download (--skip-models specified)"
        fi
    else
        print_info "Whisper not available, skipping model download"
    fi
fi

# Install VOSK models (as fallback)
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

    # Check if pytest is installed
    if ! python -c "import pytest" &>/dev/null; then
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

    # Check if Python package is importable
    if ! python -c "import vocalinux" &>/dev/null; then
        print_error "Vocalinux Python package cannot be imported."
        ((ISSUES++))
    fi

    # Return the number of issues found
    return $ISSUES
}

# Function to print installation summary
print_installation_summary() {
    local ISSUES=$1

    echo
    echo "=============================="
    echo "   INSTALLATION SUMMARY"
    echo "=============================="
    echo

    if [ "$ISSUES" -eq 0 ]; then
        print_success "Installation completed successfully with no issues!"
    else
        print_warning "Installation completed with $ISSUES potential issue(s)."
        print_warning "The application may still work, but some features might be limited."
    fi

    echo
    print_info "Installation details:"
    print_info "- Virtual environment: $VENV_DIR"
    print_info "- Desktop entry: $DESKTOP_DIR/vocalinux.desktop"
    print_info "- Icons: $ICON_DIR"
    print_info "- Configuration: $CONFIG_DIR"
    print_info "- Data directory: $DATA_DIR"

    # Check if Whisper model was installed
    if [ -f "$DATA_DIR/models/whisper/tiny.pt" ]; then
        print_info "- Whisper tiny model: $DATA_DIR/models/whisper/tiny.pt (default engine)"
    elif python -c "import whisper" 2>/dev/null; then
        print_info "- Whisper tiny model: Will be downloaded on first run"
    fi

    # Check if VOSK model was installed
    if [ "$SKIP_MODELS" = "no" ] && [ -d "$DATA_DIR/models/vosk-model-small-en-us-0.15" ]; then
        print_info "- VOSK small model: $DATA_DIR/models/vosk-model-small-en-us-0.15 (fallback)"
    elif [ "$SKIP_MODELS" = "yes" ]; then
        print_info "- VOSK models: Will be downloaded on first run (--skip-models used)"
    else
        print_info "- VOSK models: Will be downloaded on first run (installation failed)"
    fi

    echo
    print_info "To activate the virtual environment in the future, run:"
    print_info "  source $ACTIVATION_SCRIPT"
    print_info "You can then launch Vocalinux by running 'vocalinux'"

    # If venv is in a standard location, mention direct launch option
    if [[ "$VENV_DIR" == "$HOME/.local/share/vocalinux/venv" ]]; then
        echo
        print_info "Or run directly with:"
        print_info "  $VENV_DIR/bin/vocalinux"
    fi

    echo
    print_info "For more information, see: https://github.com/jatinkrmalik/vocalinux"

    if [ "$ISSUES" -gt 0 ]; then
        echo
        print_warning "If you encounter any problems, please report them at:"
        print_warning "https://github.com/jatinkrmalik/vocalinux/issues"
    fi
}

# Verify the installation
verify_installation
INSTALL_ISSUES=$?

# Print installation summary
print_installation_summary $INSTALL_ISSUES

print_success "Installation process completed!"
