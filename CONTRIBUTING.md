# Contributing to Vocalinux

Thank you for your interest in contributing to Vocalinux! This document provides guidelines and instructions for contributing to the project.

## Development Environment Setup

### Option 1: Automated Setup (Recommended)

The easiest way to set up a development environment is using the installer script with the `--dev` flag:

```bash
# Clone the repository
git clone https://github.com/YOUR-USERNAME/vocalinux.git
cd vocalinux

# Install in development mode
./install.sh --dev
```

This will:
1. Install all system dependencies
2. Create a Python virtual environment
3. Install the package in development mode with the `-e` flag
4. Install all development dependencies including testing tools
5. Run the tests automatically

### Option 2: Manual Setup

If you prefer to set up your development environment manually:

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/vocalinux.git
   cd vocalinux
   ```

3. Install system dependencies:
   ```bash
   # For Ubuntu/Debian
   sudo apt update
   sudo apt install -y python3-pip python3-gi python3-gi-cairo gir1.2-gtk-3.0 \
       gir1.2-appindicator3-0.1 libgirepository1.0-dev python3-dev portaudio19-dev python3-venv
   
   # For X11 environments
   sudo apt install -y xdotool
   
   # For Wayland environments
   sudo apt install -y wtype
   ```

4. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv --system-site-packages
   source venv/bin/activate
   ```

5. Install the package in development mode:
   ```bash
   # Update pip and setuptools
   pip install --upgrade pip setuptools wheel
   
   # Install in development mode with all dev dependencies
   pip install -e ".[dev]"
   ```

6. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Directory Structure

The project follows this directory structure:

```
vocalinux/
├── docs/                      # Documentation
│   ├── INSTALL.md            # Installation guide
│   └── USER_GUIDE.md         # User guide
├── resources/                 # Resource files
│   ├── icons/                # Application icons
│   └── sounds/               # Audio notification sounds
├── src/                       # Source code
│   ├── speech_recognition/   # Speech recognition components
│   ├── text_injection/       # Text injection components
│   └── ui/                   # User interface components
├── tests/                     # Test suite
├── CONTRIBUTING.md           # Contribution guidelines (this file)
├── install.sh                # Installation script
├── LICENSE                   # License information
├── README.md                 # Project overview
└── setup.py                  # Python package configuration
```

## Pre-commit Hooks

We use pre-commit hooks to ensure code quality and consistency. These hooks automatically run before each commit to check your code against our standards.

### Pre-commit Configuration

The pre-commit configuration in `.pre-commit-config.yaml` includes:

1. **black**: Code formatter (line length: 100)
2. **isort**: Import sorter (configured to be compatible with black)
3. **flake8**: Linter with plugins for docstrings, comprehensions, and bug detection
4. **Additional checks**: Trailing whitespace, file endings, YAML/JSON validation, etc.

### Running Pre-commit Manually

You can run the pre-commit checks manually on all files:
```bash
pre-commit run --all-files
```

Or on specific files:
```bash
pre-commit run --files path/to/file1.py path/to/file2.py
```

### Bypassing Pre-commit (Emergency Only)

In emergency situations only, you can bypass pre-commit hooks:
```bash
git commit -m "Your message" --no-verify
```

However, this is strongly discouraged as it may lead to CI pipeline failures.

## Testing

Write tests for all new features and bug fixes:

```bash
# Run all tests
pytest

# Run a specific test file
pytest tests/test_specific_file.py

# Run tests with coverage report
pytest --cov=src

# Generate HTML coverage report
pytest --cov=src --cov-report=html
```

Aim for at least 80% test coverage for new code.

## Code Style Guidelines

We follow these code style conventions:

1. **PEP 8**: With modifications:
   - Maximum line length: 100 characters
   - Use Black formatting

2. **Docstrings**: All public methods, classes, and modules should have docstrings

3. **Imports**: Organized using isort with the following sections:
   - Standard library imports
   - Third-party imports
   - Local application imports

4. **Type Annotations**: Use type hints where appropriate

## Pull Request Process

1. Ensure all pre-commit checks pass
2. Update documentation if necessary
3. Add or update tests as needed
4. Create a pull request with a clear description of the changes
5. Link any related issues
6. Wait for code review

## Commit Message Guidelines

Follow these guidelines for commit messages:

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests after the first line

Example:
```
Add voice command for deleting sentences

This implements the "delete that" command functionality
to remove the last sentence entered by the user.

Fixes #123
```

## Documentation

Update documentation for any new features or changes:

- Add docstrings to new functions, classes, and methods
- Update README.md or relevant docs in the docs/ directory
- Add or update code examples if applicable

## Development Workflow Tips

1. **Virtual Environment**: Always activate the virtual environment before working on the project:
   ```bash
   source activate-vocalinux.sh
   ```

2. **Debugging**: Use the `--debug` flag when running Vocalinux during development:
   ```bash
   vocalinux --debug
   ```

3. **Branching Strategy**:
   - Create feature branches from `main`
   - Name branches descriptively (e.g., `feature/voice-commands`, `fix/tray-icon-bug`)
   - Keep pull requests focused on a single issue/feature

4. **Common Development Tasks**:
   - Adding a new voice command? Modify `command_processor.py`
   - UI changes? Look at files in the `ui/` directory
   - Speech recognition tweaks? Check `speech_recognition/recognition_manager.py`

Thank you for contributing to Vocalinux!
