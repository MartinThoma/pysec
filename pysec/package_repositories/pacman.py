"""Pacman package repository implementation for Arch Linux."""

import shutil
import subprocess

from .base import PackageRepositoryChecker


class PacmanPackageRepository(PackageRepositoryChecker):
    """Package repository checker for Pacman packages on Arch Linux."""

    # Class variable for explicit choice mapping
    REPOSITORY_TYPE = "ARCH_PACMAN"

    @classmethod
    def get_repository_type(cls) -> str:
        """Get the repository type identifier."""
        return cls.REPOSITORY_TYPE

    def is_available(self) -> bool:
        """
        Check if Pacman is available on the current system.

        Returns:
            bool: True if pacman command is available, False otherwise.

        """
        return shutil.which("pacman") is not None

    def get_installed_packages(self) -> list[dict[str, str]]:
        """
        Return a list of installed Pacman packages.

        Returns:
            list[dict[str, str]]: List of installed packages with name and version.

        Raises:
            RuntimeError: If Pacman is not available or command execution fails.

        """
        if not self.is_available():
            raise RuntimeError("Pacman is not available on this system")

        try:
            result = subprocess.run(
                ["pacman", "-Q"],
                capture_output=True,
                text=True,
                check=True,
            )

            packages = []
            for line in result.stdout.strip().split("\n"):
                if line.strip():
                    parts = line.strip().split(" ", 1)
                    if len(parts) >= 2:  # noqa: PLR2004
                        name = parts[0]
                        version = parts[1]

                        packages.append(
                            {
                                "name": name,
                                "version": version,
                                "repository_type": self.REPOSITORY_TYPE,
                            },
                        )

            return packages

        except subprocess.CalledProcessError as e:
            raise RuntimeError("Failed to query Pacman packages") from e
        except Exception as e:
            raise RuntimeError("Error retrieving Pacman packages") from e

    def get_package_info(self, package_name: str) -> dict[str, str] | None:
        """
        Get detailed information about a specific Pacman package.

        Args:
            package_name (str): Name of the package to query.

        Returns:
            dict[str, str] | None: Package information or None if not found.

        """
        if not self.is_available():
            return None

        try:
            result = subprocess.run(
                ["pacman", "-Qi", package_name],
                capture_output=True,
                text=True,
                check=True,
            )

            # Parse pacman info output
            info = {}
            for line in result.stdout.strip().split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    info[key.strip().lower().replace(" ", "_")] = value.strip()

            if "name" in info:
                return {
                    "name": info.get("name", package_name),
                    "version": info.get("version", "unknown"),
                    "description": info.get("description", ""),
                    "architecture": info.get("architecture", ""),
                    "install_size": info.get("installed_size", ""),
                    "repository_type": self.REPOSITORY_TYPE,
                }
            return None

        except subprocess.CalledProcessError:
            return None

    def get_upgradable_packages(self) -> list[dict[str, str]]:
        """
        Get a list of packages that can be upgraded.

        Returns:
            list[dict[str, str]]: List of packages that have newer versions available.

        """
        if not self.is_available():
            return []

        try:
            result = subprocess.run(
                ["pacman", "-Qu"],
                capture_output=True,
                text=True,
                check=True,
            )

            upgradable_packages = []
            for line in result.stdout.strip().split("\n"):
                if line.strip():
                    parts = line.strip().split()
                    if len(parts) >= 4:  # noqa: PLR2004
                        name = parts[0]
                        current_version = parts[1]
                        new_version = parts[3] if len(parts) > 3 else "unknown"  # noqa: PLR2004

                        upgradable_packages.append(
                            {
                                "name": name,
                                "current_version": current_version,
                                "latest_version": new_version,
                                "repository_type": self.REPOSITORY_TYPE,
                            },
                        )

            return upgradable_packages

        except subprocess.CalledProcessError:
            # No packages to upgrade or other error
            return []
