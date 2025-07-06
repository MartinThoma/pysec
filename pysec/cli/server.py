"""Server CLI commands for pysec (Django version)."""

import subprocess
import sys
from pathlib import Path

import typer
from rich import print

server_app = typer.Typer(help="Manage pysec Django server")


def get_project_root() -> Path:
    """Get the project root directory where manage.py is located."""
    # Start from the current file and go up to find manage.py
    current_file = Path(__file__).resolve()
    for parent in current_file.parents:
        if (parent / "manage.py").exists():
            return parent
    raise FileNotFoundError("Could not find manage.py in parent directories")


@server_app.command("start")
def start_server_cmd(
    host: str = typer.Option(
        "127.0.0.1",
        "--host",
        "-h",
        help="Host to bind the server to",
    ),
    port: int = typer.Option(
        8000,
        "--port",
        "-p",
        help="Port to bind the server to",
    ),
) -> None:
    """Start the pysec Django server."""
    print(f"[bold cyan]Starting pysec Django server on {host}:{port}[/bold cyan]")
    print(f"[yellow]Access the dashboard at: http://{host}:{port}/[/yellow]")
    print(f"[yellow]Access the admin at: http://{host}:{port}/admin/[/yellow]")

    try:
        project_root = get_project_root()
        # Use Django's management command from the correct directory
        subprocess.run(
            [
                sys.executable,
                "manage.py",
                "runserver",
                f"{host}:{port}",
            ],
            cwd=str(project_root),
            check=True,
        )
    except FileNotFoundError as e:
        print(f"[red]Error: {e}[/red]")
        print(
            "[red]Make sure you're running this from the pysec project directory[/red]",
        )
        raise typer.Exit(1) from e
    except subprocess.CalledProcessError as e:
        print(f"[red]Error starting server: {e}[/red]")
        raise typer.Exit(1) from e


@server_app.command("create-client")
def create_client_cmd(
    name: str = typer.Argument(..., help="Name of the client to create"),
) -> None:
    """Create a new client with authentication token."""
    try:
        project_root = get_project_root()
        subprocess.run(
            [
                sys.executable,
                "manage.py",
                "create_client",
                name,
            ],
            cwd=str(project_root),
            check=True,
        )
    except FileNotFoundError as e:
        print(f"[red]Error: {e}[/red]")
        print(
            "[red]Make sure you're running this from the pysec project directory[/red]",
        )
        raise typer.Exit(1) from e
    except subprocess.CalledProcessError as e:
        print(f"[red]Error creating client: {e}[/red]")
        raise typer.Exit(1) from e


@server_app.command("migrate")
def migrate_cmd() -> None:
    """Run Django database migrations."""
    print("[bold cyan]Running Django migrations...[/bold cyan]")
    try:
        project_root = get_project_root()
        subprocess.run(
            [
                sys.executable,
                "manage.py",
                "migrate",
            ],
            cwd=str(project_root),
            check=True,
        )
        print("[green]✓ Migrations completed successfully[/green]")
    except FileNotFoundError as e:
        print(f"[red]Error: {e}[/red]")
        print(
            "[red]Make sure you're running this from the pysec project directory[/red]",
        )
        raise typer.Exit(1) from e
    except subprocess.CalledProcessError as e:
        print(f"[red]Error running migrations: {e}[/red]")
        raise typer.Exit(1) from e


@server_app.command("createsuperuser")
def create_superuser_cmd() -> None:
    """Create Django superuser for admin access."""
    print("[bold cyan]Creating Django superuser...[/bold cyan]")
    try:
        project_root = get_project_root()
        subprocess.run(
            [
                sys.executable,
                "manage.py",
                "createsuperuser",
            ],
            cwd=str(project_root),
            check=True,
        )
    except FileNotFoundError as e:
        print(f"[red]Error: {e}[/red]")
        print(
            "[red]Make sure you're running this from the pysec project directory[/red]",
        )
        raise typer.Exit(1) from e
    except subprocess.CalledProcessError as e:
        print(f"[red]Error creating superuser: {e}[/red]")
        raise typer.Exit(1) from e
