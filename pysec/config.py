"""
Central configuration utilities for pysec.

* Using pydantic for configuration models
* Following XDG Base Directory Specification
"""

import os
from pathlib import Path


def get_config_dir() -> Path:
    """Get the configuration directory following XDG Base Directory Specification."""
    xdg_config_home = os.getenv("XDG_CONFIG_HOME")
    if xdg_config_home:
        return Path(xdg_config_home) / "pysec"
    return Path.home() / ".config" / "pysec"


def ensure_directory(path: Path) -> Path:
    """Ensure a directory exists, creating it if necessary."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_client_config_file() -> Path:
    """Get the client configuration file path."""
    return get_config_dir() / "client.json"
