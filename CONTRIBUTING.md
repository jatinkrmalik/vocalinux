# Contributing to Vocalinux

Thank you for your interest in contributing to Vocalinux! 🎉

This document provides guidelines and instructions for contributing to the project.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Release Process](#release-process)
- [Community](#community)

## Code of Conduct

We are committed to providing a welcoming and inclusive environment. Please be respectful and constructive in your interactions.

## Getting Started

### Ways to Contribute

- 🐛 **Report bugs** - Found a bug? [Open an issue](https://github.com/jatinkrmalik/vocalinux/issues/new)
- 💡 **Suggest features** - Have an idea? [Start a discussion](https://github.com/jatinkrmalik/vocalinux/discussions)
- 📖 **Improve documentation** - Docs can always be better!
- 🔧 **Fix bugs** - Check the [issues](https://github.com/jatinkrmalik/vocalinux/issues) for things to work on
- ✨ **Add features** - Pick up a feature from the roadmap

### Good First Issues

New to the project? Look for issues labeled [`good first issue`](https://github.com/jatinkrmalik/vocalinux/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22).

## Development Setup

### Option 1: Automated Setup (Recommended)

```bash
# Fork and clone the repository
git clone https://github.com/YOUR-USERNAME/vocalinux.git
cd vocalinux

# Install in development mode (includes all dev dependencies)
./install.sh --dev
```

This will:
1. Install all system dependencies
2. Create a Python virtual environment
3. Install the package in editable mode (`-e`)
4. Install all dev dependencies (pytest, black, isort, flake8)
5. Run the test suite automatically

### Option 2: Manual Setup

1. **Fork and clone:**
   ```bash
   git clone https://github.com/YOUR-USERNAME/vocalinux.git
   cd vocalinux
   ```

2. **Install system dependencies:**
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install -y python3-pip python3-gi python3-gi-cairo \
       gir1.2-gtk-3.0 libgirepository1.0-dev \
       python3-dev portaudio19-dev python3-venv xdotool

   # For appindicator (system tray icon):
   # On older Ubuntu/Debian:
   sudo apt install -y gir1.2-appindicator3-0.1
   # On Debian 13+ (trixie) or newer:
   sudo apt install -y gir1.2-ayatanaappindicator3-0.1
   ```

3. **Set up Python environment:**
   ```bash
   python3 -m venv venv --system-site-packages
   source venv/bin/activate
   pip install --upgrade pip setuptools wheel
   pip install -e ".[dev]"
   ```

4. **Run the application:**
   ```bash
   source venv/bin/activate
   vocalinux --debug
   ```

5. **(Optional) Install pre-commit hooks:**
   ```bash
   pre-commit install
   ```
   > **Note:** Pre-commit hooks are optional. The CI pipeline runs the same checks, so you can skip this if you prefer faster local commits.

## Making Changes

### Branching Strategy

```bash
# Create a feature branch from main
git checkout main
git pull origin main
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b fix/issue-description
```

**Branch naming conventions:**
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test additions/updates

### Code Style

We use automated tools to ensure consistent code style:

- **Black** - Code formatting (line length: 100)
- **isort** - Import sorting (black-compatible profile)
- **flake8** - Linting

```bash
# Format your code
black src/ tests/
isort src/ tests/

# Check for issues
flake8 src/ tests/
```

Pre-commit hooks will run these automatically before each commit.

### Project Structure

```
vocalinux/
├── src/vocalinux/            # Main application code
│   ├── __init__.py
│   ├── main.py               # Entry point
│   ├── version.py            # Version information
│   ├── common_types.py       # Shared types/enums
│   ├── speech_recognition/   # Speech recognition engines
│   │   ├── recognition_manager.py
│   │   └── command_processor.py
│   ├── text_injection/       # Text injection (X11/Wayland)
│   │   └── text_injector.py
│   ├── ui/                   # GTK UI components
│   │   ├── tray_indicator.py
│   │   ├── settings_dialog.py
│   │   ├── config_manager.py
│   │   └── ...
│   └── utils/                # Utility functions
├── tests/                    # Test suite
├── resources/                # Icons and sounds
├── docs/                     # Documentation
└── web/                      # Website source (Next.js)
```

### Key Files for Common Tasks

| Task | Files |
|------|-------|
| Add voice command | `src/vocalinux/speech_recognition/command_processor.py` |
| UI changes | `src/vocalinux/ui/*.py` |
| Speech recognition | `src/vocalinux/speech_recognition/recognition_manager.py` |
| Text injection | `src/vocalinux/text_injection/text_injector.py` |
| Settings | `src/vocalinux/ui/config_manager.py`, `settings_dialog.py` |

## Testing

### Running Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_command_processor.py

# Run with verbose output
pytest -v
```

### Writing Tests

- Place tests in the `tests/` directory
- Name test files as `test_*.py`
- Name test functions as `test_*`
- Aim for at least 80% coverage for new code
- Use `pytest-mock` for mocking

Example test:
```python
def test_command_processor_new_line(mocker):
    """Test that 'new line' command returns correct action."""
    processor = CommandProcessor()
    result = processor.process("new line")
    assert result.action == "new_line"
```

## Pull Request Process

### Before Submitting

- [ ] Code follows the style guidelines
- [ ] Tests pass locally (`pytest`)
- [ ] Pre-commit hooks pass
- [ ] Documentation is updated (if needed)
- [ ] Commit messages are clear and descriptive

### Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) style:

```
type(scope): short description

Longer description if needed.

Fixes #123
```

**Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

**Examples:**
```
feat(commands): add "select all" voice command
fix(tray): resolve icon not updating on Wayland
docs(readme): update installation instructions
```

### Submitting

1. Push your branch to your fork
2. Open a Pull Request against `main`
3. Fill out the PR template
4. Link any related issues
5. Wait for CI to pass
6. Request a review

### Review Process

- PRs require at least one approval
- CI must pass (linting, tests)
- Maintainers may request changes
- Once approved, maintainers will merge

## Release Process

Releases are managed through GitHub tags and the release workflow.

### Version Bumping

1. Update version in `src/vocalinux/version.py`
2. Commit: `git commit -m "chore: bump version to x.y.z"`
3. Tag: `git tag vx.y.z`
4. Push: `git push origin main --tags`
5. GitHub Release will be auto-created with release notes

### Versioning Scheme

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR.MINOR.PATCH** (e.g., `1.2.3`)
- Pre-release: `x.y.z-alpha`, `x.y.z-beta`, `x.y.z-rc.1`

## Community

### Getting Help

- 💬 [GitHub Discussions](https://github.com/jatinkrmalik/vocalinux/discussions) - Ask questions
- 🐛 [GitHub Issues](https://github.com/jatinkrmalik/vocalinux/issues) - Report bugs

### Stay Connected

- ⭐ Star the repository to show support
- 👀 Watch for updates
- 🐦 Follow [@jatinkrmalik](https://twitter.com/jatinkrmalik) on Twitter

---

Thank you for contributing to Vocalinux! ❤️
