"""CLI script to audit system configuration for security best practices."""

import platform

from rich import print

from pysec.oschecks import get_checker
from pysec.package_repositories import get_all_installed_packages


def check_config() -> None:
    """Check the security configuration of the system."""
    checker = get_checker()
    if not checker:
        platform_name = platform.platform().lower()
        print(f"[red]✗ No supported OS checker found: {platform_name}[/red]")
        return

    print(f"- Found checker: {checker.__class__.__name__}")

    # Get package count from new repository system
    try:
        repo_packages = get_all_installed_packages()
        total_packages = sum(len(packages) for packages in repo_packages.values())
        print(
            f"- Installed packages: {total_packages} across "
            f"{len(repo_packages)} repository types"
        )
        for repo_type, packages in repo_packages.items():
            print(f"  - {repo_type}: {len(packages)} packages")
    except Exception as e:
        print(f"[yellow]Warning: Failed to get package count: {e}[/yellow]")
        print("- Installed packages: Unable to determine")

    if checker.is_disk_encrypted():
        print("[green]✓ Disk is encrypted[/green]")
    else:
        print("[red]✗ Disk is NOT encrypted[/red]")

    timeout = checker.screen_lock_timeout_minutes()
    if timeout is None:
        print("[red]✗ Screen lock is disabled[/red]")
    else:
        print(f"[green]✓ Screen locks after {timeout} minutes[/green]")

    if checker.automatic_daily_updates_enabled():
        print("[green]✓ Automatic daily updates are enabled[/green]")
    else:
        print("[red]✗ Automatic daily updates are NOT enabled[/red]")
