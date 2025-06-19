import typer
from rich import print

from pysec.audit_config import check_config
from pysec.audit_packages import audit_installed_packages

app = typer.Typer(help="pysec: Security tools for your system")

audit_app = typer.Typer(help="Audit system configuration and packages")
app.add_typer(audit_app, name="audit")


@audit_app.command("config")
def audit_config():
    """Check the security configuration of the system."""
    print("[bold cyan]Running system configuration audit...[/bold cyan]")
    check_config()


@audit_app.command("packages")
def audit_packages():
    """Check installed packages for known CVEs."""
    print("[bold cyan]Auditing installed packages...[/bold cyan]")
    audit_installed_packages()


def main():
    app()
