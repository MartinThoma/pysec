"""Server CLI commands for pysec (Django version)."""

import os
import subprocess
import sys
from pathlib import Path

import typer
from rich import print

server_app = typer.Typer(help="Manage pysec Django server")


def setup_django() -> None:
    """Set up Django environment."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pysec_django.settings")


def get_project_root() -> Path:
    """Get the project root directory where manage.py is located."""
    # First try to find manage.py in parent directories (for development)
    current_file = Path(__file__).resolve()
    for parent in current_file.parents:
        if (parent / "manage.py").exists():
            return parent

    # If not found, we're likely running from an installed package
    # In this case, we'll use the current working directory
    return Path.cwd()


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
        setup_django()
        project_root = get_project_root()

        # Try to use manage.py if it exists (development mode)
        manage_py = project_root / "manage.py"
        if manage_py.exists():
            subprocess.run(
                [
                    sys.executable,
                    str(manage_py),
                    "runserver",
                    f"{host}:{port}",
                ],
                cwd=str(project_root),
                check=True,
            )
        else:
            # Use Django management directly (installed package mode)
            import django  # noqa: PLC0415
            from django.conf import settings  # noqa: PLC0415, F401
            from django.core.management import execute_from_command_line  # noqa: PLC0415

            # Initialize Django
            django.setup()

            old_argv = sys.argv
            sys.argv = ["manage.py", "runserver", f"{host}:{port}"]
            try:
                execute_from_command_line(sys.argv)
            finally:
                sys.argv = old_argv

    except ImportError as e:
        print(f"[red]Error: Could not import Django: {e}[/red]")
        print("[red]Make sure Django is installed and pysec is properly set up[/red]")
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
        setup_django()
        project_root = get_project_root()

        # Try to use manage.py if it exists (development mode)
        manage_py = project_root / "manage.py"
        if manage_py.exists():
            subprocess.run(
                [
                    sys.executable,
                    str(manage_py),
                    "create_client",
                    name,
                ],
                cwd=str(project_root),
                check=True,
            )
        else:
            # Use Django management directly (installed package mode)
            import django  # noqa: PLC0415
            from django.core.management import execute_from_command_line  # noqa: PLC0415

            # Initialize Django
            django.setup()

            old_argv = sys.argv
            sys.argv = ["manage.py", "create_client", name]
            try:
                execute_from_command_line(sys.argv)
            finally:
                sys.argv = old_argv

    except ImportError as e:
        print(f"[red]Error: Could not import Django: {e}[/red]")
        print("[red]Make sure Django is installed and pysec is properly set up[/red]")
        raise typer.Exit(1) from e
    except subprocess.CalledProcessError as e:
        print(f"[red]Error creating client: {e}[/red]")
        raise typer.Exit(1) from e


@server_app.command("migrate")
def migrate_cmd() -> None:
    """Run Django database migrations."""
    print("[bold cyan]Running Django migrations...[/bold cyan]")
    try:
        setup_django()
        project_root = get_project_root()

        # Try to use manage.py if it exists (development mode)
        manage_py = project_root / "manage.py"
        if manage_py.exists():
            subprocess.run(
                [
                    sys.executable,
                    str(manage_py),
                    "migrate",
                ],
                cwd=str(project_root),
                check=True,
            )
        else:
            # Use Django management directly (installed package mode)
            import django  # noqa: PLC0415
            from django.core.management import execute_from_command_line  # noqa: PLC0415

            # Initialize Django
            django.setup()

            old_argv = sys.argv
            sys.argv = ["manage.py", "migrate"]
            try:
                execute_from_command_line(sys.argv)
            finally:
                sys.argv = old_argv

        print("[green]✓ Migrations completed successfully[/green]")
    except ImportError as e:
        print(f"[red]Error: Could not import Django: {e}[/red]")
        print("[red]Make sure Django is installed and pysec is properly set up[/red]")
        raise typer.Exit(1) from e
    except subprocess.CalledProcessError as e:
        print(f"[red]Error running migrations: {e}[/red]")
        raise typer.Exit(1) from e


@server_app.command("createsuperuser")
def create_superuser_cmd() -> None:
    """Create Django superuser for admin access."""
    print("[bold cyan]Creating Django superuser...[/bold cyan]")
    try:
        setup_django()
        project_root = get_project_root()

        # Try to use manage.py if it exists (development mode)
        manage_py = project_root / "manage.py"
        if manage_py.exists():
            subprocess.run(
                [
                    sys.executable,
                    str(manage_py),
                    "createsuperuser",
                ],
                cwd=str(project_root),
                check=True,
            )
        else:
            # Use Django management directly (installed package mode)
            import django  # noqa: PLC0415
            from django.core.management import execute_from_command_line  # noqa: PLC0415

            # Initialize Django
            django.setup()

            old_argv = sys.argv
            sys.argv = ["manage.py", "createsuperuser"]
            try:
                execute_from_command_line(sys.argv)
            finally:
                sys.argv = old_argv

    except ImportError as e:
        print(f"[red]Error: Could not import Django: {e}[/red]")
        print("[red]Make sure Django is installed and pysec is properly set up[/red]")
        raise typer.Exit(1) from e
    except subprocess.CalledProcessError as e:
        print(f"[red]Error creating superuser: {e}[/red]")
        raise typer.Exit(1) from e
