"""CLI script to audit installed packages for known CVEs."""

from rich import print
from rich.table import Table

from pysec import SeverityLevel
from pysec.cve_manager import CveManager
from pysec.oschecks import get_checker


def get_keep_severity(min_severity: SeverityLevel) -> list[str]:
    """Return a list of severity levels to keep based on the minimum severity."""
    keep_severity = []
    if min_severity in ["LOW"]:
        keep_severity.append("LOW")
    if min_severity in ["LOW", "MEDIUM"]:
        keep_severity.append("MEDIUM")
    if min_severity in ["LOW", "MEDIUM", "HIGH"]:
        keep_severity.append("HIGH")
    if min_severity in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
        keep_severity.append("CRITICAL")
    return keep_severity


def audit_installed_packages(verbosity: int, min_severity: SeverityLevel) -> None:
    """Check installed packages for known CVEs."""
    checker = get_checker()

    if not checker:
        print("[red]✗ No supported OS checker found[/red]")
        return

    installed_packages = checker.get_installed_packages()
    if not installed_packages:
        print("[yellow]No packages found.[/yellow]")
        return

    try:
        cve_manager = CveManager()
    except Exception as e:
        print(f"[red]✗ Failed to initialize CVE manager: {e}[/red]")
        return

    keep_severity = get_keep_severity(min_severity)

    results = []
    for pkg_dict in installed_packages:
        pkg_name, version = pkg_dict["name"], pkg_dict["version"]
        cves = cve_manager.get_cves(pkg_name)
        cves = [
            (cve_desc[0], cve_desc[1], cve_desc[2])
            for cve_desc in cves
            if cve_desc[2] in keep_severity
        ]
        results.append((pkg_name, version, cves))

    table = Table(title="Installed Packages with CVEs")
    table.add_column("Package")
    table.add_column("Version")
    table.add_column("CVEs", justify="left")

    # Placeholder: just print out package list with no CVE data
    for pkg in sorted(results, key=lambda x: x[0]):
        if pkg[2]:
            if verbosity == 0:
                cve_str = ", ".join(
                    [f"{cve_desc[0]}" for cve_desc in pkg[2]],
                )
            elif verbosity == 1:
                cve_str = ", ".join(
                    [f"{cve_desc[0]} ({cve_desc[2]})" for cve_desc in pkg[2]],
                )
            else:
                cve_str = ",".join(
                    [
                        f"{cve_desc[0]} ({cve_desc[2]}): {cve_desc[1].strip()}"
                        for cve_desc in pkg[2]
                    ],
                )
            table.add_row(pkg[0], pkg[1], cve_str)

    print(table)
