"""Tests for pysec server CLI commands using pytest fixtures."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from pysec.cli.main import app
from pysec.cli.server import (
    get_project_root,
    server_app,
)


@pytest.fixture
def cli_runner() -> CliRunner:
    """Provide a CLI runner for testing."""
    return CliRunner(env={"NO_COLOR": "1"})


# Tests for get_project_root function


def test_get_project_root_success() -> None:
    """Test successful project root detection."""
    # This should work since we're in the project directory
    root = get_project_root()
    assert isinstance(root, Path)
    # In development mode, manage.py should exist
    # In installed mode, it returns cwd
    assert root.exists()


@patch("pysec.cli.server.Path")
def test_get_project_root_fallback_to_cwd(mock_path) -> None:
    """Test when manage.py is not found, falls back to cwd."""
    # Mock Path to simulate no manage.py found
    mock_file = MagicMock()
    mock_file.resolve.return_value = mock_file
    mock_file.parents = [MagicMock(), MagicMock()]

    # Mock that manage.py doesn't exist in any parent
    for parent in mock_file.parents:
        (parent / "manage.py").exists.return_value = False

    mock_path.__file__ = "/fake/path/file.py"
    mock_path.return_value = mock_file

    # Mock Path.cwd() to return a known path
    mock_cwd = Path("/current/working/dir")
    mock_path.cwd.return_value = mock_cwd

    result = get_project_root()
    assert result == mock_cwd


# Tests for start server command


@patch("pysec.cli.server.subprocess.run")
@patch("pysec.cli.server.get_project_root")
def test_start_server_default_options_with_manage_py(
    mock_get_root, mock_subprocess, cli_runner
) -> None:
    """Test start server with default host and port using manage.py."""
    # Set up mocks
    mock_project_root = Path("/fake/project/root")
    mock_get_root.return_value = mock_project_root

    # Mock that manage.py exists
    with patch.object(Path, "exists") as mock_exists:
        mock_exists.return_value = True

        result = cli_runner.invoke(server_app, ["start"])

        assert result.exit_code == 0
        assert "Starting pysec Django server on 127.0.0.1:8000" in result.stdout
        assert "Access the dashboard at: http://127.0.0.1:8000/" in result.stdout
        assert "Access the admin at: http://127.0.0.1:8000/admin/" in result.stdout

        # Check subprocess was called correctly
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args
        command_list = call_args[0][0]
        assert len(command_list) == 4  # noqa: PLR2004
        assert command_list[1].endswith("manage.py")
        assert command_list[2] == "runserver"
        assert command_list[3] == "127.0.0.1:8000"


@patch("pysec.cli.server.setup_django")
@patch("django.core.management.execute_from_command_line")
@patch("django.setup")
@patch("pysec.cli.server.get_project_root")
def test_start_server_default_options_without_manage_py(
    mock_get_root, mock_django_setup, mock_execute, mock_setup_django, cli_runner
) -> None:
    """Test start server with default host and port using Django directly."""
    # Set up mocks
    mock_project_root = Path("/fake/project/root")
    mock_get_root.return_value = mock_project_root

    # Mock that manage.py doesn't exist
    with patch.object(Path, "exists") as mock_exists:
        mock_exists.return_value = False

        result = cli_runner.invoke(server_app, ["start"])

        assert result.exit_code == 0
        assert "Starting pysec Django server on 127.0.0.1:8000" in result.stdout

        # Check Django setup was called
        mock_setup_django.assert_called_once()
        mock_django_setup.assert_called_once()
        mock_execute.assert_called_once()


@patch("pysec.cli.server.subprocess.run")
@patch("pysec.cli.server.get_project_root")
def test_start_server_custom_options(mock_get_root, mock_subprocess, cli_runner) -> None:
    """Test start server with custom host and port."""
    # Set up mocks
    mock_project_root = Path("/fake/project/root")
    mock_get_root.return_value = mock_project_root

    # Mock that manage.py exists
    with patch.object(Path, "exists") as mock_exists:
        mock_exists.return_value = True

        result = cli_runner.invoke(
            server_app, ["start", "--host", "127.0.0.1", "--port", "9000"]
        )

        assert result.exit_code == 0
        assert "Starting pysec Django server on 127.0.0.1:9000" in result.stdout

        # Check subprocess was called with custom options
        call_args = mock_subprocess.call_args
        command_list = call_args[0][0]
        assert "127.0.0.1:9000" in command_list


@patch("pysec.cli.server.subprocess.run")
@patch("pysec.cli.server.get_project_root")
def test_start_server_subprocess_error(
    mock_get_root, mock_subprocess, cli_runner
) -> None:
    """Test start server when subprocess fails."""
    # Set up mocks
    mock_project_root = Path("/fake/project/root")
    mock_get_root.return_value = mock_project_root
    mock_subprocess.side_effect = subprocess.CalledProcessError(1, "manage.py")

    # Mock that manage.py exists
    with patch.object(Path, "exists") as mock_exists:
        mock_exists.return_value = True

        result = cli_runner.invoke(server_app, ["start"])

        assert result.exit_code == 1
        assert "Error starting server:" in result.stdout


@patch("pysec.cli.server.get_project_root")
def test_start_server_django_import_error(mock_get_root, cli_runner) -> None:
    """Test start server when Django import fails."""
    # Set up mocks
    mock_project_root = Path("/fake/project/root")
    mock_get_root.return_value = mock_project_root

    # Mock that manage.py doesn't exist and Django import fails
    with (
        patch.object(Path, "exists") as mock_exists,
        patch(
            "pysec.cli.server.setup_django", side_effect=ImportError("Django not found")
        ),
    ):
        mock_exists.return_value = False

        result = cli_runner.invoke(server_app, ["start"])

        assert result.exit_code == 1
        assert "Error: Could not import Django" in result.stdout


# Tests for create client command


@patch("pysec.cli.server.subprocess.run")
@patch("pysec.cli.server.get_project_root")
def test_create_client_success_with_manage_py(
    mock_get_root, mock_subprocess, cli_runner
) -> None:
    """Test successful client creation using manage.py."""
    # Set up mocks
    mock_project_root = Path("/fake/project/root")
    mock_get_root.return_value = mock_project_root

    # Mock that manage.py exists
    with patch.object(Path, "exists") as mock_exists:
        mock_exists.return_value = True

        result = cli_runner.invoke(server_app, ["create-client", "test-client"])

        assert result.exit_code == 0

        # Check subprocess was called correctly
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args
        command_list = call_args[0][0]
        assert len(command_list) == 4  # noqa: PLR2004
        assert command_list[1].endswith("manage.py")
        assert command_list[2] == "create_client"
        assert command_list[3] == "test-client"


@patch("pysec.cli.server.setup_django")
@patch("django.core.management.execute_from_command_line")
@patch("django.setup")
@patch("pysec.cli.server.get_project_root")
def test_create_client_success_without_manage_py(
    mock_get_root, mock_django_setup, mock_execute, mock_setup_django, cli_runner
) -> None:
    """Test successful client creation using Django directly."""
    # Set up mocks
    mock_project_root = Path("/fake/project/root")
    mock_get_root.return_value = mock_project_root

    # Mock that manage.py doesn't exist
    with patch.object(Path, "exists") as mock_exists:
        mock_exists.return_value = False

        result = cli_runner.invoke(server_app, ["create-client", "test-client"])

        assert result.exit_code == 0

        # Check Django setup was called
        mock_setup_django.assert_called_once()
        mock_django_setup.assert_called_once()
        mock_execute.assert_called_once()


def test_create_client_missing_name(cli_runner) -> None:
    """Test create client without providing name."""
    result = cli_runner.invoke(server_app, ["create-client"])

    assert result.exit_code != 0  # Typer uses exit code 2 for argument errors
    # Check for the specific error message in stderr
    assert "Missing argument 'NAME'" in result.stderr


# Tests for migrate command


@patch("pysec.cli.server.subprocess.run")
@patch("pysec.cli.server.get_project_root")
def test_migrate_success_with_manage_py(
    mock_get_root, mock_subprocess, cli_runner
) -> None:
    """Test successful migration using manage.py."""
    # Set up mocks
    mock_project_root = Path("/fake/project/root")
    mock_get_root.return_value = mock_project_root

    # Mock that manage.py exists
    with patch.object(Path, "exists") as mock_exists:
        mock_exists.return_value = True

        result = cli_runner.invoke(server_app, ["migrate"])

        assert result.exit_code == 0
        assert "Running Django migrations..." in result.stdout
        assert "✓ Migrations completed successfully" in result.stdout

        # Check subprocess was called correctly
        call_args = mock_subprocess.call_args
        command_list = call_args[0][0]
        assert len(command_list) == 3  # noqa: PLR2004
        assert command_list[1].endswith("manage.py")
        assert command_list[2] == "migrate"


@patch("pysec.cli.server.setup_django")
@patch("django.core.management.execute_from_command_line")
@patch("django.setup")
@patch("pysec.cli.server.get_project_root")
def test_migrate_success_without_manage_py(
    mock_get_root, mock_django_setup, mock_execute, mock_setup_django, cli_runner
) -> None:
    """Test successful migration using Django directly."""
    # Set up mocks
    mock_project_root = Path("/fake/project/root")
    mock_get_root.return_value = mock_project_root

    # Mock that manage.py doesn't exist
    with patch.object(Path, "exists") as mock_exists:
        mock_exists.return_value = False

        result = cli_runner.invoke(server_app, ["migrate"])

        assert result.exit_code == 0
        assert "Running Django migrations..." in result.stdout
        assert "✓ Migrations completed successfully" in result.stdout

        # Check Django setup was called
        mock_setup_django.assert_called_once()
        mock_django_setup.assert_called_once()
        mock_execute.assert_called_once()


# Tests for create superuser command


@patch("pysec.cli.server.subprocess.run")
@patch("pysec.cli.server.get_project_root")
def test_create_superuser_success_with_manage_py(
    mock_get_root, mock_subprocess, cli_runner
) -> None:
    """Test successful superuser creation using manage.py."""
    # Set up mocks
    mock_project_root = Path("/fake/project/root")
    mock_get_root.return_value = mock_project_root

    # Mock that manage.py exists
    with patch.object(Path, "exists") as mock_exists:
        mock_exists.return_value = True

        result = cli_runner.invoke(server_app, ["createsuperuser"])

        assert result.exit_code == 0
        assert "Creating Django superuser..." in result.stdout

        # Check subprocess was called correctly
        call_args = mock_subprocess.call_args
        command_list = call_args[0][0]
        assert len(command_list) == 3  # noqa: PLR2004
        assert command_list[1].endswith("manage.py")
        assert command_list[2] == "createsuperuser"


@patch("pysec.cli.server.setup_django")
@patch("django.core.management.execute_from_command_line")
@patch("django.setup")
@patch("pysec.cli.server.get_project_root")
def test_create_superuser_success_without_manage_py(
    mock_get_root, mock_django_setup, mock_execute, mock_setup_django, cli_runner
) -> None:
    """Test successful superuser creation using Django directly."""
    # Set up mocks
    mock_project_root = Path("/fake/project/root")
    mock_get_root.return_value = mock_project_root

    # Mock that manage.py doesn't exist
    with patch.object(Path, "exists") as mock_exists:
        mock_exists.return_value = False

        result = cli_runner.invoke(server_app, ["createsuperuser"])

        assert result.exit_code == 0
        assert "Creating Django superuser..." in result.stdout

        # Check Django setup was called
        mock_setup_django.assert_called_once()
        mock_django_setup.assert_called_once()
        mock_execute.assert_called_once()


# Integration tests


def test_server_app_help(cli_runner) -> None:
    """Test that server app shows help correctly."""
    result = cli_runner.invoke(server_app, ["--help"])

    assert result.exit_code == 0
    assert "Manage pysec Django server" in result.stdout
    assert "start" in result.stdout
    assert "create-client" in result.stdout
    assert "migrate" in result.stdout
    assert "createsuperuser" in result.stdout


def test_start_command_help(cli_runner) -> None:
    """Test start command help."""
    result = cli_runner.invoke(server_app, ["start", "--help"])

    assert result.exit_code == 0
    assert "Start the pysec Django server" in result.stdout
    assert "-host" in result.stdout  # only one "-" as CI fails otherwise
    assert "-port" in result.stdout  # only one "-" as CI fails otherwise


def test_server_command_exists_in_main_cli(cli_runner) -> None:
    """Test that server command is available in main CLI."""
    result = cli_runner.invoke(app, ["server", "--help"])

    assert result.exit_code == 0
    assert "Manage pysec Django server" in result.stdout
