"""Fetch and parse CVE data from NVD."""

import gzip
import json
import shutil
import urllib.request
from collections import defaultdict
from pathlib import Path

from appdirs import user_config_dir

CPE_LEN = 4


class CveManager:
    def __init__(self) -> None:
        """Initialize the CVE manager."""
        self.config_dir = Path(user_config_dir("pysec"))
        if not self.config_dir.exists():
            self.config_dir.mkdir(parents=True)
        self.years = [2023, 2024, 2025]
        self.cve_data: dict[
            str,
            list[tuple[str, str, str, str | None, str | None]],
        ] = defaultdict(list)
        self._load_or_download()

    def _load_or_download(self) -> None:
        for year in self.years:
            path = self.config_dir / f"nvdcve-1.1-{year}.json"
            if not path.exists():
                self._download(year)
            self._parse(path)

    def _download(self, year: int) -> None:
        url = f"https://nvd.nist.gov/feeds/json/cve/1.1/nvdcve-1.1-{year}.json.gz"
        gz_path = Path(self.config_dir) / f"nvdcve-1.1-{year}.json.gz"
        urllib.request.urlretrieve(url, gz_path)  # noqa: S310
        with (
            gzip.open(gz_path, "rb") as f_in,
            open(str(gz_path)[:-3], "wb") as f_out,  # noqa: PTH123
        ):
            shutil.copyfileobj(f_in, f_out)
        Path(gz_path).unlink()

    def _parse(self, path: Path) -> None:
        with path.open() as f:
            data = json.load(f)
        for item in data.get("CVE_Items", []):
            cve_id = item["cve"]["CVE_data_meta"]["ID"]
            desc = item["cve"]["description"]["description_data"][0]["value"]

            # Determine severity (from CVSS v3.1 if available,
            # otherwise v2, fallback to "UNKNOWN")
            severity = "UNKNOWN"
            impact = item.get("impact", {})
            if "baseMetricV3" in impact:
                severity = (
                    impact["baseMetricV3"]
                    .get("cvssV3", {})
                    .get("baseSeverity", severity)
                )
            elif "baseMetricV2" in impact:
                severity = impact["baseMetricV2"].get("severity", severity)

            for node in item.get("configurations", {}).get("nodes", []):
                for cpe in node.get("cpe_match", []):
                    if cpe.get("vulnerable"):
                        cpe_parts = cpe.get("cpe23Uri", "").split(":")
                        if len(cpe_parts) > CPE_LEN:
                            pkg = cpe_parts[CPE_LEN].lower()
                            version_start = cpe.get("versionStartIncluding")
                            version_end = cpe.get("versionEndExcluding")
                            self.cve_data[pkg].append(
                                (cve_id, desc, severity, version_start, version_end),
                            )

    def _compare_versions(self, v1: str, v2: str) -> int:
        """
        Compare two version strings.

        Returns -1 if v1 < v2, 0 if equal, 1 if v1 > v2
        """

        def normalize(v: str) -> list[int]:
            return [int(part) for part in v.split(".") if part.isdigit()]

        parts1 = normalize(v1)
        parts2 = normalize(v2)

        # Pad shorter list with zeros
        length = max(len(parts1), len(parts2))
        parts1 += [0] * (length - len(parts1))
        parts2 += [0] * (length - len(parts2))

        for a, b in zip(parts1, parts2, strict=False):
            if a < b:
                return -1
            if a > b:
                return 1
        return 0

    def get_cves(
        self,
        pkg: str,
        version: str | None = None,
    ) -> list[tuple[str, str, str]]:
        name = pkg.lower().split("-")[0]
        entries = self.cve_data.get(pkg.lower(), []) + self.cve_data.get(name, [])

        if version is None:
            return [(cve_id, desc, severity) for cve_id, desc, severity, *_ in entries]

        result = []
        for cve_id, desc, severity, version_start, version_end in entries:
            try:
                if version_start and self._compare_versions(version, version_start) < 0:
                    continue
                if version_end and self._compare_versions(version, version_end) >= 0:
                    continue
                result.append((cve_id, desc, severity))
            except Exception:
                continue

        return result
