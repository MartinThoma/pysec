"""Base class for package repository implementations."""

from abc import ABC, abstractmethod


class PackageRepositoryChecker(ABC):
    """Abstract base class for package repository implementations."""

    # Subclasses should define this class variable
    REPOSITORY_TYPE: str = "UNKNOWN"

    @classmethod
    def get_repository_type(cls) -> str:
        """Get the repository type identifier."""
        return cls.REPOSITORY_TYPE  # pragma: no cover

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if this package repository is available on the current system.

        Returns:
            bool: True if the repository/package manager is available, False otherwise.

        """

    @abstractmethod
    def get_installed_packages(self) -> list[dict[str, str]]:
        """
        Return a list of installed packages from this repository.

        Returns:
            list[dict[str, str]]: List of packages with their metadata.
            Each package should be a dictionary with at least 'name', 'version',
            and 'latest' keys. 'latest' equals 'version' if the package is up to date.

        Example:
            [
                {
                    "name": "openssl",
                    "version": "1.1.1f-1ubuntu2.20",
                    "latest": "1.1.1f-1ubuntu2.21",
                },
                {
                    "name": "python3",
                    "version": "3.8.10-0ubuntu1~20.04.8",
                    "latest": "3.8.10-0ubuntu1~20.04.8",
                },
                ...
            ]

        """

    @abstractmethod
    def get_latest_version(self, package_name: str) -> str | None:
        """
        Get the latest available version of a package from the repository.

        Args:
            package_name (str): Name of the package to query.

        Returns:
            str | None: Latest version string or None if not found/not available.

        """

    def get_package_info(self, package_name: str) -> dict[str, str] | None:  # noqa: ARG002
        """
        Get detailed information about a specific package.

        This is an optional method that repositories can implement for enhanced
        functionality.

        Args:
            package_name (str): Name of the package to query.

        Returns:
            dict[str, str] | None: Package information or None if not found/supported.

        """
        return None
