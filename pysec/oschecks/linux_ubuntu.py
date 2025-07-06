"""Ubuntu-specific security checks for pysec."""

import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from pysec.osbase import BaseSecurityChecker

logger = logging.getLogger(__name__)


class UbuntuSecurityChecker(BaseSecurityChecker):
    @staticmethod
    def is_current_os() -> bool:
        try:
            with Path("/etc/os-release").open() as f:
                for line in f:
                    if line.startswith("ID="):
                        return "ubuntu" in line.lower()
        except Exception:
            pass
        return False

    def get_audit_events(self) -> list[dict[str, str]]:
        """Get audit events from Ubuntu system."""
        events = []

        # Add current client run event
        events.append(
            {
                "timestamp": datetime.now(tz=timezone.utc).isoformat(),
                "event": "pysec_client_run",
            },
        )

        # Get recent login events using last command
        try:
            result = subprocess.run(
                ["last", "-n", "10"],
                capture_output=True,
                text=True,
                check=True,
            )
            events.extend(
                {
                    "timestamp": datetime.now(tz=timezone.utc).isoformat(),
                    "event": f"recent_login: {line.strip()}",
                }
                for line in result.stdout.strip().split("\n")
                if line.strip() and not line.startswith("wtmp")
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.debug("Failed to get login events with 'last' command")

        # Get recent authentication events from auth.log
        try:
            result = subprocess.run(
                ["journalctl", "-u", "ssh", "-n", "5", "--no-pager"],
                capture_output=True,
                text=True,
                check=True,
            )
            events.extend(
                {
                    "timestamp": datetime.now(tz=timezone.utc).isoformat(),
                    "event": f"ssh_auth: {line.strip()}",
                }
                for line in result.stdout.strip().split("\n")
                if line.strip() and ("Accepted" in line or "Failed" in line)
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.debug("Failed to get SSH authentication events")

        # Get recent package installations/updates
        try:
            result = subprocess.run(
                ["journalctl", "-u", "apt-daily", "-n", "3", "--no-pager"],
                capture_output=True,
                text=True,
                check=True,
            )
            events.extend(
                {
                    "timestamp": datetime.now(tz=timezone.utc).isoformat(),
                    "event": f"package_update: {line.strip()}",
                }
                for line in result.stdout.strip().split("\n")
                if line.strip()
                and ("install" in line.lower() or "upgrade" in line.lower())
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.debug("Failed to get package update events")

        return events

    def is_disk_encrypted(self) -> bool:
        # Check if root is on a LUKS volume (simplified)
        try:
            with Path("/proc/mounts").open() as f:
                mounts = f.read()
            return any("/dev/mapper/" in line for line in mounts.splitlines())
        except Exception:
            return False

    def screen_lock_timeout_minutes(self) -> int | None:
        # Try GNOME first (seconds)
        try:
            result = subprocess.run(
                [
                    "gsettings",
                    "get",
                    "org.gnome.desktop.session",
                    "idle-delay",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            seconds = int(result.stdout.strip())
            if seconds > 0:
                return seconds // 60
        except Exception:
            pass

        # Try MATE keys in order (values in minutes)
        try:
            # Check if screen lock is enabled
            enabled_result = subprocess.run(
                [
                    "gsettings",
                    "get",
                    "org.mate.screensaver",
                    "idle-activation-enabled",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            if enabled_result.stdout.strip() != "true":
                return None

            keys = [
                "org.mate.screensaver idle-delay",
                "org.mate.session idle-delay",
            ]
            for key in keys:
                try:
                    result = subprocess.run(
                        ["gsettings", "get", *key.split()],
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    minutes = int(result.stdout.strip())
                    if minutes > 0:
                        return minutes
                except Exception:
                    continue

        except Exception:
            pass

        return None

    def automatic_daily_updates_enabled(self) -> bool:
        """Return True if automatic daily updates are enabled."""
        config_path = Path("/etc/apt/apt.conf.d/20auto-upgrades")
        if not config_path.exists():
            return False

        enabled = {
            "APT::Periodic::Update-Package-Lists": "0",
            "APT::Periodic::Unattended-Upgrade": "0",
        }

        with config_path.open() as f:
            for line in f:
                line = line.strip()
                if line.startswith("//") or not line:
                    continue
                for key in enabled:
                    if line.startswith(key):
                        value = line.split('"')[1]
                        enabled[key] = value

        return (
            enabled["APT::Periodic::Update-Package-Lists"] != "0"
            and enabled["APT::Periodic::Unattended-Upgrade"] != "0"
        )
