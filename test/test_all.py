import sys
sys.path.append("..")

from cdnprobe.utils import create_progress
import os
import json
import pandas as pd
import time
from cdnprobe import CdnDetector
from cdnprobe import DnsResolver
from concurrent.futures.thread import ThreadPoolExecutor



tmp_dirpath = "../tmp"
res_dirpath = "../resource"
ans_dirpath = "../ans"
www_prefix_enabled = False


def detect(domain):
    dnsResolver = DnsResolver.DnsResolver(FILEPATH_RESOURCE("list.txt"))

    dns_dict, ip_number = dnsResolver.query_and_resolve_with_subnets(domain)
    # dns_dict, ip_number = asyncio.run(d.async_process_resolve(website,"8.8.8.8"))
    print(dns_dict)
    dns_records = dnsResolver.dns_records
    print(dns_records)

    def _detect(dns_dict):
        cdnDetector = CdnDetector.CdnDetector(FILEPATH_RESOURCE(
            "cname_cache.json"), FILEPATH_RESOURCE("cdnlist.txt"))
        identified_cdn = cdnDetector.identify_cdn(domain, dns_dict)
        return identified_cdn

    with ThreadPoolExecutor(max_workers=128) as executor:
        futures = {executor.submit(_detect, {value['cname']: [value['ip']]}): subnet for subnet, value in dns_records.items()}

        with create_progress() as progress:
            progress_task = progress.add_task(f"CDN Detection ip of cname ", total=len(futures))
            n_dones = 0

            while True:
                time.sleep(0.2)
                done_futures = []
                for future, subnet in futures.items():
                    if future.done():
                        n_dones += 1
                        dns_records[subnet]['cdn'] = future.result()
                        progress.update(progress_task)
                        done_futures.append(future)
                for future in done_futures:
                    del futures[future]
                progress.update(progress_task, completed=n_dones)
                
                if len(futures) == 0:
                    break

    #     for future in futures:
    #         subnet = futures[future]
    #         identified_cdn = future.result()
    #         dns_records[subnet]['cdn'] = identified_cdn

    # for subnet, value in dns_records.items():
    #     print(subnet, value)
    #     dns_dict = {value['cname']: [value['ip']]}
    #     cdnDetector = CdnDetector.CdnDetector(FILEPATH_RESOURCE(
    #         "cname_cache.json"), FILEPATH_RESOURCE("cdnlist.txt"))
    #     identified_cdn = cdnDetector.identify_cdn(domain, dns_dict)
    #     value['cdn'] = identified_cdn
    # keys = cdnDetector.keys
    keys = dns_records
    # print(identified_cdn, keys, ip_number)
    identified_cdn = None
    return (identified_cdn, keys, ip_number)


def FILEPATH_RESOURCE(filename):
    return os.path.join(res_dirpath, filename)


if __name__ == "__main__":
    domains = pd.read_csv(FILEPATH_RESOURCE(
        "top-1m.csv"))["domain"][0:10000].to_list()
    domains = ['microsoft.com', 'www.microsoft.com']
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
        # result_dict[domain]['cdn'] = identified_cdn
        # result_dict[domain]['dns'] = ip_number

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
