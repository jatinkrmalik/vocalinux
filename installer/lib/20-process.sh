get_vocalinux_pids() {
    pgrep -f "vocalinux" 2>/dev/null | while read -r pid; do
        [ -z "$pid" ] && continue

        if [ "$pid" = "$$" ] || [ "$pid" = "$PPID" ]; then
            continue
        fi

        local stat
        stat=$(ps -o stat= -p "$pid" 2>/dev/null | awk '{print $1}')
        if [[ "$stat" == Z* ]]; then
            continue
        fi

        local cmd
        cmd=$(ps -o args= -p "$pid" 2>/dev/null)
        if [[ "$cmd" == *"install.sh"* ]] || [[ "$cmd" == *"uninstall.sh"* ]]; then
            continue
        fi

        echo "$pid"
    done
}

check_running_processes() {
    local PIDS
    PIDS=$(get_vocalinux_pids || true)

    if [ -n "$PIDS" ]; then
        print_warning "Found running Vocalinux process(es): $PIDS"
        echo ""

        if [[ "$NON_INTERACTIVE" == "yes" ]]; then
            print_info "Non-interactive mode: stopping Vocalinux automatically..."
        else
            read -p "Vocalinux must be stopped before installation. Kill running process(es)? (Y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Nn]$ ]]; then
                print_error "Cannot proceed with installation while Vocalinux is running."
                print_info "Please stop Vocalinux manually and run the installer again."
                exit 1
            fi
        fi

        print_info "Stopping Vocalinux..."
        echo "$PIDS" | xargs -r kill -TERM 2>/dev/null || true
        sleep 2

        local REMAINING_PIDS
        REMAINING_PIDS=$(get_vocalinux_pids || true)

        if [ -n "$REMAINING_PIDS" ]; then
            print_warning "Some processes still running, forcing termination..."
            echo "$REMAINING_PIDS" | xargs -r kill -KILL 2>/dev/null || true
            sleep 1
        fi

        local FINAL_PIDS
        FINAL_PIDS=$(get_vocalinux_pids || true)
        if [ -n "$FINAL_PIDS" ]; then
            print_error "Could not terminate all Vocalinux processes: $FINAL_PIDS"
            print_error "Please manually kill these processes and run the installer again."
            exit 1
        else
            print_success "All Vocalinux processes stopped"
        fi
    fi
}
