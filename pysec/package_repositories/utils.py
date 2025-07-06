"""Utility functions for working with package repositories."""

import logging

from ._apt import AptPackageRepository
from ._docker import DockerPackageRepository
from ._python import PythonPackageRepository
from .base import PackageRepositoryChecker
from .homebrew import HomebrewPackageRepository
from .pacman import PacmanPackageRepository
from .snap import SnapPackageRepository

logger = logging.getLogger(__name__)


def get_available_repositories() -> list[PackageRepositoryChecker]:
    """
    Get a list of available package repositories on the current system.

    Returns:
        List[PackageRepositoryChecker]: List of available repository checkers.

    """
    repositories = [
        AptPackageRepository(),
        PythonPackageRepository(),
        SnapPackageRepository(),
        DockerPackageRepository(),
        HomebrewPackageRepository(),
        PacmanPackageRepository(),
    ]

    return [repo for repo in repositories if repo.is_available()]


def get_all_installed_packages() -> dict[str, list[dict[str, str]]]:
    """
    Get installed packages from all available repositories.

    Returns:
        dict[str, list[dict[str, str]]]: Dictionary mapping repository type to packages.

    """
    all_packages = {}

    for repo in get_available_repositories():
        repo_type = repo.get_repository_type()
        try:
            packages = repo.get_installed_packages()
            all_packages[repo_type] = packages
        except RuntimeError as e:
            logger.info(f"Warning: Failed to get packages from {repo_type}: {e}")
            all_packages[repo_type] = []

    return all_packages
