"""Homebrew package repository implementation for macOS."""

import json
import shutil
import subprocess

from .base import PackageRepositoryChecker


class HomebrewPackageRepository(PackageRepositoryChecker):
    """Package repository checker for Homebrew packages on macOS."""

    # Class variable for explicit choice mapping
    REPOSITORY_TYPE = "HOMEBREW"

    @classmethod
    def get_repository_type(cls) -> str:
        """Get the repository type identifier."""
        return cls.REPOSITORY_TYPE

    def is_available(self) -> bool:
        """
        Check if Homebrew is available on the current system.

        Returns:
            bool: True if brew command is available, False otherwise.

        """
        return shutil.which("brew") is not None

    def get_installed_packages(self) -> list[dict[str, str]]:
        """
        Return a list of installed Homebrew packages.

        Returns:
            list[dict[str, str]]: List of installed packages with name and version.

        Raises:
            RuntimeError: If Homebrew is not available or command execution fails.

        """
        if not self.is_available():
            raise RuntimeError("Homebrew is not available on this system")

        try:
            result = subprocess.run(
                ["brew", "list", "--versions"],
                capture_output=True,
                text=True,
                check=True,
            )

            packages = []
            for line in result.stdout.strip().splitlines():
                parts = line.strip().split()
                if len(parts) >= 2:  # noqa: PLR2004
                    name = parts[0]
                    version = parts[1]

                    packages.append(
                        {
                            "name": name,
                            "version": version,
                            "repository_type": self.REPOSITORY_TYPE,
                        }
                    )

            return packages

        except subprocess.CalledProcessError as e:
            raise RuntimeError("Failed to query Homebrew packages") from e
        except Exception as e:
            raise RuntimeError("Error retrieving Homebrew packages") from e

    def get_package_info(self, package_name: str) -> dict[str, str] | None:
        """
        Get detailed information about a specific Homebrew package.

        Args:
            package_name (str): Name of the package to query.

        Returns:
            dict[str, str] | None: Package information or None if not found.

        """
        if not self.is_available():
            return None

        try:
            result = subprocess.run(
                ["brew", "info", "--json=v1", package_name],
                capture_output=True,
                text=True,
                check=True,
            )

            if result.stdout.strip():
                package_data = json.loads(result.stdout)
                if package_data and len(package_data) > 0:
                    pkg = package_data[0]
                    return {
                        "name": pkg.get("name", package_name),
                        "version": pkg.get("linked_keg", "unknown"),
                        "description": pkg.get("desc", ""),
                        "homepage": pkg.get("homepage", ""),
                        "repository_type": self.REPOSITORY_TYPE,
                    }
            return None

        except (subprocess.CalledProcessError, json.JSONDecodeError):
            return None

    def get_outdated_packages(self) -> list[dict[str, str]]:
        """
        Get a list of outdated Homebrew packages.

        Returns:
            list[dict[str, str]]: List of packages that have newer versions available.

        """
        if not self.is_available():
            return []

        try:
            result = subprocess.run(
                ["brew", "outdated", "--json=v1"],
                capture_output=True,
                text=True,
                check=True,
            )

            packages_data = json.loads(result.stdout)
            outdated_packages: list[dict[str, str]] = []

            outdated_packages.extend(
                {
                    "name": package_data["name"],
                    "current_version": package_data.get(
                        "installed_versions", ["unknown"]
                    )[0],
                    "latest_version": package_data.get("current_version", "unknown"),
                    "repository_type": self.REPOSITORY_TYPE,
                }
                for package_data in packages_data
            )

            return outdated_packages

        except (subprocess.CalledProcessError, json.JSONDecodeError):
            return []
