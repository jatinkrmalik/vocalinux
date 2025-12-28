# Vocalinux Makefile
# Convenient commands for development

.PHONY: help install install-dev test lint format clean build release

# Default target
help:
	@echo "Vocalinux Development Commands"
	@echo "=============================="
	@echo ""
	@echo "Setup:"
	@echo "  make install      - Install Vocalinux"
	@echo "  make install-dev  - Install in development mode"
	@echo ""
	@echo "Development:"
	@echo "  make test         - Run test suite"
	@echo "  make lint         - Run linters (flake8, black, isort)"
	@echo "  make format       - Auto-format code"
	@echo "  make typecheck    - Run type checking (mypy)"
	@echo ""
	@echo "Build:"
	@echo "  make build        - Build distribution packages"
	@echo "  make clean        - Remove build artifacts"
	@echo ""
	@echo "Run:"
	@echo "  make run          - Run the application"
	@echo "  make run-debug    - Run with debug logging"

# Installation
install:
	./install.sh

install-dev:
	./install.sh --dev

# Testing
test:
	@echo "Running tests..."
	pytest -v

test-cov:
	@echo "Running tests with coverage..."
	pytest --cov=src --cov-report=html --cov-report=term
	@echo "Coverage report generated in htmlcov/"

# Linting
lint:
	@echo "Running flake8..."
	flake8 src/ tests/ --count --select=E9,F63,F7,F82 --show-source --statistics
	@echo "Checking black formatting..."
	black --check --diff src/ tests/
	@echo "Checking isort..."
	isort --check-only --diff --profile black src/ tests/

format:
	@echo "Formatting with black..."
	black src/ tests/
	@echo "Sorting imports with isort..."
	isort --profile black src/ tests/

typecheck:
	@echo "Running mypy..."
	mypy src/

# Build
build:
	@echo "Building distribution packages..."
	python -m build
	@echo "Built packages in dist/"

clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf src/*.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/
	rm -f .coverage
	rm -f coverage.xml
	@echo "Clean complete"

# Run
run:
	vocalinux

run-debug:
	vocalinux --debug

run-source:
	python -m vocalinux.main

run-source-debug:
	python -m vocalinux.main --debug

# Pre-commit
pre-commit:
	pre-commit run --all-files

# Version info
version:
	@python -c "from src.vocalinux.version import __version__; print(__version__)"
