"""Python package repository implementation using pip."""

import json
import shutil
import subprocess

from .base import PackageRepositoryChecker


class PythonPackageRepository(PackageRepositoryChecker):
    """Package repository checker for Python packages managed by pip."""

    # Class variable for explicit choice mapping
    REPOSITORY_TYPE = "PYTHON_PIP"

    @classmethod
    def get_repository_type(cls) -> str:
        """Get the repository type identifier."""
        return cls.REPOSITORY_TYPE

    def is_available(self) -> bool:
        """
        Check if pip is available on the current system.

        Returns:
            bool: True if pip command is available, False otherwise.

        """
        return shutil.which("pip") is not None or shutil.which("pip3") is not None

    def get_installed_packages(self) -> list[dict[str, str]]:
        """
        Return a list of installed Python packages.

        Returns:
            list[dict[str, str]]: List of installed packages with name, version,
            and location.

        Raises:
            RuntimeError: If pip is not available or command execution fails.

        """
        if not self.is_available():
            raise RuntimeError("pip is not available on this system")

        try:
            # Use pip list with JSON format for reliable parsing
            pip_cmd = "pip3" if shutil.which("pip3") else "pip"
            result = subprocess.run(
                [pip_cmd, "list", "--format=json"],
                capture_output=True,
                text=True,
                check=True,
            )

            packages_data = json.loads(result.stdout)
            packages = []

            for package_data in packages_data:
                package_info = {
                    "name": package_data["name"],
                    "version": package_data["version"],
                    "repository_type": self.REPOSITORY_TYPE,
                }

                # Add editable location if available
                if "editable_project_location" in package_data:
                    package_info["editable_location"] = package_data[
                        "editable_project_location"
                    ]

                packages.append(package_info)

            return packages

        except subprocess.CalledProcessError as e:
            raise RuntimeError("Failed to query Python packages") from e
        except json.JSONDecodeError as e:
            raise RuntimeError("Failed to parse pip output") from e
        except Exception as e:
            raise RuntimeError("Error retrieving Python packages") from e

    def get_package_info(self, package_name: str) -> dict[str, str] | None:
        """
        Get detailed information about a specific Python package.

        Args:
            package_name (str): Name of the package to query.

        Returns:
            Optional[dict[str, str]]: Package information or None if not found.

        """
        if not self.is_available():
            return None

        try:
            pip_cmd = "pip3" if shutil.which("pip3") else "pip"
            result = subprocess.run(
                [pip_cmd, "show", "--format=json", package_name],
                capture_output=True,
                text=True,
                check=True,
            )

            if result.stdout.strip():
                package_data = json.loads(result.stdout)
                return {
                    "name": package_data.get("name", package_name),
                    "version": package_data.get("version", "unknown"),
                    "summary": package_data.get("summary", ""),
                    "location": package_data.get("location", ""),
                    "repository_type": self.REPOSITORY_TYPE,
                }
            return None

        except subprocess.CalledProcessError:
            return None
        except json.JSONDecodeError:
            return None

    def get_outdated_packages(self) -> list[dict[str, str]]:
        """
        Get a list of outdated Python packages.

        Returns:
            list[dict[str, str]]: List of packages that have newer versions available.

        """
        if not self.is_available():
            return []

        try:
            pip_cmd = "pip3" if shutil.which("pip3") else "pip"
            result = subprocess.run(
                [pip_cmd, "list", "--outdated", "--format=json"],
                capture_output=True,
                text=True,
                check=True,
            )

            packages_data = json.loads(result.stdout)

            return [
                {
                    "name": package_data["name"],
                    "current_version": package_data["version"],
                    "latest_version": package_data["latest_version"],
                    "repository_type": self.REPOSITORY_TYPE,
                }
                for package_data in packages_data
            ]

        except (subprocess.CalledProcessError, json.JSONDecodeError):
            return []
