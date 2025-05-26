#!/bin/bash
# Vocalinux Virtual Environment Activation Script
# This script activates the virtual environment and sets up the Python path

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if virtual environment exists
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    echo "Error: Virtual environment not found at $SCRIPT_DIR/venv"
    echo "Please run the installer script first: ./install.sh"
    return 1 2>/dev/null || exit 1
fi

# Activate the virtual environment
source "$SCRIPT_DIR/venv/bin/activate"

# Set up Python path for development
export PYTHONPATH="$SCRIPT_DIR/src:$PYTHONPATH"

echo "Vocalinux development environment activated!"
echo "Virtual environment: $SCRIPT_DIR/venv"
echo "Python path includes: $SCRIPT_DIR/src"
echo ""
echo "You can now:"
echo "  - Run tests: pytest tests/"
echo "  - Run Vocalinux: python -m vocalinux.main"
echo "  - Install in development mode: pip install -e ."
echo ""
