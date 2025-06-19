"""CLI script to audit system configuration for security best practices."""

import platform

from rich import print

from pysec.oschecks import get_checker


def check_config() -> None:
    """Check the security configuration of the system."""
    checker = get_checker()
    if not checker:
        platform_name = platform.platform().lower()
        print(f"[red]✗ No supported OS checker found: {platform_name}[/red]")
        return

    print(f"- Found checker: {checker.__class__.__name__}")

    print("- Installed packages:", len(checker.get_installed_packages()))

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
