#!/bin/bash
# Vocalinux Uninstaller
# This script removes Vocalinux and cleans up the environment

# Don't exit on error to allow for more robust cleanup
# set -e

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

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to safely remove a file or directory
safe_remove() {
    local path="$1"
    local description="$2"
    
    if [ -e "$path" ]; then
        print_info "Removing $description: $path"
        rm -rf "$path" && {
            print_success "Successfully removed $description"
            return 0
        } || {
            print_error "Failed to remove $description: $path"
            return 1
        }
    else
        print_info "$description not found: $path"
        return 0
    fi
}

print_info "Vocalinux Uninstaller"
print_info "=============================="
echo ""

# Parse command line arguments
KEEP_CONFIG="no"
KEEP_DATA="no"
VENV_DIR="venv"

while [[ $# -gt 0 ]]; do
    case $1 in
        --keep-config)
            KEEP_CONFIG="yes"
            shift
            ;;
        --keep-data)
            KEEP_DATA="yes"
            shift
            ;;
        --venv-dir=*)
            VENV_DIR="${1#*=}"
            shift
            ;;
        --help)
            echo "Vocalinux Uninstaller"
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --keep-config     Keep configuration files"
            echo "  --keep-data       Keep application data (models, etc.)"
            echo "  --venv-dir=PATH   Specify custom virtual environment directory (default: venv)"
            echo "  --help            Show this help message"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help to see available options"
            exit 1
            ;;
    esac
done

# Define XDG directories
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/vocalinux"
DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/vocalinux"
DESKTOP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
ICON_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor/scalable/apps"

# Print uninstallation options
echo "Uninstallation options:"
echo "- Virtual environment directory: $VENV_DIR"
[[ "$KEEP_CONFIG" == "yes" ]] && echo "- Keeping configuration files"
[[ "$KEEP_DATA" == "yes" ]] && echo "- Keeping application data"
echo

# Ask for confirmation
read -p "This will remove Vocalinux from your system. Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_info "Uninstallation cancelled."
    exit 0
fi

# Function to handle virtual environment removal
remove_virtual_environment() {
    if [ -d "$VENV_DIR" ]; then
        print_info "Removing virtual environment..."
        
        # Deactivate the virtual environment if it's active
        if [[ -n "$VIRTUAL_ENV" && "$VIRTUAL_ENV" == *"$VENV_DIR"* ]]; then
            print_warning "Virtual environment is active. Deactivating..."
            deactivate 2>/dev/null || {
                print_warning "Failed to deactivate virtual environment. This is not critical."
            }
        fi
        
        # Remove the virtual environment directory
        safe_remove "$VENV_DIR" "virtual environment directory"
    else
        print_info "Virtual environment not found: $VENV_DIR"
    fi
}

# Function to remove application files
remove_application_files() {
    # Remove activation script
    safe_remove "activate-vocalinux.sh" "activation script"
    
    # Remove desktop entry
    safe_remove "$DESKTOP_DIR/vocalinux.desktop" "desktop entry"
    
    # Remove icons
    print_info "Removing application icons..."
    local ICONS=(
        "vocalinux.svg"
        "vocalinux-microphone.svg"
        "vocalinux-microphone-off.svg"
        "vocalinux-microphone-process.svg"
    )
    
    for icon in "${ICONS[@]}"; do
        safe_remove "$ICON_DIR/$icon" "icon"
    done
    
    # Update icon cache
    if command_exists gtk-update-icon-cache; then
        print_info "Updating icon cache..."
        gtk-update-icon-cache -f -t "${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor" 2>/dev/null || {
            print_warning "Failed to update icon cache. This is not critical."
        }
    fi
}

# Function to remove configuration and data
remove_config_and_data() {
    # Remove configuration if not keeping it
    if [[ "$KEEP_CONFIG" != "yes" ]]; then
        safe_remove "$CONFIG_DIR" "configuration directory"
    else
        print_info "Keeping configuration directory as requested: $CONFIG_DIR"
    fi
    
    # Remove data if not keeping it
    if [[ "$KEEP_DATA" != "yes" ]]; then
        safe_remove "$DATA_DIR" "application data directory"
    else
        print_info "Keeping application data directory as requested: $DATA_DIR"
    fi
}

# Function to clean up build artifacts
cleanup_build_artifacts() {
    print_info "Cleaning up build artifacts..."
    
    # Remove Python package build directories
    safe_remove "build/" "build directory"
    safe_remove "dist/" "distribution directory"
    safe_remove "*.egg-info/" "egg-info directory"
    
    # Find and remove egg-info directories in src
    find src -name "*.egg-info" -type d -exec rm -rf {} \; 2>/dev/null || {
        print_warning "Failed to remove some egg-info directories."
    }
    
    # Find and remove __pycache__ directories
    find . -name "__pycache__" -type d -exec rm -rf {} \; 2>/dev/null || {
        print_warning "Failed to remove some __pycache__ directories."
    }
    
    # Clean up any temporary or generated files
    print_info "Cleaning up temporary files..."
    find . -name "*.pyc" -delete 2>/dev/null
    find . -name "*.pyo" -delete 2>/dev/null
    find . -name ".pytest_cache" -type d -exec rm -rf {} \; 2>/dev/null
    find . -name ".coverage" -delete 2>/dev/null
    
    # Remove wrapper script if it exists
    safe_remove "vocalinux-run.py" "wrapper script"
}

# Function to verify uninstallation
verify_uninstallation() {
    print_info "Verifying uninstallation..."
    local ISSUES=0
    
    # Check if virtual environment still exists
    if [ -d "$VENV_DIR" ]; then
        print_warning "Virtual environment still exists: $VENV_DIR"
        ((ISSUES++))
    fi
    
    # Check if desktop entry still exists
    if [ -f "$DESKTOP_DIR/vocalinux.desktop" ]; then
        print_warning "Desktop entry still exists: $DESKTOP_DIR/vocalinux.desktop"
        ((ISSUES++))
    fi
    
    # Check if any icons still exist
    local ICON_COUNT=0
    for icon in vocalinux.svg vocalinux-microphone.svg vocalinux-microphone-off.svg vocalinux-microphone-process.svg; do
        if [ -f "$ICON_DIR/$icon" ]; then
            ((ICON_COUNT++))
        fi
    done
    
    if [ "$ICON_COUNT" -gt 0 ]; then
        print_warning "$ICON_COUNT icons still exist in $ICON_DIR"
        ((ISSUES++))
    fi
    
    # Check if configuration still exists (only if not keeping it)
    if [[ "$KEEP_CONFIG" != "yes" && -d "$CONFIG_DIR" ]]; then
        print_warning "Configuration directory still exists: $CONFIG_DIR"
        ((ISSUES++))
    fi
    
    # Check if data still exists (only if not keeping it)
    if [[ "$KEEP_DATA" != "yes" && -d "$DATA_DIR" ]]; then
        print_warning "Application data directory still exists: $DATA_DIR"
        ((ISSUES++))
    fi
    
    # Return the number of issues found
    return $ISSUES
}

# Function to print uninstallation summary
print_uninstallation_summary() {
    local ISSUES=$1
    
    echo
    echo "=============================="
    echo "   UNINSTALLATION SUMMARY"
    echo "=============================="
    echo
    
    if [ "$ISSUES" -eq 0 ]; then
        print_success "Uninstallation completed successfully with no issues!"
    else
        print_warning "Uninstallation completed with $ISSUES potential issue(s)."
        print_warning "Some files or directories may still exist."
    fi
    
    echo
    if [[ "$KEEP_CONFIG" == "yes" ]]; then
        print_info "Configuration directory was kept: $CONFIG_DIR"
    fi
    
    if [[ "$KEEP_DATA" == "yes" ]]; then
        print_info "Application data directory was kept: $DATA_DIR"
    fi
    
    echo
    print_info "Your system has been cleaned up and is ready for a fresh installation."
    
    if [ "$ISSUES" -gt 0 ]; then
        echo
        print_warning "If you encounter any problems, please report them at:"
        print_warning "https://github.com/jatinkrmalik/vocalinux/issues"
    fi
}

# Perform uninstallation steps
remove_virtual_environment
remove_application_files
remove_config_and_data
cleanup_build_artifacts

# Verify uninstallation
verify_uninstallation
UNINSTALL_ISSUES=$?

# Print uninstallation summary
print_uninstallation_summary $UNINSTALL_ISSUES

print_success "Uninstallation process completed!"
