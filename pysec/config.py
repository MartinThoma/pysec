"""
Central configuration utilities for pysec.

* Using pydantic for configuration models
* Following XDG Base Directory Specification
"""

import json
import os
import secrets
import string
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel


class ServerConfig(BaseModel):
    """Server configuration model."""

    admin_password: str
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    created_at: str


def get_config_dir() -> Path:
    """Get the configuration directory following XDG Base Directory Specification."""
    xdg_config_home = os.getenv("XDG_CONFIG_HOME")
    if xdg_config_home:
        return Path(xdg_config_home) / "pysec"
    return Path.home() / ".config" / "pysec"


def get_data_dir() -> Path:
    """Get the data directory following XDG Base Directory Specification."""
    xdg_data_home = os.getenv("XDG_DATA_HOME")
    if xdg_data_home:
        return Path(xdg_data_home) / "pysec"
    return Path.home() / ".local" / "share" / "pysec"


def get_cache_dir() -> Path:
    """Get the cache directory following XDG Base Directory Specification."""
    xdg_cache_home = os.getenv("XDG_CACHE_HOME")
    if xdg_cache_home:
        return Path(xdg_cache_home) / "pysec"
    return Path.home() / ".cache" / "pysec"


def get_runtime_dir() -> Path:
    """Get the runtime directory following XDG Base Directory Specification."""
    xdg_runtime_dir = os.getenv("XDG_RUNTIME_DIR")
    if xdg_runtime_dir:
        return Path(xdg_runtime_dir) / "pysec"
    # Fallback to a secure temporary directory if XDG_RUNTIME_DIR is not set
    return Path(tempfile.gettempdir()) / f"pysec-{os.getuid()}"


def ensure_directory(path: Path) -> Path:
    """Ensure a directory exists, creating it if necessary."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_client_config_file() -> Path:
    """Get the client configuration file path."""
    return get_config_dir() / "client.json"


def get_server_config_file() -> Path:
    """Get the server configuration file path."""
    return get_config_dir() / "server.json"


def get_default_db_path() -> Path:
    """Get the default database path for the server."""
    return get_data_dir() / "pysec.db"


def generate_secure_password(length: int = 20) -> str:
    """Generate a secure random password."""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def get_or_create_server_config() -> ServerConfig:
    """Get or create server configuration with secure admin password."""
    config_file = get_server_config_file()
    ensure_directory(config_file.parent)

    if config_file.exists():
        try:
            with config_file.open() as f:
                config_data = json.load(f)
                return ServerConfig(**config_data)
        except (OSError, json.JSONDecodeError, ValueError):
            # If config is corrupted or invalid, recreate it
            pass

    # Create new config with secure password and JWT settings
    config_data = {
        "admin_password": generate_secure_password(),
        "secret_key": generate_secure_password(32),
        "algorithm": "HS256",
        "access_token_expire_minutes": 30,
        "created_at": str(datetime.now(tz=timezone.utc)),
    }

    # Create ServerConfig object
    config = ServerConfig(**config_data)

    # Save to file
    with config_file.open("w") as f:
        json.dump(config.model_dump(), f, indent=2)

    # Set restrictive permissions (owner read/write only)
    config_file.chmod(0o600)

    return config
