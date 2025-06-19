"""Module to query CVEs for a package from the Ubuntu CVE tracker."""

import requests

HTTP_STATUS_OK = 200


def get_cves_for_package(package_name: str) -> list[str]:
    """Query CVEs for a package. Stub implementation for Ubuntu CVE tracker."""
    try:
        url = f"https://ubuntu.com/security/cves?package={package_name}"
        response = requests.get(url, timeout=5)
        if response.status_code == HTTP_STATUS_OK and "CVE-" in response.text:
            # Real parsing would require proper scraping or API access
            return ["(possible CVEs)"]  # Stubbed
    except Exception:
        pass

    return []
