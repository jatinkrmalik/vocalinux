# Check Python version
check_python_version() {
    local MIN_VERSION="3.9"
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
        print_warning "python3 -m venv failed, trying python3 -m virtualenv..."
        python3 -m virtualenv --system-site-packages "$VENV_DIR" || {
            print_error "Failed to create virtual environment. Please check your Python installation."
            exit 1
        }
    }

    # Activate virtual environment
    source "$VENV_DIR/bin/activate" || { print_error "Failed to activate virtual environment"; exit 1; }

    # Update pip and setuptools
    print_info "Updating pip, setuptools, and wheel..."
    pip install --upgrade pip setuptools wheel || { print_error "Failed to update pip, setuptools, and wheel"; exit 1; }

    print_info "Virtual environment activated successfully."
}

# Create activation script for users
# Put it in ~/.local/bin when running remotely, or current dir when running locally
create_activation_script() {
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
export PYTHONNOUSERSITE=1
source "$VENV_DIR/bin/activate"
echo "Vocalinux virtual environment activated."
echo "To start the application, run: vocalinux"
EOF
    chmod +x "$ACTIVATION_SCRIPT"
    print_info "Created activation script: $ACTIVATION_SCRIPT"
}
