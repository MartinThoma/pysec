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


@server_app.command(
    "manage.py",
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def manage_py_cmd(
    ctx: typer.Context,
) -> None:
    """Run Django management commands via manage.py."""
    args = ctx.params.get("args", []) + ctx.args

    if not args:
        print("[red]Error: No management command provided[/red]")
        print("[yellow]Usage: pysec server manage.py <command> [args...][/yellow]")
        print("[yellow]Examples:[/yellow]")
        print("[yellow]  pysec server manage.py runserver[/yellow]")
        print("[yellow]  pysec server manage.py runserver 0.0.0.0:8000[/yellow]")
        print("[yellow]  pysec server manage.py migrate[/yellow]")
        print("[yellow]  pysec server manage.py migrate --plan[/yellow]")
        print("[yellow]  pysec server manage.py createsuperuser[/yellow]")
        print("[yellow]  pysec server manage.py create_client myclient[/yellow]")
        print("[yellow]  pysec server manage.py collectstatic[/yellow]")
        print("[yellow]  pysec server manage.py shell[/yellow]")
        print("[yellow]  pysec server manage.py help[/yellow]")
        raise typer.Exit(1)

    try:
        setup_django()
        project_root = get_project_root()

        # Try to use manage.py if it exists (development mode)
        manage_py = project_root / "manage.py"
        if manage_py.exists():
            cmd = [sys.executable, str(manage_py), *args]
            print(f"[dim]Running: {' '.join(cmd)}[/dim]")
            subprocess.run(
                cmd,
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
            sys.argv = ["manage.py", *args]
            try:
                print(f"[dim]Running Django command: {' '.join(sys.argv)}[/dim]")
                execute_from_command_line(sys.argv)
            finally:
                sys.argv = old_argv

    except ImportError as e:
        print(f"[red]Error: Could not import Django: {e}[/red]")
        print("[red]Make sure Django is installed and pysec is properly set up[/red]")
        raise typer.Exit(1) from e
    except subprocess.CalledProcessError as e:
        print(f"[red]Error running management command: {e}[/red]")
        raise typer.Exit(1) from e
