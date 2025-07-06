"""Tests for package repository checkers."""

from unittest.mock import MagicMock, patch

import pytest

from pysec.client import get_installed_packages
from pysec.package_repositories import (
    AptPackageRepository,
    PackageRepositoryChecker,
    PythonPackageRepository,
    get_available_repositories,
)
from pysec.server.serializers import PackagesListSerializer


class MockRepository(PackageRepositoryChecker):
    """Mock repository for testing."""

    REPOSITORY_TYPE = "MOCK_REPO"

    def __init__(self, *, available: bool = True) -> None:
        self._available = available

    def is_available(self) -> bool:
        return self._available

    def get_installed_packages(self) -> list[dict[str, str]]:
        return [
            {
                "name": "test-package",
                "version": "1.0.0",
                "repository_type": self.REPOSITORY_TYPE,
            }
        ]


class TestPackageRepositoryChecker:
    """Test the base package repository checker."""

    def test_abstract_base_class(self) -> None:
        """Test that the base class cannot be instantiated."""
        # This should raise TypeError because it's an abstract class
        with pytest.raises(TypeError):
            PackageRepositoryChecker()

    def test_mock_implementation(self) -> None:
        """Test our mock implementation works."""
        repo = MockRepository()
        assert repo.is_available() is True
        packages = repo.get_installed_packages()
        assert len(packages) == 1
        assert packages[0]["name"] == "test-package"

    def test_get_package_info_default(self) -> None:
        """Test default get_package_info returns None."""
        repo = MockRepository()
        assert repo.get_package_info("any-package") is None

    def test_repository_type_constants(self) -> None:
        """Test that repository classes have proper type constants."""
        # Test that constants are defined
        assert hasattr(AptPackageRepository, "REPOSITORY_TYPE")
        assert hasattr(PythonPackageRepository, "REPOSITORY_TYPE")

        # Test constant values
        assert AptPackageRepository.REPOSITORY_TYPE == "DEBIAN_APT"
        assert PythonPackageRepository.REPOSITORY_TYPE == "PYTHON_PIP"

        # Test classmethod
        assert AptPackageRepository.get_repository_type() == "DEBIAN_APT"
        assert PythonPackageRepository.get_repository_type() == "PYTHON_PIP"


class TestAptPackageRepository:
    """Test APT package repository implementation."""

    @patch("shutil.which")
    def test_is_available_with_apt(self, mock_which) -> None:
        """Test availability when apt is present."""
        mock_which.side_effect = lambda cmd: "/usr/bin/apt" if cmd == "apt" else None

        repo = AptPackageRepository()
        assert repo.is_available() is True

    @patch("shutil.which")
    def test_is_available_with_apt_get(self, mock_which) -> None:
        """Test availability when only apt-get is present."""
        mock_which.side_effect = (
            lambda cmd: "/usr/bin/apt-get" if cmd == "apt-get" else None
        )

        repo = AptPackageRepository()
        assert repo.is_available() is True

    @patch("shutil.which")
    def test_is_not_available(self, mock_which) -> None:
        """Test when APT is not available."""
        mock_which.return_value = None

        repo = AptPackageRepository()
        assert repo.is_available() is False

    @patch("shutil.which")
    def test_get_packages_when_not_available(self, mock_which) -> None:
        """Test error when trying to get packages without APT."""
        mock_which.return_value = None

        repo = AptPackageRepository()
        with pytest.raises(RuntimeError, match="APT is not available"):
            repo.get_installed_packages()


class TestPythonPackageRepository:
    """Test Python package repository implementation."""

    @patch("shutil.which")
    def test_is_available_with_pip3(self, mock_which) -> None:
        """Test availability when pip3 is present."""
        mock_which.side_effect = lambda cmd: "/usr/bin/pip3" if cmd == "pip3" else None

        repo = PythonPackageRepository()
        assert repo.is_available() is True

    @patch("shutil.which")
    def test_is_available_with_pip(self, mock_which) -> None:
        """Test availability when pip is present."""
        mock_which.side_effect = lambda cmd: "/usr/bin/pip" if cmd == "pip" else None

        repo = PythonPackageRepository()
        assert repo.is_available() is True

    @patch("shutil.which")
    def test_is_not_available(self, mock_which) -> None:
        """Test when pip is not available."""
        mock_which.return_value = None

        repo = PythonPackageRepository()
        assert repo.is_available() is False

    @patch("shutil.which")
    def test_get_packages_when_not_available(self, mock_which) -> None:
        """Test error when trying to get packages without pip."""
        mock_which.return_value = None

        repo = PythonPackageRepository()
        with pytest.raises(RuntimeError, match="pip is not available"):
            repo.get_installed_packages()


class TestUtilityFunctions:
    """Test utility functions."""

    @patch("pysec.package_repositories.utils.PacmanPackageRepository")
    @patch("pysec.package_repositories.utils.HomebrewPackageRepository")
    @patch("pysec.package_repositories.utils.SnapPackageRepository")
    @patch("pysec.package_repositories.utils.AptPackageRepository")
    @patch("pysec.package_repositories.utils.PythonPackageRepository")
    def test_get_available_repositories(
        self,
        mock_python_repo,
        mock_apt_repo,
        mock_snap_repo,
        mock_homebrew_repo,
        mock_pacman_repo,
    ) -> None:
        """Test getting available repositories."""
        # Mock only APT and Python as available, others as not available
        mock_apt_instance = MagicMock()
        mock_apt_instance.is_available.return_value = True
        mock_apt_repo.return_value = mock_apt_instance

        mock_python_instance = MagicMock()
        mock_python_instance.is_available.return_value = True
        mock_python_repo.return_value = mock_python_instance

        mock_snap_instance = MagicMock()
        mock_snap_instance.is_available.return_value = False
        mock_snap_repo.return_value = mock_snap_instance

        mock_homebrew_instance = MagicMock()
        mock_homebrew_instance.is_available.return_value = False
        mock_homebrew_repo.return_value = mock_homebrew_instance

        mock_pacman_instance = MagicMock()
        mock_pacman_instance.is_available.return_value = False
        mock_pacman_repo.return_value = mock_pacman_instance

        repos = get_available_repositories()
        assert len(repos) == 2  # noqa: PLR2004

    @patch("pysec.package_repositories.utils.PacmanPackageRepository")
    @patch("pysec.package_repositories.utils.HomebrewPackageRepository")
    @patch("pysec.package_repositories.utils.SnapPackageRepository")
    @patch("pysec.package_repositories.utils.AptPackageRepository")
    @patch("pysec.package_repositories.utils.PythonPackageRepository")
    def test_get_available_repositories_partial(
        self,
        mock_python_repo,
        mock_apt_repo,
        mock_snap_repo,
        mock_homebrew_repo,
        mock_pacman_repo,
    ) -> None:
        """Test getting available repositories when only one is available."""
        # Mock APT as available, others as not available
        mock_apt_instance = MagicMock()
        mock_apt_instance.is_available.return_value = True
        mock_apt_repo.return_value = mock_apt_instance

        mock_python_instance = MagicMock()
        mock_python_instance.is_available.return_value = False
        mock_python_repo.return_value = mock_python_instance

        mock_snap_instance = MagicMock()
        mock_snap_instance.is_available.return_value = False
        mock_snap_repo.return_value = mock_snap_instance

        mock_homebrew_instance = MagicMock()
        mock_homebrew_instance.is_available.return_value = False
        mock_homebrew_repo.return_value = mock_homebrew_instance

        mock_pacman_instance = MagicMock()
        mock_pacman_instance.is_available.return_value = False
        mock_pacman_repo.return_value = mock_pacman_instance

        repos = get_available_repositories()
        assert len(repos) == 1


class TestClientPackageSubmission:
    """Test client package submission functionality."""

    def test_client_package_format(self) -> None:
        """Test that client packages have correct format for server."""
        # Mock the repository functions
        with patch("pysec.client.get_all_installed_packages") as mock_get_all:
            mock_get_all.return_value = {
                "DEBIAN_APT": [
                    {
                        "name": "libc6",
                        "version": "2.31-0ubuntu9.9",
                        "repository_type": "DEBIAN_APT",
                    }
                ],
                "PYTHON_PIP": [
                    {
                        "name": "requests",
                        "version": "2.28.1",
                        "repository_type": "PYTHON_PIP",
                    }
                ],
            }

            packages = get_installed_packages()

            # Check that packages have required fields
            assert len(packages) == 2  # noqa: PLR2004
            for pkg in packages:
                assert "name" in pkg
                assert "version" in pkg
                assert "package_repository" in pkg

            # Check specific values
            apt_pkg = next(p for p in packages if p["name"] == "libc6")
            assert apt_pkg["package_repository"] == "DEBIAN_APT"

            pip_pkg = next(p for p in packages if p["name"] == "requests")
            assert pip_pkg["package_repository"] == "PYTHON_PIP"

    def test_client_package_format_with_fallback(self) -> None:
        """Test client package format when repository system fails."""
        # Mock repository system to fail, then test fallback
        with patch("pysec.client.get_all_installed_packages") as mock_get_all:
            mock_get_all.side_effect = Exception("Repository system failed")

            with patch("pysec.client.get_checker") as mock_get_checker:
                mock_get_checker.return_value = None  # No OS checker

                with patch("subprocess.run") as mock_subprocess:
                    mock_subprocess.return_value.stdout = (
                        '[{"name": "pip-package", "version": "1.0.0"}]'
                    )

                    packages = get_installed_packages()

                    # Should fall back to pip packages with PYTHON_PIP repository type
                    assert len(packages) == 1
                    assert packages[0]["name"] == "pip-package"
                    assert packages[0]["version"] == "1.0.0"
                    assert packages[0]["package_repository"] == "PYTHON_PIP"

    def test_package_serializer_validation(self) -> None:
        """Test that the server serializer accepts our package format."""
        # Test data in the format the client now sends
        test_data = {
            "packages": [
                {
                    "name": "libc6",
                    "version": "2.31-0ubuntu9.9",
                    "package_repository": "DEBIAN_APT",
                },
                {
                    "name": "requests",
                    "version": "2.28.1",
                    "package_repository": "PYTHON_PIP",
                },
            ]
        }

        serializer = PackagesListSerializer(data=test_data)
        is_valid = serializer.is_valid()

        assert is_valid, (
            f"Serializer should be valid but got errors: {serializer.errors}"
        )

        # Test that packages can be accessed after validation
        assert hasattr(serializer, "validated_data")
        packages = test_data["packages"]  # Use original data for verification
        assert len(packages) == 2  # noqa: PLR2004

        for pkg in packages:
            assert "name" in pkg
            assert "version" in pkg
            assert "package_repository" in pkg
