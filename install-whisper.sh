#!/bin/bash
# VocaLinux Whisper Installation Helper Script
# This script helps install Whisper AI support for VocaLinux

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print functions
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the VocaLinux directory
if [ ! -f "setup.py" ] || [ ! -d "src/vocalinux" ]; then
    print_error "This script must be run from the VocaLinux root directory"
    exit 1
fi

print_info "VocaLinux Whisper Installation Helper"
echo "======================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_error "Virtual environment not found. Please run ./install.sh first."
    exit 1
fi

print_info "Found virtual environment: venv/"

# Activate virtual environment
print_info "Activating virtual environment..."
source venv/bin/activate

# Check current Python and pip
print_info "Python executable: $(which python)"
print_info "Pip version: $(pip --version)"

# Check if Whisper is already installed
print_info "Checking current Whisper installation..."
if python -c "import whisper; print('Whisper version:', whisper.__version__)" 2>/dev/null; then
    print_success "Whisper is already installed!"
    python -c "import whisper; print('Available models:', whisper.available_models())"
    exit 0
fi

print_warning "Whisper is not installed. Attempting installation..."

# Try different installation methods
echo ""
print_info "Attempting Method 1: Standard pip installation..."
if pip install openai-whisper torch torchaudio; then
    print_success "Whisper installed successfully using standard method!"
else
    print_warning "Standard installation failed. Trying with trusted hosts..."
    
    print_info "Attempting Method 2: Installation with trusted hosts..."
    if pip install openai-whisper torch torchaudio \
        --trusted-host pypi.org \
        --trusted-host pypi.python.org \
        --trusted-host files.pythonhosted.org; then
        print_success "Whisper installed successfully using trusted hosts!"
    else
        print_warning "Trusted hosts method failed. Trying with --break-system-packages..."
        
        print_info "Attempting Method 3: Installation with --break-system-packages..."
        if pip install openai-whisper torch torchaudio --break-system-packages; then
            print_success "Whisper installed successfully with --break-system-packages!"
        else
            print_error "All installation methods failed."
            echo ""
            print_info "Manual installation options:"
            echo "1. Fix SSL issues in your Python installation"
            echo "2. Use conda: conda install pytorch torchaudio -c pytorch && pip install openai-whisper"
            echo "3. Install from source: https://github.com/openai/whisper"
            echo "4. Use system packages if available"
            echo ""
            print_info "For SSL issues, you may need to:"
            echo "- Install ca-certificates: sudo apt install ca-certificates"
            echo "- Reinstall Python with SSL support"
            echo "- Use a different Python installation (pyenv, conda, etc.)"
            exit 1
        fi
    fi
fi

# Verify installation
echo ""
print_info "Verifying Whisper installation..."
if python -c "import whisper; import torch; print('✅ Whisper and PyTorch imported successfully')"; then
    print_success "Whisper installation verified!"
    
    # Show available models
    python -c "
import whisper
import torch
print('Available Whisper models:', whisper.available_models())
print('PyTorch version:', torch.__version__)
print('CUDA available:', torch.cuda.is_available())
"
    
    echo ""
    print_success "Whisper is now ready to use in VocaLinux!"
    print_info "You can now:"
    echo "1. Start VocaLinux: ./activate-vocalinux.sh && vocalinux"
    echo "2. Open Settings and select Whisper as the speech engine"
    echo "3. Choose a model size (base, small, medium recommended)"
    
else
    print_error "Whisper installation verification failed"
    exit 1
fi