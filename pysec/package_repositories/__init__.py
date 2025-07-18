"""Package repository checkers for various package management systems."""

from ._apt import AptPackageRepository
from ._docker import DockerPackageRepository
from ._python import PythonPackageRepository
from .base import PackageRepositoryChecker
from .homebrew import HomebrewPackageRepository
from .pacman import PacmanPackageRepository
from .snap import SnapPackageRepository
from .utils import (
    get_all_installed_packages,
    get_available_repositories,
)

__all__ = [
    "AptPackageRepository",
    "DockerPackageRepository",
    "HomebrewPackageRepository",
    "PackageRepositoryChecker",
    "PacmanPackageRepository",
    "PythonPackageRepository",
    "SnapPackageRepository",
    "get_all_installed_packages",
    "get_available_repositories",
]
