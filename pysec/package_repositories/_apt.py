"""APT package repository implementation for Debian/Ubuntu systems."""

import shutil
import subprocess

from .base import PackageRepositoryChecker


class AptPackageRepository(PackageRepositoryChecker):
    """
    Package repository checker for APT (Advanced Package Tool).

    e.g. on Debian/Ubuntu systems
    """

    # Class variable for explicit choice mapping
    REPOSITORY_TYPE = "DEBIAN_APT"

    @classmethod
    def get_repository_type(cls) -> str:
        """Get the repository type identifier."""
        return cls.REPOSITORY_TYPE

    def is_available(self) -> bool:
        """
        Check if APT is available on the current system.

        Returns:
            bool: True if apt command is available, False otherwise.

        """
        return shutil.which("apt") is not None or shutil.which("apt-get") is not None

    def get_installed_packages(self) -> list[dict[str, str]]:
        """
        Return a list of installed APT packages.

        Returns:
            list[dict[str, str]]: List of installed packages with name, version,
            and architecture.

        Raises:
            RuntimeError: If APT is not available or command execution fails.

        """
        if not self.is_available():
            raise RuntimeError("APT is not available on this system")

        try:
            # Use dpkg-query to get installed packages in a parseable format
            result = subprocess.run(
                [
                    "dpkg-query",
                    "-W",
                    "-f=${Package}\t${Version}\t${Architecture}\t${Status}\n",
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            latest_versions = self._get_latest_versions()
            packages = []
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue

                parts = line.split("\t")
                if len(parts) >= 4:  # noqa: PLR2004
                    package_name, version, architecture, status = (
                        parts[0],
                        parts[1],
                        parts[2],
                        parts[3],
                    )

                    # Only include packages that are properly installed
                    if "install ok installed" in status:
                        packages.append(
                            {
                                "name": package_name,
                                "version": version,
                                "latest": latest_versions.get(package_name, version),
                                "architecture": architecture,
                                "repository_type": self.REPOSITORY_TYPE,
                            },
                        )

            return packages

        except subprocess.CalledProcessError as e:
            raise RuntimeError("Failed to query APT packages") from e
        except Exception as e:
            raise RuntimeError("Error retrieving APT packages") from e

    def get_package_info(self, package_name: str) -> dict[str, str] | None:
        """
        Get detailed information about a specific package.

        Args:
            package_name (str): Name of the package to query.

        Returns:
            dict[str, str] | None: Package information or None if not found.

        """
        if not self.is_available():
            return None

        try:
            result = subprocess.run(
                [
                    "dpkg-query",
                    "-W",
                    "-f=${Package}\t${Version}\t${Architecture}\t${Status}\n",
                    package_name,
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            line = result.stdout.strip()
            if line:
                parts = line.split("\t")
                if len(parts) >= 4:  # noqa: PLR2004
                    package_name, version, architecture, status = (
                        parts[0],
                        parts[1],
                        parts[2],
                        parts[3],
                    )
                    if "install ok installed" in status:
                        return {
                            "name": package_name,
                            "version": version,
                            "architecture": architecture,
                            "repository_type": self.REPOSITORY_TYPE,
                        }
            return None

        except subprocess.CalledProcessError:
            return None

    def _get_latest_versions(self) -> dict[str, str]:
        """
        Get the candidate versions of all upgradable packages in a single call.

        Returns:
            dict[str, str]: Mapping of package name to candidate version.
            Packages that are up to date are not included.

        """
        try:
            result = subprocess.run(
                ["apt", "list", "--upgradable"],
                capture_output=True,
                text=True,
                check=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            return {}

        latest_versions: dict[str, str] = {}
        for line in result.stdout.splitlines():
            # e.g. "openssl/jammy-updates 3.0.13-1 amd64 [upgradable from: 3.0.12-1]"
            name, _, rest = line.partition("/")
            parts = rest.split()
            if name and len(parts) >= 2:  # noqa: PLR2004
                latest_versions[name] = parts[1]
        return latest_versions

    def get_latest_version(self, package_name: str) -> str | None:
        """
        Get the latest available version of a package from APT repositories.

        Args:
            package_name (str): Name of the package to query.

        Returns:
            str | None: Latest version string or None if not found/not available.

        """
        if not self.is_available():
            return None

        try:
            # Use apt-cache policy to get the candidate (latest available) version
            result = subprocess.run(
                ["apt-cache", "policy", package_name],
                capture_output=True,
                text=True,
                check=True,
            )

            for line in result.stdout.split("\n"):
                line = line.strip()
                if line.startswith("Candidate:"):
                    candidate_version = line.split(":", 1)[1].strip()
                    if candidate_version != "(none)":
                        return candidate_version

            return None

        except subprocess.CalledProcessError:
            return None
        except Exception:
            return None
