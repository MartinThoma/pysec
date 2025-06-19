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
        self.config_dir = user_config_dir("pysec")
        Path(self.config_dir).mkdir(parents=True)
        self.years = [2023, 2024, 2025]
        self.cve_data = defaultdict(list)
        self._load_or_download()

    def _load_or_download(self) -> None:
        config_path = Path(self.config_dir)
        for year in self.years:
            path = config_path / f"nvdcve-1.1-{year}.json"
            if not path.exists():
                self._download(year)
            self._parse(path)

    def _download(self, year: int) -> None:
        url = f"https://nvd.nist.gov/feeds/json/cve/1.1/nvdcve-1.1-{year}.json.gz"
        gz_path = Path(self.config_dir) / f"nvdcve-1.1-{year}.json.gz"
        urllib.request.urlretrieve(url, gz_path)  # noqa: S310
        with gzip.open(gz_path, "rb") as f_in, open(gz_path[:-3], "wb") as f_out:  # noqa: PTH123
                shutil.copyfileobj(f_in, f_out)
        Path(gz_path).unlink()

    def _parse(self, path: Path) -> None:
        with path.open() as f:
            data = json.load(f)
        for item in data.get("CVE_Items", []):
            cve_id = item["cve"]["CVE_data_meta"]["ID"]
            desc = item["cve"]["description"]["description_data"][0]["value"]
            for node in item.get("configurations", {}).get("nodes", []):
                for cpe in node.get("cpe_match", []):
                    if cpe.get("vulnerable"):
                        cpe_parts = cpe.get("cpe23Uri", "").split(":")
                        if len(cpe_parts) > CPE_LEN:
                            pkg = cpe_parts[CPE_LEN].lower()
                            self.cve_data[pkg].append((cve_id, desc))

    def get_cves(self, pkg: str) -> list:
        name = pkg.lower().split("-")[0]  # Basic heuristic
        return self.cve_data.get(pkg.lower(), []) + self.cve_data.get(name, [])
