"""Mac-specific security checks for pysec."""

import subprocess

from pysec.osbase import BaseSecurityChecker


class MacSecurityChecker(BaseSecurityChecker):
    @staticmethod
    def is_current_os() -> bool:
        try:
            result = subprocess.run(
                ["uname"],
                check=False,
                capture_output=True,
                text=True,
            )
            return result.stdout.strip() == "Darwin"
        except Exception:
            return False

    def get_installed_packages(self) -> list[dict[str, str]]:
        try:
            result = subprocess.run(
                ["brew", "list", "--versions"],
                capture_output=True,
                text=True,
                check=True,
            )
            packages = []
            for line in result.stdout.strip().splitlines():
                parts = line.strip().split()
                if len(parts) >= 2:  # noqa: PLR2004
                    name = parts[0]
                    version = parts[1]
                    packages.append({"name": name, "version": version})
            return packages
        except subprocess.CalledProcessError:
            return []

    def is_disk_encrypted(self) -> bool:
        try:
            result = subprocess.run(
                ["fdesetup", "status"],
                check=False,
                capture_output=True,
                text=True,
            )
            return "FileVault is On" in result.stdout
        except Exception:
            return False

    def screen_lock_timeout_minutes(self) -> int | None:
        try:
            result = subprocess.run(
                [
                    "defaults",
                    "-currentHost",
                    "read",
                    "com.apple.screensaver",
                    "idleTime",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            seconds = int(result.stdout.strip())
            return seconds // 60 if seconds > 0 else None
        except subprocess.CalledProcessError:
            return None

    def automatic_daily_updates_enabled(self) -> bool:
        try:
            result = subprocess.run(
                [
                    "defaults",
                    "read",
                    "/Library/Preferences/com.apple.SoftwareUpdate",
                    "AutomaticCheckEnabled",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip() == "1"
        except subprocess.CalledProcessError:
            return False
