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
USE_VENV="no"
RUN_TESTS="no"
DEV_MODE="no"

while [[ $# -gt 0 ]]; do
    case $1 in
        --dev)
            DEV_MODE="yes"
            shift
            ;;
        --venv)
            USE_VENV="yes"
            shift
            ;;
        --test)
            RUN_TESTS="yes"
            shift
            ;;
        --help)
            echo "Vocalinux Installer"
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --dev      Install in development mode with all dev dependencies"
            echo "  --venv     Use virtual environment instead of system-wide installation"
            echo "  --test     Run tests after installation"
            echo "  --help     Show this help message"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help to see available options"
            exit 1
            ;;
    esac
done

# If dev mode is enabled, automatically use venv and run tests
if [[ "$DEV_MODE" == "yes" ]]; then
    USE_VENV="yes"
    RUN_TESTS="yes"
fi

print_info "Vocalinux Installer"
print_info "=============================="
echo ""
[[ "$USE_VENV" == "yes" ]] && print_info "Using virtual environment mode"
[[ "$DEV_MODE" == "yes" ]] && print_info "Installing in development mode"
[[ "$RUN_TESTS" == "yes" ]] && print_info "Tests will be run after installation"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_error "Please do not run this script as root or with sudo."
    exit 1
fi

# Check Ubuntu version
if [ -f /etc/os-release ]; then
    . /etc/os-release
    if [[ "$NAME" != *"Ubuntu"* ]]; then
        print_warning "This installer is designed for Ubuntu. Your system: $NAME"
        echo "The application may still work, but you might need to install dependencies manually."
        read -p "Do you want to continue anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        print_info "Detected Ubuntu $VERSION_ID"
    fi
fi

# Install system dependencies
print_info "Installing system dependencies..."
sudo apt update
sudo apt install -y python3-pip python3-gi python3-gi-cairo gir1.2-gtk-3.0 \
    gir1.2-appindicator3-0.1 libgirepository1.0-dev python3-dev portaudio19-dev

# Install venv if needed
if [[ "$USE_VENV" == "yes" ]]; then
    print_info "Installing Python virtual environment..."
    sudo apt install -y python3-venv
fi

# Detect desktop environment
if [ "$XDG_SESSION_TYPE" = "wayland" ]; then
    print_info "Detected Wayland session, installing wtype..."
    sudo apt install -y wtype
else
    print_info "Detected X11 session, installing xdotool..."
    sudo apt install -y xdotool
fi

# Create directories
print_info "Creating application directories..."
mkdir -p ~/.local/share/vocalinux/icons
mkdir -p ~/.local/share/vocalinux/models
mkdir -p ~/.config/vocalinux

# Set up virtual environment if requested
VENV_DIR="venv"
if [[ "$USE_VENV" == "yes" ]]; then
    print_info "Setting up Python virtual environment..."
    python3 -m venv $VENV_DIR --system-site-packages

    # Activate virtual environment
    source $VENV_DIR/bin/activate

    # Update pip and setuptools
    pip install --upgrade pip setuptools wheel

    print_info "Virtual environment activated."

    # Create activation script for users
    cat > activate-vocalinux.sh << EOF
#!/bin/bash
# This script activates the Vocalinux virtual environment
source "\$(dirname "\$(realpath "\$0")")/$VENV_DIR/bin/activate"
echo "Vocalinux virtual environment activated."
echo "To start the application, run: vocalinux"
EOF
    chmod +x activate-vocalinux.sh
    print_info "Created activation script: activate-vocalinux.sh"
fi

# Modify setup.py to exclude PyGObject when installing in a venv
if [[ "$USE_VENV" == "yes" ]]; then
    print_info "Using system PyGObject for virtual environment..."
    # Create a temporary modified setup.py file that excludes PyGObject
    SETUP_BACKUP="setup.py.bak"
    cp setup.py $SETUP_BACKUP
    # Remove PyGObject from install_requires
    sed -i 's/"PyGObject",  # For GTK UI/"# PyGObject is provided by system packages",/g' setup.py
fi

# Install Python package
if [[ "$DEV_MODE" == "yes" ]]; then
    print_info "Installing Vocalinux in development mode..."
    if [[ "$USE_VENV" == "yes" ]]; then
        pip install -e .
        pip install pytest pytest-mock pytest-cov pynput
    else
        pip3 install --user -e .
        pip3 install --user pytest pytest-mock pytest-cov pynput
    fi
else
    print_info "Installing Vocalinux Python package..."
    if [[ "$USE_VENV" == "yes" ]]; then
        pip install .
    else
        pip3 install --user .
    fi
fi

# Restore original setup.py if it was modified
if [[ "$USE_VENV" == "yes" && -f "$SETUP_BACKUP" ]]; then
    mv $SETUP_BACKUP setup.py
fi

# Install optional Whisper support
if [[ "$DEV_MODE" != "yes" ]]; then
    read -p "Do you want to install Whisper AI support? This requires additional disk space. (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Installing Whisper support (this might take a while)..."
        if [[ "$USE_VENV" == "yes" ]]; then
            pip install ".[whisper]"
        else
            pip3 install --user ".[whisper]"
        fi
    fi
else
    # In dev mode, install all optional dependencies
    print_info "Installing all optional dependencies for development..."
    if [[ "$USE_VENV" == "yes" ]]; then
        pip install ".[whisper,dev]"
    else
        pip3 install --user ".[whisper,dev]"
    fi
fi

# Install desktop entry
print_info "Installing desktop entry..."
mkdir -p ~/.local/share/applications
cp vocalinux.desktop ~/.local/share/applications/

# If using virtual environment, modify the desktop entry to use the venv
if [[ "$USE_VENV" == "yes" ]]; then
    VENV_SCRIPT_PATH="$(realpath $VENV_DIR/bin/vocalinux)"
    sed -i "s|^Exec=vocalinux|Exec=$VENV_SCRIPT_PATH|" ~/.local/share/applications/vocalinux.desktop
    print_info "Updated desktop entry to use virtual environment"
fi

# TODO: Install icons
print_info "Installing application icons..."
# Future: Copy SVG icons to ~/.local/share/icons/hicolor/scalable/apps/

# Run tests if requested
if [[ "$RUN_TESTS" == "yes" ]]; then
    print_info "Running tests..."
    python3 tests/run_basic_tests.py
    if [ $? -eq 0 ]; then
        print_success "All tests passed!"
    else
        print_error "Some tests failed!"
    fi
fi

print_success "Installation complete!"

if [[ "$USE_VENV" == "yes" ]]; then
    print_info "To activate the virtual environment in the future, run:"
    print_info "  source activate-vocalinux.sh"
    print_info "You can then launch Vocalinux by running 'vocalinux'"
else
    print_info "You can now launch Vocalinux from your application menu"
    print_info "or by running 'vocalinux' in a terminal."
fi

echo
print_info "For more information, see the documentation in the docs/ directory."
