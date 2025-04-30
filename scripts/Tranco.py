import json
from pathlib import Path
from time import sleep
import requests
from datetime import datetime
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

tranco_dir = Path(__file__).resolve().parent.parent / 'resource' / "tranco"
# parent.parent / 'assets' / "tranco"


class TrancoListFetcher:
    def __init__(self, start_year=2024, start_month=10):
        self.api_url = "https://tranco-list.eu/api/"
        self.date_url = "/lists/date/{date}"     # /lists/date/{date}[?subdomains={subdomains}]
        self.download_url = "https://tranco-list.eu/download/{list_id}/1000000"
        self.start_date = datetime(start_year, start_month, 1)
        self.today = datetime.now()

    def generate_monthly_dates(self):
        dates = []
        current_date = self.start_date
        while current_date <= self.today:
            dates.append(current_date.strftime('%Y%m01'))
            # Move to the first day of the next month
            next_month = current_date.month % 12 + 1
            next_year = current_date.year + (current_date.month // 12)
            current_date = datetime(next_year, next_month, 1)
        return dates

    def fetch_list_ids(self):
        list_ids = {}
        dates = self.generate_monthly_dates()
        for date in dates:
            list_id = self.get_list_id_for_date(date)
            print(date, list_id)

            list_ids[date] = list_id
        return list_ids

    def get_list_id_for_date(self, date):
        while True:
            try:
                # Construct the URL using urllib.parse
                date_url = self.date_url.format(date=date)
                url = urllib.parse.urljoin(self.api_url, date_url)
                url = self.api_url + date_url

                response = requests.get(url)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('available'):
                        return data['list_id']
                elif response.status_code == 404:
                    print(f"No list found for date {date}.")
            except requests.RequestException as e:
                # Improved logging for debugging
                print(f"Request failed for date {date}: {e}")

    def download_list(self, list_id):
        while True:
            try:
                download_url = self.download_url.format(list_id=list_id)
                response = requests.get(download_url)
                if response.status_code == 200:
                    return response.text
                else:
                    print(f"Failed to download list {list_id}.")
            except requests.RequestException as e:
                print(f"Request failed for list {list_id}: {e}")

    def download_lists(self, list_ids):
        lists = {}
        n_list_lds = len(list_ids)

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
                print(f"{n_dones} / {n_list_lds}")

                for date in dones:
                    del futures[date]

                if n_dones == n_list_lds:
                    break
        print("All lists")
        return lists


# Usage
# fetcher = TrancoListFetcher(start_year=2022, start_month=10)
# list_ids = fetcher.fetch_list_ids()
# print("Fetched list IDs:", list_ids)
# with open("list_ids.json", 'w') as f:
#     json.dump(list_ids, f)


# fetcher = TrancoListFetcher(start_year=2022, start_month=10)
# list_ids = json.load(open("list_ids.json"))
# lists = fetcher.download_lists(list_ids)
# for date, list_data in lists.items():
#     with open(f"tranco_{date}.csv", 'w') as f:
#         f.write(list_data)
MAX_LINES = 10000
print(tranco_dir)
stats = {}
for filename in tranco_dir.glob("*.csv"):
    print(filename)
    with open(filename, 'r') as f:
        lines = f.readlines()
        # Skip the first line (header)
        lines = lines[:10000]
        # Process the remaining lines
        for line in lines:
            domain = line.strip().split(",")[1]
            # print(domain)
            if domain in stats:
                stats[domain] += 1
            else:
                stats[domain] = 1
print(len(stats))
with open(tranco_dir / "stats.json", 'w') as f:
    json.dump(stats, f, indent=4)