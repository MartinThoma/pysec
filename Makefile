# Makefile for pysec project

.PHONY: clean help test lint format install dev-install

# Default target
help:
	@echo "Available targets:"
	@echo "  clean       - Remove all __pycache__ directories and .pyc files"
	@echo "  test        - Run tests using pytest"
	@echo "  lint        - Run ruff linter"
	@echo "  format      - Format code using ruff"
	@echo "  install     - Install the package"
	@echo "  dev-install - Install in development mode with dev dependencies"
	@echo "  help        - Show this help message"

# Clean target - removes all __pycache__ directories and .pyc files
clean:
	@echo "Cleaning up __pycache__ directories and .pyc files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleanup complete!"

# Test target
test:
	python -m pytest

# Lint target
lint:
	python -m ruff check .

# Format target
format:
	python -m ruff format .

# Install target
install:
	pip install -e .

# Development install target
dev-install:
	pip install -e .[dev]

tree:
	tree -I venv
