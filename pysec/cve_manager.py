
import os
from appdirs import user_config_dir
from collections import defaultdict
import gzip
import shutil
import json
import urllib.request


class CveManager:
    def __init__(self):
        self.config_dir = user_config_dir("pysec")
        os.makedirs(self.config_dir, exist_ok=True)
        self.years = [2023, 2024, 2025]
        self.cve_data = defaultdict(list)
        self._load_or_download()

    def _load_or_download(self):
        for year in self.years:
            path = os.path.join(self.config_dir, f"nvdcve-1.1-{year}.json")
            if not os.path.exists(path):
                self._download(year)
            self._parse(path)

    def _download(self, year):
        url = f"https://nvd.nist.gov/feeds/json/cve/1.1/nvdcve-1.1-{year}.json.gz"
        gz_path = os.path.join(self.config_dir, f"nvdcve-1.1-{year}.json.gz")
        print(f"Downloading {url}")
        urllib.request.urlretrieve(url, gz_path)
        with gzip.open(gz_path, 'rb') as f_in:
            with open(gz_path[:-3], 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        os.remove(gz_path)

    def _parse(self, path):
        with open(path) as f:
            data = json.load(f)
        for item in data.get("CVE_Items", []):
            cve_id = item["cve"]["CVE_data_meta"]["ID"]
            desc = item["cve"]["description"]["description_data"][0]["value"]
            for node in item.get("configurations", {}).get("nodes", []):
                for cpe in node.get("cpe_match", []):
                    if cpe.get("vulnerable"):
                        cpe_parts = cpe.get("cpe23Uri", "").split(":")
                        if len(cpe_parts) > 4:
                            pkg = cpe_parts[4].lower()
                            self.cve_data[pkg].append((cve_id, desc))

    def get_cves(self, pkg: str) -> list:
        name = pkg.lower().split('-')[0]  # Basic heuristic
        return self.cve_data.get(pkg.lower(), []) + self.cve_data.get(name, [])
