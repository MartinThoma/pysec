"""Client CLI commands for pysec."""

from typing import Optional

import typer
from rich import print
from rich.console import Console
from rich.table import Table

from pysec.client import ClientConfig, PysecClient
from pysec.package_repositories import (
    get_all_installed_packages,
    get_available_repositories,
)

client_app = typer.Typer(help="Manage pysec client")
console = Console()


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
        config = ClientConfig(server_url=server_url, token=token)
        config.save()
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
        config = ClientConfig.load()
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


@client_app.command("list-repositories")
def list_repositories() -> None:
    """List available package repositories on this system."""
    print("[bold blue]Available Package Repositories[/bold blue]")
    print()

    repos = get_available_repositories()
    if not repos:
        print("[yellow]No package repositories found on this system.[/yellow]")
        return

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Repository Type", style="cyan")
    table.add_column("Class Name", style="green")
    table.add_column("Status", style="yellow")

    for repo in repos:
        repo_type = repo.get_repository_type()
        class_name = repo.__class__.__name__
        table.add_row(repo_type, class_name, "✓ Available")

    console.print(table)


@client_app.command("list-packages")
def list_packages(
    repository: Optional[str] = typer.Option(
        None,
        "--repository",
        "-r",
        help="Filter by repository type (e.g., DEBIAN_APT, PYTHON_PIP)",
    ),
    limit: int = typer.Option(
        50,
        "--limit",
        "-l",
        help="Limit number of packages to display per repository",
    ),
    search: Optional[str] = typer.Option(
        None,
        "--search",
        "-s",
        help="Search for packages containing this term",
    ),
) -> None:
    """List installed packages from available repositories."""
    print("[bold blue]Installed Packages[/bold blue]")
    print()

    try:
        all_packages = get_all_installed_packages()

        if not all_packages:
            print("[yellow]No packages found.[/yellow]")
            return

        for repo_type, packages in all_packages.items():
            # Filter by repository if specified
            if repository and repo_type != repository:
                continue

            # Filter by search term if specified
            filtered_packages = packages
            if search:
                filtered_packages = [
                    pkg
                    for pkg in packages
                    if search.lower() in pkg.get("name", "").lower()
                ]

            if not filtered_packages:
                continue

            print(
                f"[bold green]{repo_type}[/bold green] "
                f"({len(filtered_packages)} packages)"
            )

            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Package Name", style="cyan")
            table.add_column("Version", style="yellow")
            table.add_column("Architecture", style="green")

            # Limit the number of packages displayed
            display_packages = filtered_packages[:limit]

            for package in display_packages:
                name = package.get("name", "unknown")
                version = package.get("version", "unknown")
                arch = package.get("architecture", "N/A")
                table.add_row(name, version, arch)

            console.print(table)

            if len(filtered_packages) > limit:
                remaining = len(filtered_packages) - limit
                print(f"[dim]... and {remaining} more packages[/dim]")

            print()

    except Exception as e:
        print(f"[red]Error retrieving packages: {e}[/red]")
        raise typer.Exit(1) from e
