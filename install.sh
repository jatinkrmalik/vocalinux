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
        --help)
            echo "Vocalinux Installer"
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --dev            Install in development mode with all dev dependencies"
            echo "  --test           Run tests after installation"
            echo "  --venv-dir=PATH  Specify custom virtual environment directory (default: venv)"
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
print_info "Using virtual environment: $VENV_DIR"
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
    gir1.2-appindicator3-0.1 libgirepository1.0-dev python3-dev portaudio19-dev python3-venv

# Define XDG directories
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/vocalinux"
DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/vocalinux"
DESKTOP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
ICON_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor/scalable/apps"

# Detect desktop environment for text input tools
if [ "$XDG_SESSION_TYPE" = "wayland" ]; then
    print_info "Detected Wayland session, installing wtype..."
    sudo apt install -y wtype
else
    print_info "Detected X11 session, installing xdotool..."
    sudo apt install -y xdotool
fi

# Create necessary directories
print_info "Creating application directories..."
mkdir -p "$CONFIG_DIR"
mkdir -p "$DATA_DIR/models"
mkdir -p "$DESKTOP_DIR"
mkdir -p "$ICON_DIR"

# Set up virtual environment 
print_info "Setting up Python virtual environment..."
python3 -m venv "$VENV_DIR" --system-site-packages

# Activate virtual environment
source "$VENV_DIR/bin/activate"

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

# Install Python package
if [[ "$DEV_MODE" == "yes" ]]; then
    print_info "Installing Vocalinux in development mode..."
    pip install -e .
    pip install pytest pytest-mock pytest-cov
    # Install all optional dependencies for development
    print_info "Installing all optional dependencies for development..."
    pip install ".[whisper,dev]"
else
    print_info "Installing Vocalinux..."
    pip install .
    
    # Prompt for Whisper installation
    read -p "Do you want to install Whisper AI support? This requires additional disk space. (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Installing Whisper support (this might take a while)..."
        pip install ".[whisper]"
    fi
fi

# Install desktop entry
print_info "Installing desktop entry..."
cp vocalinux.desktop "$DESKTOP_DIR/"

# Update the desktop entry to use the venv
VENV_SCRIPT_PATH="$(realpath $VENV_DIR/bin/vocalinux)"
sed -i "s|^Exec=vocalinux|Exec=$VENV_SCRIPT_PATH|" "$DESKTOP_DIR/vocalinux.desktop"
print_info "Updated desktop entry to use virtual environment"

# Install icons
print_info "Installing application icons..."
if [ -d "resources/icons/scalable" ]; then
    cp resources/icons/scalable/vocalinux.svg "$ICON_DIR/"
    cp resources/icons/scalable/vocalinux-microphone.svg "$ICON_DIR/"
    cp resources/icons/scalable/vocalinux-microphone-off.svg "$ICON_DIR/"
    cp resources/icons/scalable/vocalinux-microphone-process.svg "$ICON_DIR/"
    print_info "Installed custom Vocalinux icons"
else
    print_warning "Custom icons not found in resources/icons/scalable directory"
fi

# Update icon cache to make the icons available immediately
gtk-update-icon-cache -f -t "${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor" 2>/dev/null || true

# Run tests if requested
if [[ "$RUN_TESTS" == "yes" ]]; then
    print_info "Running tests..."
    # Install pytest if not already installed
    pip install pytest pytest-mock pytest-cov
    
    # Run the tests with pytest
    pytest
    if [ $? -eq 0 ]; then
        print_success "All tests passed!"
    else
        print_error "Some tests failed!"
    fi
fi

print_success "Installation complete!"
print_info "To activate the virtual environment in the future, run:"
print_info "  source activate-vocalinux.sh"
print_info "You can then launch Vocalinux by running 'vocalinux'"

echo
print_info "For more information, see the documentation in the docs/ directory."
