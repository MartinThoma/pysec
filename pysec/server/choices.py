"""Choices for Django models in pysec server."""

from django.db import models


class PackageRepository(models.TextChoices):
    """
    Package repository choices.

    Must match PackageRepositoryChecker implementations.
    """

    UNKNOWN = "UNKNOWN", "Unknown/Legacy"
    DEBIAN_APT = "DEBIAN_APT", "Debian/Ubuntu APT"
    PYTHON_PIP = "PYTHON_PIP", "Python pip"
    SNAP = "SNAP", "Snap packages"
    HOMEBREW = "HOMEBREW", "Homebrew (macOS)"
    ARCH_PACMAN = "ARCH_PACMAN", "Arch Linux Pacman"
    DOCKER = "DOCKER", "Docker images/containers"
