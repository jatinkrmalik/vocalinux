# Contributing to Vocalinux

Thank you for your interest in contributing to Vocalinux! This document provides guidelines and instructions for contributing to the project.

## Development Environment Setup

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/vocalinux.git
   cd vocalinux
   ```
3. Set up the development environment:
   ```bash
   # Install development dependencies
   pip install -e ".[dev]"

   # Install pre-commit hooks
   pip install pre-commit
   pre-commit install
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

## Testing

Write tests for all new features and bug fixes:

```bash
# Run tests
pytest

# Run tests with coverage report
pytest --cov=src
```

Aim for at least 80% test coverage for new code.

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

Thank you for contributing to Vocalinux!
