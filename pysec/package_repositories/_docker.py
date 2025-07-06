"""Docker package repository implementation for containerized environments."""

import json
import shutil
import subprocess

from .base import PackageRepositoryChecker


class DockerPackageRepository(PackageRepositoryChecker):
    """
    Package repository checker for Docker containers and images.

    This checker can list Docker images and running containers on the system.
    """

    # Class variable for explicit choice mapping
    REPOSITORY_TYPE = "DOCKER"

    @classmethod
    def get_repository_type(cls) -> str:
        """Get the repository type identifier."""
        return cls.REPOSITORY_TYPE

    def is_available(self) -> bool:
        """
        Check if Docker is available on the current system.

        Returns:
            bool: True if docker command is available and daemon is running,
                False otherwise.

        """
        if shutil.which("docker") is None:
            return False

        try:
            # Check if Docker daemon is running by testing a simple command
            result = subprocess.run(
                ["docker", "version", "--format", "json"],
                capture_output=True,
                text=True,
                check=False,
                timeout=5,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def get_installed_packages(self) -> list[dict[str, str]]:
        """
        Return a list of Docker images and containers on the system.

        Returns:
            list[dict[str, str]]: List of Docker images and containers with metadata.
            Each item includes name, version/tag, type (image/container), and status.

        Raises:
            RuntimeError: If Docker is not available or command execution fails.

        """
        if not self.is_available():
            raise RuntimeError("Docker is not available on this system")

        packages = []

        # Get Docker images
        try:
            packages.extend(self._get_docker_images())
        except Exception as e:
            raise RuntimeError("Failed to get Docker images") from e

        # Get Docker containers
        try:
            packages.extend(self._get_docker_containers())
        except Exception as e:
            raise RuntimeError("Failed to get Docker containers") from e

        return packages

    def _get_docker_images(self) -> list[dict[str, str]]:
        """
        Get Docker images from the system.

        Returns:
            list[dict[str, str]]: List of Docker images with metadata.

        """
        result = subprocess.run(
            ["docker", "images", "--format", "json"],
            capture_output=True,
            text=True,
            check=True,
        )

        images = []
        for line in result.stdout.strip().split("\n"):
            if line.strip():
                try:
                    image_data = json.loads(line)
                    images.append(
                        {
                            "name": image_data.get("Repository", "unknown"),
                            "version": image_data.get("Tag", "unknown"),
                            "type": "image",
                            "size": image_data.get("Size", "unknown"),
                            "created": image_data.get("CreatedSince", "unknown"),
                            "image_id": image_data.get("ID", "unknown"),
                        }
                    )
                except json.JSONDecodeError:
                    continue

        return images

    def _get_docker_containers(self) -> list[dict[str, str]]:
        """
        Get Docker containers from the system (both running and stopped).

        Returns:
            list[dict[str, str]]: List of Docker containers with metadata.

        """
        result = subprocess.run(
            ["docker", "ps", "-a", "--format", "json"],
            capture_output=True,
            text=True,
            check=True,
        )

        containers = []
        for line in result.stdout.strip().split("\n"):
            if line.strip():
                try:
                    container_data = json.loads(line)
                    containers.append(
                        {
                            "name": container_data.get("Names", "unknown"),
                            "version": container_data.get("Image", "unknown"),
                            "type": "container",
                            "status": container_data.get("Status", "unknown"),
                            "created": container_data.get("CreatedAt", "unknown"),
                            "container_id": container_data.get("ID", "unknown"),
                        }
                    )
                except json.JSONDecodeError:
                    continue

        return containers

    def get_package_info(self, package_name: str) -> dict[str, str] | None:
        """
        Get detailed information about a specific Docker image or container.

        Args:
            package_name (str): Name of the Docker image or container to query.

        Returns:
            dict[str, str] | None: Package information or None if not found.

        """
        if not self.is_available():
            return None

        # Try to get info as an image first
        try:
            result = subprocess.run(
                ["docker", "image", "inspect", package_name],
                capture_output=True,
                text=True,
                check=True,
            )

            image_data = json.loads(result.stdout)[0]
            config = image_data.get("Config", {})

            return {
                "name": package_name,
                "type": "image",
                "id": image_data.get("Id", "unknown"),
                "created": image_data.get("Created", "unknown"),
                "architecture": image_data.get("Architecture", "unknown"),
                "os": image_data.get("Os", "unknown"),
                "size": str(image_data.get("Size", 0)),
                "labels": str(config.get("Labels", {})),
                "exposed_ports": str(list(config.get("ExposedPorts", {}).keys())),
            }
        except (subprocess.CalledProcessError, json.JSONDecodeError, IndexError):
            pass

        # Try to get info as a container
        try:
            result = subprocess.run(
                ["docker", "container", "inspect", package_name],
                capture_output=True,
                text=True,
                check=True,
            )

            container_data = json.loads(result.stdout)[0]
            state = container_data.get("State", {})
            config = container_data.get("Config", {})

            return {
                "name": package_name,
                "type": "container",
                "id": container_data.get("Id", "unknown"),
                "image": config.get("Image", "unknown"),
                "created": container_data.get("Created", "unknown"),
                "status": state.get("Status", "unknown"),
                "running": str(state.get("Running", False)),
                "restart_count": str(state.get("RestartCount", 0)),
                "platform": container_data.get("Platform", "unknown"),
            }
        except (subprocess.CalledProcessError, json.JSONDecodeError, IndexError):
            pass

        return None
