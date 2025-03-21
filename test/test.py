import sys
sys.path.append("..")
from src import dnsResolver
from src import multifinder

import time
import threading
import pandas as pd
import json
import os
from concurrent.futures.thread import ThreadPoolExecutor

ans_dirpath="../ans"
tmp_dirpath="../tmp"
res_dirpath="../resource"


def find(website):
    d = dnsResolver.DnsResolve(get_resource_path("prefix1.txt"))
    cdn = multifinder.CdnDetect(get_resource_path("cname_cache.json"),get_resource_path("cdnlist.txt"))

    dns_dict, ip_number = d.query_and_resolve_with_subnets(website)
    print(dns_dict)

    result = cdn.identify_cdn(website,dns_dict)
    key = cdn.key
    return (result, key, ip_number)
    

def get_resource_path(filename):
    return os.path.join(res_dirpath,filename)


if __name__ == "__main__":
    website = "www.uniqlo.com"
    result = find(website)
    print(result)
