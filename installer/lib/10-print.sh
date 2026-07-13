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

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

is_kde_plasma_session() {
    local desktop="${XDG_CURRENT_DESKTOP:-} ${DESKTOP_SESSION:-} ${GDMSESSION:-}"
    local kde_session="${KDE_FULL_SESSION:-}"
    local desktop_lower="${desktop,,}"
    local kde_session_lower="${kde_session,,}"

    [[ "$desktop_lower" == *kde* || "$desktop_lower" == *plasma* || "$kde_session_lower" == "true" ]]
}

print_kde_wayland_ibus_hint() {
    print_warning "KDE Plasma Wayland detected."
    print_info "For direct dictation into apps, open System Settings -> Keyboard -> Virtual Keyboard and select 'IBus Wayland'."
    print_info "After changing it, restart Vocalinux or log out and back in."
}

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
