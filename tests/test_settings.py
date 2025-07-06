"""Django settings for testing."""

from pysec_django.settings import *  # noqa: F403

# Override database to use in-memory SQLite for faster tests
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    },
}


# Disable migrations for faster tests
class DisableMigrations:
    def __contains__(self, item: str) -> bool:
        return True

    def __getitem__(self, item: str) -> None:
        return None


MIGRATION_MODULES = DisableMigrations()

# Use fast password hashing for tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Disable logging during tests
LOGGING_CONFIG = None

# Ensure we're in test mode
DEBUG = False
SECRET_KEY = "test-secret-key-for-testing-only"  # noqa: S105
