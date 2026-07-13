#!/usr/bin/env bash
set -euo pipefail

# Phase 1: Detect Python, create throwaway venv, install textual, exec TUI.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

find_python() {
    for cmd in python3.14 python3.13 python3.12 python3.11 python3.10 python3.9 python3; do
        if command -v "$cmd" >/dev/null 2>&1; then
            if "$cmd" -c "import sys; sys.exit(0 if sys.version_info >= (3,9) else 1)" 2>/dev/null; then
                echo "$cmd"
                return 0
            fi
        fi
    done
    return 1
}

PYTHON=$(find_python) || {
    echo "Python >= 3.9 not found. Falling back to text-mode installer."
    exit 1
}

# Ensure pip
"$PYTHON" -m pip --version >/dev/null 2>&1 || {
    "$PYTHON" -m ensurepip --default-pip 2>/dev/null || {
        echo "pip not available. Falling back to text-mode installer."
        exit 1
    }
}

# Throwaway venv
VENV_DIR=$(mktemp -d /tmp/vl-tui-XXXXXX)
trap 'rm -rf "$VENV_DIR"' EXIT

"$PYTHON" -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --quiet "textual>=8.0,<9.0"

# Set PYTHONPATH to find our TUI package
export PYTHONPATH="$SCRIPT_DIR/tui:${PYTHONPATH:-}"

"$VENV_DIR/bin/python" -m vocalinux_installer_tui "$@"
