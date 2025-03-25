import sys  # noqa
sys.path.append("..")  # noqa

from cdnprobe import DnsResolver
from cdnprobe import CdnDetector
import time
import pandas as pd
import json
import os


tmp_dirpath = "../tmp"
res_dirpath = "../resource"
ans_dirpath = "../ans"
www_prefix_enabled = True


def detect(domain):
    dnsResolver = DnsResolver.DnsResolver(FILEPATH_RESOURCE("prefix.txt"))
    cdnDetector = CdnDetector.CdnDetector(FILEPATH_RESOURCE(
        "cname_cache.json"), FILEPATH_RESOURCE("cdnlist.txt"))

    dns_dict, ip_number = dnsResolver.query_and_resolve_with_subnets(domain)
    # dns_dict, ip_number = asyncio.run(d.async_process_resolve(website,"8.8.8.8"))
    print(dns_dict)

    identified_cdn = cdnDetector.identify_cdn(domain, dns_dict)
    keys = cdnDetector.keys
    print(identified_cdn, keys, ip_number)
    return (identified_cdn, keys, ip_number)


def FILEPATH_RESOURCE(filename):
    return os.path.join(res_dirpath, filename)


if __name__ == "__main__":
    domains = pd.read_csv(FILEPATH_RESOURCE(
        "top-1m.csv"))["domain"][0:10000].to_list()

    stime = time.time()

    os.makedirs(ans_dirpath, exist_ok=True)
    os.makedirs(tmp_dirpath, exist_ok=True)

    result_dict = {}
    i = 1
    prev_tmp_name = None
    for domain in domains:
        domain = ("www." if www_prefix_enabled else "") + domain

        print("\n" * 2)
        print(f"{i}/{len(domains)}")
        print(domain)
        i += 1

        identified_cdn, keys, ip_number = detect(domain)
        result_dict[domain] = keys
        result_dict[domain]['cdn'] = identified_cdn
        result_dict[domain]['dns'] = ip_number

        tmp_name = f"{time.time()}.json"
        with open(os.path.join(tmp_dirpath, tmp_name), "w")as f:
            json.dump(result_dict, f, indent=4)
        if prev_tmp_name is not None:
            os.remove(os.path.join(tmp_dirpath, prev_tmp_name))
        prev_tmp_name = tmp_name

    ans_name = time.strftime("%Y%m%d") + ("_ans_www.json" if www_prefix_enabled else "_ans_no_www.json")
    with open(os.path.join(ans_dirpath, ans_name), 'w') as f:
        json.dump(result_dict, f, indent=4)
    print(time.time() - stime)
    exit(0)
