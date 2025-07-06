"""Tests for pysec server CLI commands."""

import subprocess
import unittest.mock
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from pysec.cli.main import app
from pysec.cli.server import (
    get_project_root,
    server_app,
)


class TestGetProjectRoot:
    """Test the get_project_root function."""

    def test_get_project_root_success(self) -> None:
        """Test successful project root detection."""
        # This should work since we're in the project directory
        root = get_project_root()
        assert isinstance(root, Path)
        assert (root / "manage.py").exists()
        assert root.name == "pysec"

    @patch("pysec.cli.server.Path")
    def test_get_project_root_not_found(self, mock_path: MagicMock) -> None:
        """Test when manage.py is not found."""
        # Mock Path to simulate no manage.py found
        mock_file = MagicMock()
        mock_file.resolve.return_value = mock_file
        mock_file.parents = [MagicMock(), MagicMock()]

        # Mock that manage.py doesn't exist in any parent
        for parent in mock_file.parents:
            (parent / "manage.py").exists.return_value = False

        mock_path.__file__ = "/fake/path/file.py"
        mock_path.return_value = mock_file

        with pytest.raises(FileNotFoundError, match="Could not find manage.py"):
            get_project_root()


class TestStartServerCommand:
    """Test the start server CLI command."""

    @patch("pysec.cli.server.subprocess.run")
    @patch("pysec.cli.server.get_project_root")
    def test_start_server_default_options(
        self,
        mock_get_root: MagicMock,
        mock_subprocess: MagicMock,
    ) -> None:
        """Test start server with default host and port."""
        mock_get_root.return_value = Path("/fake/project/root")
        mock_subprocess.return_value = None

        runner = CliRunner()
        result = runner.invoke(server_app, ["start"])

        assert result.exit_code == 0
        assert "Starting pysec Django server on 127.0.0.1:8000" in result.stdout
        assert "Access the dashboard at: http://127.0.0.1:8000/" in result.stdout
        assert "Access the admin at: http://127.0.0.1:8000/admin/" in result.stdout

        # Check subprocess was called correctly
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args
        assert call_args[0][0] == [
            unittest.mock.ANY,  # sys.executable
            "manage.py",
            "runserver",
            "127.0.0.1:8000",
        ]
        assert Path(call_args[1]["cwd"]) == Path("/fake/project/root")
        assert call_args[1]["check"] is True

    @patch("pysec.cli.server.subprocess.run")
    @patch("pysec.cli.server.get_project_root")
    def test_start_server_custom_options(
        self,
        mock_get_root: MagicMock,
        mock_subprocess: MagicMock,
    ) -> None:
        """Test start server with custom host and port."""
        mock_get_root.return_value = Path("/fake/project/root")
        mock_subprocess.return_value = None

        runner = CliRunner()
        result = runner.invoke(
            server_app, ["start", "--host", "127.0.0.1", "--port", "9000"]
        )

        assert result.exit_code == 0
        assert "Starting pysec Django server on 127.0.0.1:9000" in result.stdout

        # Check subprocess was called with custom options
        call_args = mock_subprocess.call_args
        assert "127.0.0.1:9000" in call_args[0][0]

    @patch("pysec.cli.server.get_project_root")
    def test_start_server_project_not_found(self, mock_get_root: MagicMock) -> None:
        """Test start server when project root is not found."""
        mock_get_root.side_effect = FileNotFoundError("Could not find manage.py")

        runner = CliRunner()
        result = runner.invoke(server_app, ["start"])

        assert result.exit_code == 1
        assert "Error: Could not find manage.py" in result.stdout

    @patch("pysec.cli.server.subprocess.run")
    @patch("pysec.cli.server.get_project_root")
    def test_start_server_subprocess_error(
        self,
        mock_get_root: MagicMock,
        mock_subprocess: MagicMock,
    ) -> None:
        """Test start server when subprocess fails."""
        mock_get_root.return_value = Path("/fake/project/root")
        mock_subprocess.side_effect = subprocess.CalledProcessError(1, "manage.py")

        runner = CliRunner()
        result = runner.invoke(server_app, ["start"])

        assert result.exit_code == 1
        assert "Error starting server:" in result.stdout


class TestCreateClientCommand:
    """Test the create client CLI command."""

    @patch("pysec.cli.server.subprocess.run")
    @patch("pysec.cli.server.get_project_root")
    def test_create_client_success(
        self,
        mock_get_root: MagicMock,
        mock_subprocess: MagicMock,
    ) -> None:
        """Test successful client creation."""
        mock_get_root.return_value = Path("/fake/project/root")
        mock_subprocess.return_value = None

        runner = CliRunner()
        result = runner.invoke(server_app, ["create-client", "test-client"])

        assert result.exit_code == 0

        # Check subprocess was called correctly
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args
        assert call_args[0][0] == [
            unittest.mock.ANY,  # sys.executable
            "manage.py",
            "create_client",
            "test-client",
        ]

    def test_create_client_missing_name(self) -> None:
        """Test create client without providing name."""
        runner = CliRunner(env={"NO_COLOR": "1"})
        result = runner.invoke(server_app, ["create-client"])

        assert result.exit_code != 0  # Typer uses exit code 2 for argument errors
        # Check for the specific error message
        assert "Missing argument 'NAME'" in result.stderr


class TestMigrateCommand:
    """Test the migrate CLI command."""

    @patch("pysec.cli.server.subprocess.run")
    @patch("pysec.cli.server.get_project_root")
    def test_migrate_success(
        self,
        mock_get_root: MagicMock,
        mock_subprocess: MagicMock,
    ) -> None:
        """Test successful migration."""
        mock_get_root.return_value = Path("/fake/project/root")
        mock_subprocess.return_value = None

        runner = CliRunner()
        result = runner.invoke(server_app, ["migrate"])

        assert result.exit_code == 0
        assert "Running Django migrations..." in result.stdout
        assert "✓ Migrations completed successfully" in result.stdout

        # Check subprocess was called correctly
        call_args = mock_subprocess.call_args
        assert call_args[0][0] == [
            unittest.mock.ANY,  # sys.executable
            "manage.py",
            "migrate",
        ]


class TestCreateSuperuserCommand:
    """Test the create superuser CLI command."""

    @patch("pysec.cli.server.subprocess.run")
    @patch("pysec.cli.server.get_project_root")
    def test_create_superuser_success(
        self,
        mock_get_root: MagicMock,
        mock_subprocess: MagicMock,
    ) -> None:
        """Test successful superuser creation."""
        mock_get_root.return_value = Path("/fake/project/root")
        mock_subprocess.return_value = None

        runner = CliRunner()
        result = runner.invoke(server_app, ["createsuperuser"])

        assert result.exit_code == 0
        assert "Creating Django superuser..." in result.stdout

        # Check subprocess was called correctly
        call_args = mock_subprocess.call_args
        assert call_args[0][0] == [
            unittest.mock.ANY,  # sys.executable
            "manage.py",
            "createsuperuser",
        ]


class TestServerAppIntegration:
    """Integration tests for the server app."""

    def test_server_app_help(self) -> None:
        """Test that server app shows help correctly."""
        runner = CliRunner(env={"NO_COLOR": "1"})
        result = runner.invoke(server_app, ["--help"])

        assert result.exit_code == 0
        # No need to strip ANSI codes since we're using NO_COLOR env var
        assert "Manage pysec Django server" in result.stdout
        assert "start" in result.stdout
        assert "create-client" in result.stdout
        assert "migrate" in result.stdout
        assert "createsuperuser" in result.stdout

    def test_start_command_help(self) -> None:
        """Test start command help."""
        runner = CliRunner(env={"NO_COLOR": "1"})
        result = runner.invoke(server_app, ["start", "--help"])

        assert result.exit_code == 0
        # No need to strip ANSI codes since we're using NO_COLOR env var
        assert "Start the pysec Django server" in result.stdout
        assert "-host" in result.stdout
        assert "-port" in result.stdout


# Integration test with the actual CLI
class TestCLIIntegration:
    """Test integration with the main CLI."""

    def test_server_command_exists(self) -> None:
        """Test that server command is available in main CLI."""
        runner = CliRunner(env={"NO_COLOR": "1"})
        result = runner.invoke(app, ["server", "--help"])

        assert result.exit_code == 0
        # No need to strip ANSI codes since we're using NO_COLOR env var
        assert "Manage pysec Django server" in result.stdout
