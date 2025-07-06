"""Arch Linux specific security checks for pysec."""

import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from pysec.osbase import BaseSecurityChecker


class ArchLinuxSecurityChecker(BaseSecurityChecker):
    @staticmethod
    def is_current_os() -> bool:
        return Path("/etc/arch-release").exists()

    def get_audit_events(self) -> list[dict[str, str]]:
        """Get audit events from Arch Linux system."""
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
            pass

        # Get recent pacman transactions
        try:
            result = subprocess.run(
                ["journalctl", "-u", "pacman", "-n", "5", "--no-pager"],
                capture_output=True,
                text=True,
                check=True,
            )
            events.extend(
                {
                    "timestamp": datetime.now(tz=timezone.utc).isoformat(),
                    "event": f"pacman: {line.strip()}",
                }
                for line in result.stdout.strip().split("\n")
                if line.strip()
                and ("installed" in line or "upgraded" in line or "removed" in line)
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        # Get recent SSH authentication events
        try:
            result = subprocess.run(
                ["journalctl", "-u", "sshd", "-n", "5", "--no-pager"],
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
            pass

        return events

    def is_disk_encrypted(self) -> bool:
        # Check lsblk for devices using crypt
        try:
            output = subprocess.check_output(
                ["lsblk", "-o", "TYPE,NAME,MOUNTPOINT"],
                text=True,
            )
            for line in output.strip().split("\n"):
                if line.startswith("crypt"):
                    return True
        except Exception:
            pass

        # Fallback: check if /etc/crypttab exists and is non-empty
        crypttab = Path("/etc/crypttab")
        return bool(crypttab.exists() and crypttab.read_text().strip())

    def screen_lock_timeout_minutes(self) -> int | None:
        # Try checking xautolock (common with i3)
        try:
            ps_output = subprocess.check_output(["ps", "aux"], text=True)
            for line in ps_output.splitlines():
                if "xautolock" in line:
                    match = re.search(r"-time\s+(\d+)", line)
                    if match:
                        return int(match.group(1))
        except Exception:
            pass

        # Alternatively check X11 DPMS settings as fallback
        try:
            xset_output = subprocess.check_output(["xset", "q"], text=True)
            if "DPMS is Enabled" in xset_output:
                standby = re.search(r"Standby:\s+(\d+)", xset_output)
                if standby:
                    minutes = int(standby.group(1)) // 60
                    return minutes if minutes > 0 else None
        except Exception:
            pass

        return None  # Locking not detected

    def automatic_daily_updates_enabled(self) -> bool:
        # Look for systemd timer that runs `pacman -Syu` or similar
        try:
            timers_output = subprocess.check_output(
                ["systemctl", "list-timers", "--all"],
                text=True,
            )
            for line in timers_output.splitlines():
                if "pacman" in line or "update" in line:
                    return True
        except Exception:
            pass

        return False
