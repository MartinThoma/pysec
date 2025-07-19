"""
CLI for pysec.

The relevant commands are in subcommands which are in submodules.
"""

import typer
from rich import print

from pysec import SeverityLevel
from pysec.cli.audit_config import check_config
from pysec.cli.audit_packages import audit_installed_packages
from pysec.cli.client_cli import client_app
from pysec.cli.server import server_app

app = typer.Typer(help="pysec: Security tools for your system")

audit_app = typer.Typer(help="Audit system configuration and packages")
app.add_typer(audit_app, name="audit")
app.add_typer(server_app, name="server")
app.add_typer(client_app, name="client")


@audit_app.command("config")
def audit_config() -> None:
    """Check the security configuration of the system."""
    print("[bold cyan]Running system configuration audit...[/bold cyan]")
    check_config()


@audit_app.command("packages")
def audit_packages(
    verbosity: int = typer.Option(
        0,
        "--verbose",
        "-v",
        count=True,
        help="Increase verbosity (-v, -vv for more output)",
    ),
    min_severity: SeverityLevel = typer.Option(
        SeverityLevel.LOW,
        "--min-severity",
        help="Minimum CVE severity to report (LOW, MEDIUM, HIGH, CRITICAL)",
    ),
) -> None:
    """Check installed packages for known CVEs."""
    print("[bold cyan]Auditing installed packages...[/bold cyan]")
    audit_installed_packages(verbosity=verbosity, min_severity=min_severity)
