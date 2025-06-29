"""Authentication utilities for pysec server."""

import secrets
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from pysec.config import get_or_create_server_config

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Get password hash."""
    return pwd_context.hash(password)


def generate_token() -> str:
    """Generate a secure random token for client authentication."""
    return secrets.token_urlsafe(32)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create JWT access token."""
    config = get_or_create_server_config()
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(tz=timezone.utc) + expires_delta
    else:
        expire = datetime.now(tz=timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, config.secret_key, algorithm=config.algorithm)


def verify_token(token: str) -> str | None:
    """Verify JWT token and return username if valid."""
    config = get_or_create_server_config()
    try:
        payload = jwt.decode(token, config.secret_key, algorithms=[config.algorithm])
        username = payload.get("sub")
        if username is None:
            return None
        return username
    except JWTError:
        return None
