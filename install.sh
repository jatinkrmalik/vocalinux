#!/bin/bash
# Ubuntu Voice Typing Installer
# This script installs the Ubuntu Voice Typing application and its dependencies

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

print_info "Ubuntu Voice Typing Installer"
print_info "=============================="
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
        print_error "This installer is designed for Ubuntu. Your system: $NAME"
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
sudo apt install -y python3-pip python3-gi gir1.2-appindicator3-0.1 python3-dev portaudio19-dev

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
mkdir -p ~/.local/share/ubuntu-voice-typing/icons
mkdir -p ~/.local/share/ubuntu-voice-typing/models
mkdir -p ~/.config/ubuntu-voice-typing

# Install Python package
print_info "Installing Ubuntu Voice Typing Python package..."
pip3 install --user .

# Install optional Whisper support
read -p "Do you want to install Whisper AI support? This requires additional disk space. (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_info "Installing Whisper support (this might take a while)..."
    pip3 install --user ".[whisper]"
fi

# Install desktop entry
print_info "Installing desktop entry..."
mkdir -p ~/.local/share/applications
cp ubuntu-voice-typing.desktop ~/.local/share/applications/

# TODO: Install icons
print_info "Installing application icons..."
# Future: Copy SVG icons to ~/.local/share/icons/hicolor/scalable/apps/

print_success "Installation complete!"
print_info "You can now launch Ubuntu Voice Typing from your application menu"
print_info "or by running 'ubuntu-voice-typing' in a terminal."
echo
print_info "For more information, see the documentation in the docs/ directory."