from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class BaseSecurityChecker(ABC):
    """
    Abstract base class for OS-specific security auditing implementations.
    """

    @abstractmethod
    def get_installed_packages(self) -> List[Dict[str, str]]:
        """
        Return a list of installed packages with their versions.
        Example: [{ "name": "openssl", "version": "1.1.1" }, ...]
        """
        pass

    @abstractmethod
    def is_disk_encrypted(self) -> bool:
        """
        Return True if the system disk is encrypted, False otherwise.
        """
        pass

    @abstractmethod
    def screen_lock_timeout_minutes(self) -> Optional[int]:
        """
        Return the screen lock timeout in minutes.
        - Return None if screen locking is disabled.
        - Return a positive integer if locking is enabled.
        """
        pass
