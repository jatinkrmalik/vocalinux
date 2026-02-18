# AGENTS.md - Vocalinux

Guidelines for AI agents working on this codebase.

## Project Overview

Vocalinux is a voice dictation system for Linux. It uses:
- **Python 3.8+** for the main application
- **GTK 3** (via PyGObject) for the desktop UI and system tray
- **whisper.cpp** (default), **OpenAI Whisper**, and **Vosk** for speech recognition
- **Next.js/TypeScript** for the website (in `web/`)

### Key Dependencies
- `pywhispercpp` - Python bindings for whisper.cpp (default engine)
- `vosk` - Lightweight speech recognition
- `pyaudio` - Audio capture
- `PyGObject` - GTK integration
- `psutil` - Process utilities (required by pywhispercpp)

## Build & Test Commands

### Python

```bash
# Install in development mode
./install.sh --dev
# Or manually:
pip install -e ".[dev]"

# Run all tests
pytest

# Run a single test file
pytest tests/test_command_processor.py

# Run a single test function
pytest tests/test_command_processor.py::TestCommandProcessor::test_initialization

# Run tests with verbose output
pytest -v

# Run tests with coverage
pytest --cov=src --cov-report=html

# Run tests excluding slow/integration tests
pytest -m "not slow"
pytest -m "not integration"

# Lint (check only)
make lint
# Or manually:
flake8 src/ tests/ --select=E9,F63,F7,F82
black --check --diff src/ tests/
isort --check-only --diff --profile black src/ tests/

# Auto-format code
make format
# Or manually:
black src/ tests/
isort --profile black src/ tests/

# Type checking
make typecheck
# Or: mypy src/

# Run the application
vocalinux --debug
# Or from source: python -m vocalinux.main --debug
```

### Website (Next.js)

```bash
cd web
npm install
npm run dev      # Development server
npm run build    # Production build
npm run lint     # ESLint
npm run test     # Jest tests
```

## Code Style Guidelines

### Formatting

- **Line length**: 100 characters
- **Formatter**: Black
- **Import sorter**: isort (black-compatible profile)
- **Linter**: flake8

### Import Order

Use isort with black profile. Imports should be grouped:
1. Standard library (`import os`, `from typing import ...`)
2. Third-party packages (`import gi`, `from vosk import Model`)
3. Local imports (`from vocalinux.common_types import ...`)

### Type Hints

Use type hints for all function signatures. Use `Protocol` for interfaces (see `common_types.py`).

### Naming Conventions

- **Classes**: `PascalCase` (e.g., `CommandProcessor`, `ConfigManager`)
- **Functions/methods**: `snake_case` (e.g., `process_text`, `load_config`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `CONFIG_DIR`, `DEFAULT_CONFIG`)
- **Private methods**: `_leading_underscore` (e.g., `_compile_patterns`)
- **Module-level logger**: `logger = logging.getLogger(__name__)`

### Docstrings

Use triple-quoted docstrings for modules, classes, and public functions:

```python
"""Configuration manager for Vocalinux."""

class ConfigManager:
    """Manager for user configuration settings."""

    def load_config(self):
        """Load configuration from the config file."""
```

### Error Handling

Use specific exception types, log errors with context:

```python
try:
    with open(CONFIG_FILE, "r") as f:
        user_config = json.load(f)
except json.JSONDecodeError as e:
    logger.error(f"Invalid JSON in config file: {e}")
```

### Logging

Each module should have its own logger:

```python
import logging
logger = logging.getLogger(__name__)
```

## Testing Guidelines

- Place tests in `tests/` directory
- Name test files as `test_*.py`, functions as `test_*`
- Use `unittest.TestCase` or plain pytest functions
- Use `pytest-mock` for mocking (via `mocker` fixture)

### Test Markers

```python
@pytest.mark.slow          # Long-running tests
@pytest.mark.integration   # Integration tests
@pytest.mark.audio         # Requires audio hardware
```

## Project Structure

```
src/vocalinux/
├── main.py                    # Application entry point
├── version.py                 # Version info
├── common_types.py            # Shared types/enums/protocols
├── speech_recognition/
│   ├── recognition_manager.py # VOSK/Whisper/whisper.cpp management
│   └── command_processor.py   # Voice command processing
├── text_injection/
│   └── text_injector.py       # X11/Wayland text injection
├── ui/
│   ├── tray_indicator.py      # System tray icon
│   ├── settings_dialog.py     # Settings GUI
│   ├── config_manager.py      # Configuration handling
│   └── keyboard_backends/     # Keyboard input handling
└── utils/
    ├── resource_manager.py    # Resource utilities
    ├── whispercpp_model_info.py   # whisper.cpp model metadata & hardware detection
    └── vosk_model_info.py         # VOSK model metadata
```

## Release Process

See `docs/RELEASE_PROCESS.md` for detailed release instructions.

Quick summary:
1. Update version in `src/vocalinux/version.py`
2. Update version references in README.md, docs/INSTALL.md, docs/UPDATE.md
3. Update web/src/app/page.tsx and web/package.json
4. Run `make lint` to verify code quality
5. Create branch `release/vX.Y.Z-PHASE`
6. Commit with `chore(release): prepare vX.Y.Z-PHASE`
7. Push and create PR
8. After merge, create and push tag: `git tag -a vX.Y.Z-PHASE -m "Release X.Y.Z-PHASE"`
9. GitHub Actions will build and publish automatically

## Commit Message Format

Follow Conventional Commits:

```
type(scope): short description

Longer description if needed.

Fixes #123
```

**Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

**Examples**:
```
feat(commands): add "select all" voice command
fix(tray): resolve icon not updating on Wayland
docs(readme): update installation instructions
```

## Branch Naming

- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test additions/updates
- `release/` - Release preparation (e.g., `release/v0.6.2-beta`)

## Important Rules

- **Never push directly to `main`** - Always create a branch and PR
- **All changes require a PR** - Even small fixes and documentation updates
- **Wait for CI to pass** before merging PRs
- **Squash merge** PRs to keep history clean
