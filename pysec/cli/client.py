"""Client CLI commands for pysec."""

from typing import Optional

import typer
from rich import print

from pysec.client import PysecClient, load_client_config, save_client_config

client_app = typer.Typer(help="Manage pysec client")


@client_app.command("configure")
def configure_client(
    server_url: str = typer.Option(
        ...,
        "--server-url",
        "-s",
        help="URL of the pysec server (e.g., http://localhost:8000)",
    ),
    token: str = typer.Option(
        ...,
        "--token",
        "-t",
        help="Authentication token provided by the server admin",
    ),
) -> None:
    """Configure the pysec client."""
    try:
        save_client_config(server_url, token)
        print("[green]✓ Client configuration saved successfully[/green]")
        print(f"Server URL: {server_url}")
        print("Token: [hidden for security]")
    except Exception as e:
        print(f"[red]Error saving configuration: {e}[/red]")
        raise typer.Exit(1) from e


@client_app.command("run")
def run_client(
    server_url: Optional[str] = typer.Option(
        None,
        "--server-url",
        "-s",
        help="URL of the pysec server (overrides config file)",
    ),
    token: Optional[str] = typer.Option(
        None,
        "--token",
        "-t",
        help="Authentication token (overrides config file)",
    ),
) -> None:
    """Run the pysec client audit and submit data to server."""
    # Load from config file if not provided via command line
    if not server_url or not token:
        config = load_client_config()
        if not config:
            print(
                "[red]No client configuration found. "
                "Run 'pysec client configure' first.[/red]",
            )
            raise typer.Exit(1)

        server_url = server_url or config.server_url
        token = token or config.token

    if not server_url or not token:
        print("[red]Server URL and token are required. Use --help for details.[/red]")
        raise typer.Exit(1)

    try:
        client = PysecClient(server_url, token)
        client.run_audit()
    except Exception as e:
        print(f"[red]Error running client audit: {e}[/red]")
        raise typer.Exit(1) from e
