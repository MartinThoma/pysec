"""Server CLI commands for pysec."""

import typer
from rich import print

from pysec.config import get_or_create_server_config, get_server_config_file
from pysec.server.app import start_server

server_app = typer.Typer(help="Manage pysec server")


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
    reload: bool = typer.Option(
        False,
        "--reload",
        help="Enable auto-reload for development",
    ),
) -> None:
    """Start the pysec web server."""
    print(f"[bold cyan]Starting pysec server on {host}:{port}[/bold cyan]")
    config_file = get_server_config_file()
    print(f"[yellow]Admin config stored at: {config_file}[/yellow]")
    print(f"[yellow]Access the dashboard at: http://{host}:{port}[/yellow]")
    start_server(host=host, port=port, reload=reload)


@server_app.command("admin-password")
def show_admin_password() -> None:
    """Show the admin password for the dashboard."""
    try:
        server_config = get_or_create_server_config()
        config_file = get_server_config_file()
        print(f"[bold green]Admin password:[/bold green] {server_config.admin_password}")
        print(f"[dim]Config stored at: {config_file}[/dim]")
    except Exception as e:
        print(f"[bold red]Error getting admin password:[/bold red] {e}")
        typer.Exit(1)
