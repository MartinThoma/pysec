import subprocess
from pysec.osbase import BaseSecurityChecker

class UbuntuSecurityChecker(BaseSecurityChecker):
    @staticmethod
    def is_current_os() -> bool:
        try:
            with open("/etc/os-release") as f:
                for line in f:
                    if line.startswith("ID="):
                        return "ubuntu" in line.lower()
        except Exception:
            print("Error reading /etc/os-release")
            pass
        return False

    def get_installed_packages(self) -> list[dict[str, str]]:
        result = subprocess.run(
            ["dpkg-query", "-W", "-f=${Package}\t${Version}\n"],
            capture_output=True, text=True, check=True
        )
        packages = []
        for line in result.stdout.strip().splitlines():
            name, version = line.strip().split("\t")
            packages.append({"name": name, "version": version})
        return packages

    def is_disk_encrypted(self) -> bool:
        # Check if root is on a LUKS volume (simplified)
        try:
            with open("/proc/mounts") as f:
                mounts = f.read()
            return any("/dev/mapper/" in line for line in mounts.splitlines())
        except Exception:
            return False

    def screen_lock_timeout_minutes(self) -> int | None:
        import subprocess

        # Try GNOME first (seconds)
        try:
            result = subprocess.run(
                ["gsettings", "get", "org.gnome.desktop.session", "idle-delay"],
                capture_output=True, text=True, check=True
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
                ["gsettings", "get", "org.mate.screensaver", "idle-activation-enabled"],
                capture_output=True, text=True, check=True
            )
            if enabled_result.stdout.strip() != "true":
                return None

            keys = [
                "org.mate.screensaver idle-delay",
                "org.mate.session idle-delay"
            ]
            for key in keys:
                try:
                    result = subprocess.run(
                        ["gsettings", "get"] + key.split(),
                        capture_output=True, text=True, check=True
                    )
                    minutes = int(result.stdout.strip())
                    if minutes > 0:
                        return minutes
                except Exception:
                    continue

        except Exception:
            pass

        return None
