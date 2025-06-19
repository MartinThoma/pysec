from pysec.oschecks import get_checker
from rich import print
import platform


def check_config():
    checker = get_checker()
    if not checker:
        print(f"[red]✗ No supported OS checker found: {platform.platform().lower()}[/red]")
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
