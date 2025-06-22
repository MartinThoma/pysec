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
