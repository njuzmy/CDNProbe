import sys
sys.path.append("..")
from src import mydns
from src import multifinder

import time
import threading
import pandas as pd
import json
import os
import asyncio
from concurrent.futures.thread import ThreadPoolExecutor

tmp_dirpath = "../tmp"
res_dirpath = "../resource"
ans_dirpath = "../ans"
www_prefix_enabled = True


def find(website):
    d = mydns.DnsResolve(get_resource_path("prefix1.txt"))
    cdn = multifinder.CdnDetect(get_resource_path(
        "cname_cache.json"), get_resource_path("cdnlist.txt"))

    dns_dict, ip_number = d.process_resolve(website)
    # dns_dict, ip_number = asyncio.run(d.async_process_resolve(website,"8.8.8.8"))
    print(dns_dict)

    result = cdn.identify_cdn(website, dns_dict)
    key = cdn.key
    return (result, key, ip_number)


def get_resource_path(filename):
    return os.path.join(res_dirpath, filename)


if __name__ == "__main__":
    websites = pd.read_csv(get_resource_path(
        "top-1m.csv"))["domain"][0:10000].to_list()

    stime = time.time()

    os.makedirs(ans_dirpath, exist_ok=True)
    os.makedirs(tmp_dirpath, exist_ok=True)

    result_dict = {}
    cnt = 1
    prev_tmp_name = None
    for website in websites:
        website = ("www." if www_prefix_enabled else "") + website

        print("\n" * 2)
        print(f"{cnt}/{len(websites)}")
        print(website)
        cnt += 1
        result = find(website)
        print(result)
        result_dict[website] = result[1]
        result_dict[website]['cdn'] = result[0]
        result_dict[website]['dns'] = result[2]
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
