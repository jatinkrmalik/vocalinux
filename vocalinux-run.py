#!/usr/bin/env python3
"""
Wrapper script to run Vocalinux directly.
"""
import os
import sys
import subprocess

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
# Build the path to the main.py file
main_script = os.path.join(script_dir, "src", "main.py")

# Execute the main script with any command line arguments
if __name__ == "__main__":
    sys.exit(subprocess.call([sys.executable, main_script] + sys.argv[1:]))
