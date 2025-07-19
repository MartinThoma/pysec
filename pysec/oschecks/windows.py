"""Windows-specific security checks for pysec."""

import logging
import platform
import subprocess
from datetime import datetime, timezone

from pysec.osbase import BaseSecurityChecker

logger = logging.getLogger(__name__)


class WindowsSecurityChecker(BaseSecurityChecker):
    @staticmethod
    def is_current_os() -> bool:
        return platform.system().lower() == "windows"

    def get_audit_events(self) -> list[dict[str, str]]:
        """Get audit events from Windows system."""
        events = []

        # Add current client run event
        events.append(
            {
                "timestamp": datetime.now(tz=timezone.utc).isoformat(),
                "event": "pysec_client_run",
            },
        )

        # Try to get recent login events using PowerShell
        try:
            # Get recent logon events from Windows Event Log
            ps_command = (
                "Get-WinEvent -FilterHashtable @{LogName='Security'; ID=4624} "
                "-MaxEvents 5 -ErrorAction SilentlyContinue | "
                "Select-Object -Property TimeCreated, Message | "
                "ConvertTo-Json"
            )
            result = subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            )
            if result.stdout.strip():
                events.append(
                    {
                        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
                        "event": (
                            "recent_logons: "
                            f"{len(result.stdout.strip().split())} events found"
                        ),
                    },
                )
        except (
            subprocess.CalledProcessError,
            subprocess.TimeoutExpired,
            FileNotFoundError,
        ):
            logger.debug("Failed to get Windows login events")

        # Try to get recent system events
        try:
            ps_command = (
                "Get-WinEvent -FilterHashtable @{LogName='System'} "
                "-MaxEvents 3 -ErrorAction SilentlyContinue | "
                "Select-Object -Property TimeCreated, LevelDisplayName, Message | "
                "ConvertTo-Json"
            )
            result = subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            )
            if result.stdout.strip():
                events.append(
                    {
                        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
                        "event": (
                            "recent_system_events: "
                            f"{len(result.stdout.strip().split())} events found"
                        ),
                    },
                )
        except (
            subprocess.CalledProcessError,
            subprocess.TimeoutExpired,
            FileNotFoundError,
        ):
            logger.debug("Failed to get Windows system events")

        return events

    def is_disk_encrypted(self) -> bool:
        """Check if BitLocker is enabled on the system drive."""
        try:
            # Check BitLocker status for C: drive
            result = subprocess.run(
                ["manage-bde", "-status", "C:"],
                capture_output=True,
                text=True,
                check=True,
            )
            return "Protection On" in result.stdout
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback: check via PowerShell
            try:
                ps_command = (
                    "Get-BitLockerVolume -MountPoint C: | "
                    "Select-Object -ExpandProperty ProtectionStatus"
                )
                result = subprocess.run(
                    ["powershell", "-Command", ps_command],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                return "On" in result.stdout.strip()
            except Exception:
                logger.debug("Failed to check BitLocker status")
                return False

    def screen_lock_timeout_minutes(self) -> int | None:
        """Get screen lock timeout from Windows registry."""
        try:
            # Query registry for screen saver timeout
            result = subprocess.run(
                [
                    "reg",
                    "query",
                    "HKEY_CURRENT_USER\\Control Panel\\Desktop",
                    "/v",
                    "ScreenSaveTimeOut",
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            # Parse the output to extract the timeout value
            for line in result.stdout.split("\n"):
                if "ScreenSaveTimeOut" in line:
                    # Extract the REG_SZ value (seconds)
                    parts = line.strip().split()
                    if len(parts) >= 3:  # noqa: PLR2004
                        seconds = int(parts[-1])
                        if seconds > 0:
                            return seconds // 60

            return None
        except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
            logger.debug("Failed to get Windows screen lock timeout")
            return None

    def automatic_daily_updates_enabled(self) -> bool:
        """Check if Windows automatic updates are enabled."""
        try:
            # Check Windows Update service status
            result = subprocess.run(
                ["sc", "query", "wuauserv"],
                capture_output=True,
                text=True,
                check=True,
            )

            # Service should be running for automatic updates
            if "RUNNING" in result.stdout:
                # Check automatic update settings via registry
                try:
                    result = subprocess.run(
                        [
                            "reg",
                            "query",
                            (
                                "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft"
                                "\\Windows\\CurrentVersion\\WindowsUpdate\\Auto Update"
                            ),
                            "/v",
                            "AUOptions",
                        ],
                        capture_output=True,
                        text=True,
                        check=True,
                    )

                    # Parse AUOptions value:
                    # 2 = Notify before download
                    # 3 = Automatically download and notify of installation
                    # 4 = Automatically download and schedule installation (automatic)
                    # 5 = Automatic Updates is required, but end users can configure it
                    for line in result.stdout.split("\n"):
                        if "AUOptions" in line:
                            parts = line.strip().split()
                            if len(parts) >= 3:  # noqa: PLR2004
                                option = int(parts[-1], 16)  # Value might be hex
                                return option in (4, 5)  # Automatic modes

                except (subprocess.CalledProcessError, ValueError):
                    # If we can't check the setting, assume enabled if service is running
                    return True

            return False
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.debug("Failed to check Windows automatic updates status")
            return False
