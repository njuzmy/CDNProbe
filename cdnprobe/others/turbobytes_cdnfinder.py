import json
import subprocess

from pathlib import Path
from urllib.parse import urljoin


DEFAULT_TURBOBYTES_BASE_URL = "http://127.0.0.1:1337/"


def get_cmd(domain, qtype, base_url=DEFAULT_TURBOBYTES_BASE_URL):
    base_url = base_url.rstrip("/") + "/"
    requests = [
        (base_url, {"url": f"http://{domain}"}),
        (base_url, {"url": f"http://www.{domain}"}),
        (urljoin(base_url, "hostname/"), {"hostname": domain}),
        (urljoin(base_url, "hostname/"), {"hostname": f"www.{domain}"}),
        (base_url, {"url": f"https://{domain}"}),
        (base_url, {"url": f"https://www.{domain}"}),
    ]
    url, payload = requests[qtype]
    return [
        "curl",
        "-X",
        "POST",
        "-d",
        json.dumps(payload),
        "-H",
        "Content-Type: application/json",
        url,
    ]


def detect(domain: str, error_log_path: Path | None = None, base_url=DEFAULT_TURBOBYTES_BASE_URL):
    ans = {}
    error_counter = 0
    for i in range(4):
        try:
            cmd = get_cmd(domain, i, base_url=base_url)
            print(" ".join(cmd))
            dns_message = subprocess.check_output(cmd).decode("utf-8", "ignore")
            try:
                msg = json.loads(dns_message)
            except Exception:
                msg = dns_message
            ans[i] = msg
        except Exception as exc:
            print(exc)
            error_counter += 1

    if error_counter == 4 and error_log_path is not None:
        with error_log_path.open("a") as f:
            f.write(domain + "\n")
    return ans
