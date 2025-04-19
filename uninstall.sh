#!/bin/bash
# Vocalinux Uninstaller
# This script removes Vocalinux and cleans up the environment

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

print_info "Vocalinux Uninstaller"
print_info "=============================="
echo ""

# Define XDG directories
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/vocalinux"
DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/vocalinux"
DESKTOP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
ICON_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor/scalable/apps"

# Ask for confirmation
read -p "This will completely remove Vocalinux and all its data. Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_info "Uninstallation cancelled."
    exit 0
fi

# Remove virtual environment (if exists)
if [ -d "venv" ]; then
    print_info "Removing virtual environment..."
    rm -rf venv
fi

# Remove activation script
if [ -f "activate-vocalinux.sh" ]; then
    print_info "Removing activation script..."
    rm activate-vocalinux.sh
fi

# Remove application configuration and data
if [ -d "$CONFIG_DIR" ]; then
    print_info "Removing configuration directory..."
    rm -rf "$CONFIG_DIR"
fi

if [ -d "$DATA_DIR" ]; then
    print_info "Removing application data directory..."
    rm -rf "$DATA_DIR"
fi

# Remove desktop entry
if [ -f "$DESKTOP_DIR/vocalinux.desktop" ]; then
    print_info "Removing desktop entry..."
    rm "$DESKTOP_DIR/vocalinux.desktop"
fi

# Remove icons
print_info "Removing application icons..."
rm -f "$ICON_DIR/vocalinux.svg"
rm -f "$ICON_DIR/vocalinux-microphone.svg"
rm -f "$ICON_DIR/vocalinux-microphone-off.svg"
rm -f "$ICON_DIR/vocalinux-microphone-process.svg"

# Update icon cache
gtk-update-icon-cache -f -t "${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor" 2>/dev/null || true

# Remove Python package build directories
print_info "Removing build directories..."
rm -rf build/ dist/ *.egg-info/
find src -name "*.egg-info" -type d -exec rm -rf {} +
find src -name "__pycache__" -type d -exec rm -rf {} +

# Clean up any temporary or generated files
print_info "Cleaning up temporary files..."
find . -name "*.pyc" -delete
find . -name "*.pyo" -delete
find . -name "__pycache__" -type d -exec rm -rf {} +
find . -name ".pytest_cache" -type d -exec rm -rf {} +
find . -name ".coverage" -delete

# Remove wrapper script if it exists
if [ -f "vocalinux-run.py" ]; then
    print_info "Removing wrapper script..."
    rm vocalinux-run.py
fi

print_success "Uninstallation complete!"
print_info "Your system has been cleaned up and is ready for a fresh installation."
