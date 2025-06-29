"""Client functionality for pysec."""

import json
import subprocess
import sys
from typing import Any

import requests
from pydantic import BaseModel, ValidationError
from rich import print

from pysec.config import ensure_directory, get_client_config_file
from pysec.oschecks import get_checker


class ClientConfig(BaseModel):
    """Pydantic model for client configuration."""

    server_url: str
    token: str

    @classmethod
    def load(cls) -> "ClientConfig | None":
        """Load client configuration from file."""
        config_file = get_client_config_file()

        if not config_file.exists():
            return None

        try:
            with config_file.open() as f:
                config_data = json.load(f)
            return cls(**config_data)
        except (OSError, json.JSONDecodeError, ValidationError) as e:
            print(f"[yellow]Warning: Failed to load client config: {e}[/yellow]")
            return None

    def save(self) -> None:
        """Save client configuration to file."""
        config_file = get_client_config_file()
        ensure_directory(config_file.parent)

        with config_file.open("w") as f:
            json.dump(self.model_dump(), f, indent=2)

        # Set restrictive permissions
        config_file.chmod(0o600)


def get_installed_packages() -> list[dict[str, str]]:
    """Get list of installed packages and their versions using OS-specific checker."""
    checker = get_checker()
    if checker:
        try:
            return checker.get_installed_packages()
        except Exception as e:
            print(
                f"[yellow]Warning: OS-specific package collection failed: {e}[/yellow]",
            )

    # Fallback to basic pip packages if OS checker is not available
    packages = []
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "list", "--format=json"],
            capture_output=True,
            text=True,
            check=True,
        )
        pip_packages = json.loads(result.stdout)
        packages.extend(
            [{"name": pkg["name"], "version": pkg["version"]} for pkg in pip_packages],
        )
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        print("[yellow]Warning: Could not get pip packages[/yellow]")

    return packages


def get_audit_events() -> list[dict[str, str]]:
    """Get audit events from the system using OS-specific checker."""
    checker = get_checker()
    if not checker:
        return []
    try:
        return checker.get_audit_events()
    except Exception as e:
        print(
            f"[yellow]Warning: OS-specific audit event collection failed: {e}[/yellow]",
        )
    return []


class PysecClient:
    """Client for communicating with pysec server."""

    def __init__(self, server_url: str, token: str) -> None:
        """Initialize client."""
        self.server_url = server_url.rstrip("/")
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def submit_audit_logs(self, events: list[dict[str, str]]) -> bool:
        """Submit audit logs to server."""
        try:
            for event in events:
                data = {
                    "timestamp": event["timestamp"],
                    "event": event["event"],
                }
                response = requests.post(
                    f"{self.server_url}/api/audit-log",
                    headers=self.headers,
                    json=data,
                    timeout=30,
                )
                response.raise_for_status()
            return True
        except requests.RequestException as e:
            print(f"[red]Error submitting audit logs: {e}[/red]")
            return False

    def submit_packages(self, packages: list[dict[str, str]]) -> bool:
        """Submit package list to server."""
        try:
            data = {"packages": packages}
            response = requests.post(
                f"{self.server_url}/api/packages",
                headers=self.headers,
                json=data,
                timeout=30,
            )
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            print(f"[red]Error submitting packages: {e}[/red]")
            return False

    def get_security_info(self) -> dict[str, Any]:
        """Get security information using OS-specific checker."""
        security_info: dict[str, bool | str | int | None] = {}
        checker = get_checker()

        if checker:
            try:
                security_info["disk_encrypted"] = checker.is_disk_encrypted()
                security_info["screen_lock_timeout"] = (
                    checker.screen_lock_timeout_minutes()
                )
                security_info["auto_updates_enabled"] = (
                    checker.automatic_daily_updates_enabled()
                )
                security_info["os_checker_available"] = True
            except Exception as e:
                print(f"[yellow]Warning: Failed to collect security info: {e}[/yellow]")
                security_info["os_checker_available"] = False
                security_info["error"] = str(e)
        else:
            security_info["os_checker_available"] = False
            security_info["error"] = "No OS-specific checker available"

        return security_info

    def submit_security_info(self, security_info: dict[str, Any]) -> bool:
        """Submit security information to server."""
        try:
            response = requests.post(
                f"{self.server_url}/api/security-info",
                headers=self.headers,
                json=security_info,
                timeout=30,
            )
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            print(f"[red]Error submitting security info: {e}[/red]")
            return False

    def run_audit(self) -> None:
        """Run full audit and submit to server."""
        print("[bold cyan]Starting pysec client audit...[/bold cyan]")

        # Get audit events
        print("Collecting audit events...")
        events = get_audit_events()
        print(f"Found {len(events)} audit events")

        # Submit audit logs
        if events:
            print("Submitting audit logs...")
            if self.submit_audit_logs(events):
                print("[green]✓ Audit logs submitted successfully[/green]")
            else:
                print("[red]✗ Failed to submit audit logs[/red]")

        # Get installed packages
        print("Collecting installed packages...")
        packages = get_installed_packages()
        print(f"Found {len(packages)} packages")

        # Submit packages
        if packages:
            print("Submitting package list...")
            if self.submit_packages(packages):
                print("[green]✓ Package list submitted successfully[/green]")
            else:
                print("[red]✗ Failed to submit package list[/red]")

        # Get security information
        print("Collecting security information...")
        security_info = self.get_security_info()
        print(f"Security info collected: {list(security_info.keys())}")

        # Submit security information
        print("Submitting security information...")
        if self.submit_security_info(security_info):
            print("[green]✓ Security information submitted successfully[/green]")
        else:
            print("[red]✗ Failed to submit security information[/red]")

        print("[bold green]Audit complete![/bold green]")
