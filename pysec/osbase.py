"""Base class for OS-specific security auditing implementations."""

from abc import ABC, abstractmethod


class BaseSecurityChecker(ABC):
    """Abstract base class for OS-specific security auditing implementations."""

    @abstractmethod
    def is_current_os(self) -> bool:
        """Check if the current OS matches the implementation."""

    @abstractmethod
    def get_audit_events(self) -> list[dict[str, str]]:
        """
        Return a list of recent audit events from the system.

        Each event should be a dictionary with 'timestamp' and 'event' keys.

        Example:
        [{"timestamp": "2023-06-29T10:30:00Z", "event": "user_login: alice"}, ...].

        """

    @abstractmethod
    def is_disk_encrypted(self) -> bool:
        """Return if the system disk is encrypted."""

    @abstractmethod
    def screen_lock_timeout_minutes(self) -> int | None:
        """
        Return the screen lock timeout in minutes.

        - Return None if screen locking is disabled.
        - Return a positive integer if locking is enabled.
        """

    @abstractmethod
    def automatic_daily_updates_enabled(self) -> bool:
        """Return if automatic daily updates are enabled."""
