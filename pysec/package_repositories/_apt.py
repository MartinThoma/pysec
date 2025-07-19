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
            Optional[dict[str, str]]: Package information or None if not found.

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
