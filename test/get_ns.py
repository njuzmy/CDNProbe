import sys
sys.path.append("..")
from src.utils import query_and_resolve

import os
import json
from src import multifinder
from src import mydns
import dns
import clientsubnetoption
import signal

import time
import pandas as pd


www_prefix_enabled = True

ans_dirpath = "../ans"
res_dirpath = "../resource"
tmp_dirpath = "../tmp"
dns_server = "223.5.5.5"


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

    for website in websites:
        website = ("www." if www_prefix_enabled else "") + website

        print("\n" * 2)
        print(f"{cnt}/{len(websites)}")
        print(website)
        cnt += 1

        def timeout_handler(signum, frame):
            raise Exception
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(10)
        try:
            result = query_and_resolve(website, "NS")
        except:
            result = []
        signal.alarm(0)
        
        print(result)
        result_dict[website] = result
        with open(os.path.join(tmp_dirpath, f'{time.time()}.json'), "w")as f:
            json.dump(result_dict, f, indent=4)

    with open(os.path.join(ans_dirpath, 'ns_www.json'), 'w') as f:
        json.dump(result_dict, f, indent=4)
    print(time.time() - stime)
    exit(0)
