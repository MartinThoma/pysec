# Makefile for pysec project

.PHONY: clean help test coverage lint format install dev-install specs

# Default target
help:
	@echo "Available targets:"
	@echo "  clean       - Remove all __pycache__ directories and .pyc files"
	@echo "  test        - Run tests using pytest"
	@echo "  coverage    - Run tests with coverage analysis and generate HTML report"
	@echo "  lint        - Run ruff linter"
	@echo "  format      - Format code using ruff"
	@echo "  install     - Install the package"
	@echo "  dev-install - Install in development mode with dev dependencies"
	@echo "  specs       - Generate OpenAPI specs to docs/specs.yml"
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

# Coverage target - runs tests in two phases and generates HTML coverage report
coverage:
	@echo "Running coverage analysis..."
	@echo "Phase 1: Running all tests except migrations (without --migrations flag)..."
	python -m coverage run --source=pysec,pysec_django -m pytest --ignore=tests/test_migrations.py
	@echo "Phase 2: Running migration test with --migrations flag..."
	python -m coverage run --source=pysec,pysec_django --append -m pytest tests/test_migrations.py --migrations
	@echo "Generating HTML coverage report..."
	python -m coverage html
	@echo "Coverage report generated in htmlcov/index.html"
	@echo "To view: open htmlcov/index.html in your browser"

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

# Generate OpenAPI specs
specs:
	@echo "Generating OpenAPI specs..."
	python manage.py spectacular --color --file docs/specs.yml
	@echo "OpenAPI specs generated at docs/specs.yml"
