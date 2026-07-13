# Install git via the first available package manager (avoids re-detecting distro).
ensure_git_installed() {
    command_exists git && return 0

    print_warning "git is not installed. Attempting to install git..."

    local ok=0
    if command_exists apt; then
        sudo apt update && sudo apt install -y git && ok=1 || true
    elif command_exists dnf; then
        sudo dnf install -y git && ok=1 || true
    elif command_exists pacman; then
        sudo pacman -S --noconfirm git && ok=1 || true
    elif command_exists zypper; then
        sudo zypper install -y git && ok=1 || true
    elif command_exists emerge; then
        sudo emerge git && ok=1 || true
    elif command_exists apk; then
        sudo apk add git && ok=1 || true
    elif command_exists xbps-install; then
        sudo xbps-install -Sy git && ok=1 || true
    elif command_exists eopkg; then
        sudo eopkg install git && ok=1 || true
    elif command_exists urpmi; then
        sudo urpmi --force git && ok=1 || true
    fi

    if [ "$ok" -eq 1 ] && command_exists git; then
        print_success "git installed successfully!"
        return 0
    fi

    print_error "git is not installed and could not be installed automatically."
    print_error "Please install git manually and run the installer again:"
    print_error "  Ubuntu/Debian: sudo apt install git"
    print_error "  Fedora/RHEL: sudo dnf install git"
    print_error "  Arch: sudo pacman -S git"
    print_error "  openSUSE: sudo zypper install git"
    exit 1
}

# Returns 0 if running from within the vocalinux repo (and sets INSTALL_DIR).
# Otherwise clones the repo at INSTALL_TAG and sets INSTALL_DIR there.
# The caller is expected to call `resolve_venv_dir "$INSTALL_DIR"` afterward.
setup_install_repo() {
    # Validate that pyproject.toml/setup.py actually belongs to vocalinux
    IS_VOCALINUX_LOCAL=false
    if [ -f "pyproject.toml" ] && grep -q 'name = "vocalinux"' "pyproject.toml" 2>/dev/null; then
        IS_VOCALINUX_LOCAL=true
    elif [ -f "setup.py" ] && grep -q "vocalinux" "setup.py" 2>/dev/null; then
        IS_VOCALINUX_LOCAL=true
    fi

    if [ "$IS_VOCALINUX_LOCAL" = true ]; then
        INSTALL_DIR="$(pwd)"
        print_info "Running from local repository: $INSTALL_DIR"
        return 0
    fi

    print_info "Installing Vocalinux version: ${INSTALL_TAG}"

    # Ensure git is installed before attempting to clone
    ensure_git_installed

    IS_REMOTE_INSTALL="yes"
    INSTALL_DIR="$HOME/.local/share/vocalinux-install"
    mkdir -p "$INSTALL_DIR"

    if [ -d "$INSTALL_DIR/.git" ]; then
        print_info "Updating existing clone..."
        cd "$INSTALL_DIR"
        git fetch origin tag "$INSTALL_TAG"
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
}
