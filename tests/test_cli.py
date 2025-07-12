"""Test if the CLI commands work as expected."""

from typer.testing import CliRunner

from pysec.cli import app

runner = CliRunner()


def test_audit_packages() -> None:
    result = runner.invoke(app, ["audit", "packages"])
    assert result.exit_code == 0
    assert "Auditing installed packages..." in result.output


def test_audit_config() -> None:
    result = runner.invoke(app, ["audit", "config"])
    assert result.exit_code == 0
    assert "Running system configuration audit" in result.output


def test_client_configure() -> None:
    result = runner.invoke(
        app,
        [
            "client",
            "configure",
            "--server-url",
            "http://localhost:8000",
            "--token",
            "test-token",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "✓ Client configuration saved successfully" in result.output


def test_client_run() -> None:
    result = runner.invoke(app, ["client", "run"])
    assert result.exit_code == 0
    assert "Starting pysec client audit..." in result.output
    assert "Submitting audit logs..." in result.output


def test_client_list_repositories() -> None:
    result = runner.invoke(app, ["client", "list-repositories"])
    assert result.exit_code == 0
    assert "Available Package Repositories" in result.output


def test_client_list_packages() -> None:
    result = runner.invoke(app, ["client", "list-packages"])
    assert result.exit_code == 0
    assert "Installed Packages" in result.output
