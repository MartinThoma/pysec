"""Snap package repository implementation for Ubuntu/Linux systems."""

import shutil
import subprocess

from .base import PackageRepositoryChecker


class SnapPackageRepository(PackageRepositoryChecker):
    """Package repository checker for Snap packages on Ubuntu/Linux systems."""

    # Class variable for explicit choice mapping
    REPOSITORY_TYPE = "SNAP"

    @classmethod
    def get_repository_type(cls) -> str:
        """Get the repository type identifier."""
        return cls.REPOSITORY_TYPE

    def is_available(self) -> bool:
        """
        Check if Snap is available on the current system.

        Returns:
            bool: True if snap command is available, False otherwise.

        """
        return shutil.which("snap") is not None

    def get_installed_packages(self) -> list[dict[str, str]]:
        """
        Return a list of installed Snap packages.

        Returns:
            list[dict[str, str]]:
                List of installed packages with name, version, and channel.

        Raises:
            RuntimeError: If Snap is not available or command execution fails.

        """
        if not self.is_available():
            raise RuntimeError("Snap is not available on this system")

        try:
            result = subprocess.run(
                ["snap", "list"],
                capture_output=True,
                text=True,
                check=True,
            )

            latest_versions = self._get_latest_versions()
            packages = []
            lines = result.stdout.strip().splitlines()

            # Skip header line
            for line in lines[1:]:
                parts = line.split()
                if len(parts) >= 2:  # noqa: PLR2004
                    name = parts[0]
                    version = parts[1]

                    package_info = {
                        "name": name,
                        "version": version,
                        "latest": latest_versions.get(name, version),
                        "repository_type": self.REPOSITORY_TYPE,
                    }

                    # Add additional fields if available
                    if len(parts) >= 3:  # noqa: PLR2004
                        package_info["revision"] = parts[2]
                    if len(parts) >= 4:  # noqa: PLR2004
                        package_info["tracking"] = parts[3]
                    if len(parts) >= 5:  # noqa: PLR2004
                        package_info["publisher"] = parts[4]

                    packages.append(package_info)

            return packages

        except subprocess.CalledProcessError as e:
            raise RuntimeError("Failed to query Snap packages") from e
        except Exception as e:
            raise RuntimeError("Error retrieving Snap packages") from e

    def get_package_info(self, package_name: str) -> dict[str, str] | None:
        """
        Get detailed information about a specific Snap package.

        Args:
            package_name (str): Name of the package to query.

        Returns:
            dict[str, str] | None: Package information or None if not found.

        """
        if not self.is_available():
            return None

        try:
            result = subprocess.run(
                ["snap", "info", package_name],
                capture_output=True,
                text=True,
                check=True,
            )

            # Parse snap info output
            info = {}
            for line in result.stdout.strip().split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    info[key.strip().lower()] = value.strip()

            if "name" in info:
                return {
                    "name": info.get("name", package_name),
                    "version": info.get("version", "unknown"),
                    "summary": info.get("summary", ""),
                    "description": info.get("description", ""),
                    "publisher": info.get("publisher", ""),
                    "repository_type": self.REPOSITORY_TYPE,
                }
            return None

        except subprocess.CalledProcessError:
            return None

    def _get_latest_versions(self) -> dict[str, str]:
        """
        Get the versions of all snaps with a pending refresh in a single call.

        Returns:
            dict[str, str]: Mapping of snap name to the version available in its
            tracked channel. Snaps that are up to date are not included.

        """
        try:
            result = subprocess.run(
                ["snap", "refresh", "--list"],
                capture_output=True,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError:
            return {}

        latest_versions: dict[str, str] = {}
        # Skip header line. If nothing is pending, there is only a one-line message.
        for line in result.stdout.strip().splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 2:  # noqa: PLR2004
                latest_versions[parts[0]] = parts[1]
        return latest_versions

    def get_latest_version(self, package_name: str) -> str | None:
        """
        Get the latest available version of a package from Snap store.

        Args:
            package_name (str): Name of the package to query.

        Returns:
            str | None: Latest version string or None if not found/not available.

        """
        if not self.is_available():
            return None

        try:
            # Use snap info to get information about the package
            result = subprocess.run(
                ["snap", "info", package_name],
                capture_output=True,
                text=True,
                check=True,
            )

            # Parse snap info output to find version information
            for line in result.stdout.split("\n"):
                line = line.strip()
                # e.g. "latest/stable:    1.2.3 2023-01-01 (123) 123MB -"
                if line.startswith("latest/stable:"):
                    parts = line.split()
                    if len(parts) >= 2:  # noqa: PLR2004
                        return parts[1]

            return None

        except subprocess.CalledProcessError:
            return None
        except Exception:
            return None
