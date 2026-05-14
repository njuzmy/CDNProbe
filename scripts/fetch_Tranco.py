import argparse
import json
import sys
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from time import sleep

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cdnprobe.paths import tranco_input

DEFAULT_TRANCO_DIR = tranco_input()


class TrancoListFetcher:
    def __init__(self, start_year=2024, start_month=10):
        self.api_url = "https://tranco-list.eu/api/"
        self.date_url = "/lists/date/{date}"
        self.download_url = "https://tranco-list.eu/download/{list_id}/1000000"
        self.start_date = datetime(start_year, start_month, 1)
        self.today = datetime.now()

    def generate_monthly_dates(self):
        dates = []
        current_date = self.start_date
        while current_date <= self.today:
            dates.append(current_date.strftime("%Y%m01"))
            next_month = current_date.month % 12 + 1
            next_year = current_date.year + (current_date.month // 12)
            current_date = datetime(next_year, next_month, 1)
        return dates

    def fetch_list_ids(self):
        list_ids = {}
        for date in self.generate_monthly_dates():
            list_id = self.get_list_id_for_date(date)
            print(date, list_id)
            list_ids[date] = list_id
        return list_ids

    def get_list_id_for_date(self, date):
        while True:
            try:
                date_url = self.date_url.format(date=date)
                url = urllib.parse.urljoin(self.api_url, date_url)
                response = requests.get(url)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("available"):
                        return data["list_id"]
                elif response.status_code == 404:
                    print(f"No list found for date {date}.")
            except requests.RequestException as exc:
                print(f"Request failed for date {date}: {exc}")

    def download_list(self, list_id):
        while True:
            try:
                response = requests.get(self.download_url.format(list_id=list_id))
                if response.status_code == 200:
                    return response.text
                print(f"Failed to download list {list_id}.")
            except requests.RequestException as exc:
                print(f"Request failed for list {list_id}: {exc}")

    def download_lists(self, list_ids):
        lists = {}
        n_list_ids = len(list_ids)
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {date: executor.submit(self.download_list, list_id) for date, list_id in list_ids.items()}
            n_dones = 0
            while True:
                sleep(0.2)
                dones = []
                for date, future in futures.items():
                    if future.done():
                        n_dones += 1
                        lists[date] = future.result()
                        dones.append(date)
                print(f"{n_dones} / {n_list_ids}")
                for date in dones:
                    del futures[date]
                if n_dones == n_list_ids:
                    break
        print("All lists")
        return lists


def build_stats(tranco_dir: Path = DEFAULT_TRANCO_DIR, max_lines: int = 10000) -> dict[str, int]:
    stats: dict[str, int] = {}
    for filename in sorted(tranco_dir.glob("*.csv")):
        print(filename)
        with filename.open("r") as f:
            lines = f.readlines()[:max_lines]
            for line in lines:
                domain = line.strip().split(",")[1]
                stats[domain] = stats.get(domain, 0) + 1
    return stats


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build domain frequency stats from Tranco CSV snapshots.")
    parser.add_argument(
        "--tranco-dir",
        type=Path,
        default=DEFAULT_TRANCO_DIR,
        help=f"Directory containing Tranco CSV files. Defaults to {DEFAULT_TRANCO_DIR}.",
    )
    parser.add_argument(
        "--max-lines",
        type=int,
        default=10000,
        help="Maximum number of rows to read from each Tranco CSV.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Stats JSON output path. Defaults to <tranco-dir>/stats.json.",
    )
    return parser


def main():
    args = build_parser().parse_args()
    tranco_dir = args.tranco_dir
    tranco_dir.mkdir(parents=True, exist_ok=True)
    print(tranco_dir)
    stats = build_stats(tranco_dir, args.max_lines)
    print(len(stats))
    output = args.output or tranco_dir / "stats.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w") as f:
        json.dump(stats, f, indent=4)


if __name__ == "__main__":
    main()
