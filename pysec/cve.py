import requests

def get_cves_for_package(package_name):
    """Query CVEs for a package. Stub implementation for Ubuntu CVE tracker."""
    try:
        url = f"https://ubuntu.com/security/cves?package={package_name}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200 and "CVE-" in response.text:
            # Real parsing would require proper scraping or API access
            return ["(possible CVEs)"]  # Stubbed
    except Exception:
        pass

    return []
