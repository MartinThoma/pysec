"""Pytest configuration for Django tests."""

import os
import sys
from pathlib import Path

import django

# Add the project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))


def pytest_configure() -> None:
    """Configure Django for pytest."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.test_settings")
    django.setup()
