# Define XDG directories
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/vocalinux"
DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/vocalinux"
DESKTOP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
ICON_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor/scalable/apps"

# Function to detect and install text input tools
install_text_input_tools() {
    if [[ "$SKIP_SYSTEM_DEPS" == "yes" ]]; then
        print_warning "Skipping text input tool installation (--skip-system-deps specified)."
        return 0
    fi

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
    if [[ "$SESSION_TYPE" == "wayland" ]] && is_kde_plasma_session; then
        print_kde_wayland_ibus_hint
    fi

    # Install appropriate tools based on session type and distribution
    case "$SESSION_TYPE" in
        wayland)
            print_info "Installing Wayland text input tools..."
            case "$DISTRO_FAMILY" in
                ubuntu|debian)
                    if ! apt_package_installed "wtype"; then
                        DEBIAN_FRONTEND=noninteractive sudo apt install -y wtype || { print_warning "Failed to install wtype. Text injection may not work properly."; }
                    else
                        print_info "wtype is already installed."
                    fi
                    ;;
                fedora)
                    if command_exists dnf && ! rpm_package_installed "wtype"; then
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
                    if ! xbps-query wtype >/dev/null 2>&1; then
                        sudo xbps-install -Sy wtype || { print_warning "Failed to install wtype. Text injection may not work properly."; }
                    else
                        print_info "wtype is already installed."
                    fi
                    ;;
                solus)
                    if ! eopkg list-installed | grep -qw wtype; then
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
                        if ! DEBIAN_FRONTEND=noninteractive sudo apt install -y ydotool 2>/dev/null; then
                            if [[ "$DISTRO_FAMILY" == "debian" ]]; then
                                print_warning "ydotool is not packaged in Debian's standard repos."
                                print_info "For full Wayland input support, you can compile ydotool from source:"
                                print_info "  sudo apt install -y git cmake libevdev-dev"
                                print_info "  git clone https://github.com/ReimuNotMoe/ydotool.git /tmp/ydotool"
                                print_info "  cmake -S /tmp/ydotool -B /tmp/ydotool/build && sudo cmake --build /tmp/ydotool/build --target install"
                                print_info "  sudo systemctl enable --now ydotoold"
                                print_info "Alternatively, wtype (already installed) will handle most Wayland compositors."
                            else
                                print_info "ydotool not available in repos (optional)"
                            fi
                        fi
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
                        DEBIAN_FRONTEND=noninteractive sudo apt install -y xdotool || { print_warning "Failed to install xdotool. Text injection may not work properly."; }
                    else
                        print_info "xdotool is already installed."
                    fi
                    ;;
                fedora)
                    if command_exists dnf && ! rpm_package_installed "xdotool"; then
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
                    if ! xbps-query xdotool >/dev/null 2>&1; then
                        sudo xbps-install -Sy xdotool || { print_warning "Failed to install xdotool. Text injection may not work properly."; }
                    else
                        print_info "xdotool is already installed."
                    fi
                    ;;
                solus)
                    if ! eopkg list-installed | grep -qw xdotool; then
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
                    DEBIAN_FRONTEND=noninteractive sudo apt install -y xdotool wtype || { print_warning "Failed to install text input tools. Text injection may not work properly."; }
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
