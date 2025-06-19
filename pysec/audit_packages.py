from rich import print
from rich.table import Table
from pysec.oschecks import get_checker
from pysec.cve_manager import CveManager

def audit_installed_packages():
    checker = get_checker()

    if not checker:
        print("[red]✗ No supported OS checker found[/red]")
        return

    installed_packages = checker.get_installed_packages()
    if not installed_packages:
        print("[yellow]No packages found.[/yellow]")
        return
    
    cve_manager = CveManager()

    results = []
    for pkg_dict in installed_packages:
        pkg_name, version = pkg_dict['name'], pkg_dict['version']
        cves = cve_manager.get_cves(pkg_name)
        results.append((pkg_name, version, cves))


    table = Table(title="Installed Packages with CVEs")
    table.add_column("Package")
    table.add_column("Version")
    table.add_column("CVEs", justify="left")

    # Placeholder: just print out package list with no CVE data
    for pkg in sorted(results, key=lambda x: x[0]):
        if pkg[2]:
            table.add_row(pkg[0], pkg[1], ",".join([f"{cve_desc[0]}: {cve_desc[1]}" for cve_desc in pkg[2]]))

    print(table)
