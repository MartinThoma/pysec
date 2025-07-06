"""Authentication utilities for Django pysec server."""

import secrets
import string

CLIENT_TOKEN_LENGHT = 64


def generate_client_token() -> str:
    """Generate a secure random token for client authentication."""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(CLIENT_TOKEN_LENGHT))
