"""Authentication utilities for pysec server."""

import secrets
import string

CLIENT_TOKEN_LENGHT = 64


def generate_client_token(token_length: int) -> str:
    """Generate a secure random token for client authentication."""
    alphabet = string.ascii_letters + string.digits + "-_"
    return "".join(secrets.choice(alphabet) for _ in range(token_length))
