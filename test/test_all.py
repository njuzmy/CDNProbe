import sys
sys.path.append("..")
from src import mydns
from src import multifinder

import time
import threading
import pandas as pd
import json
import os
from concurrent.futures.thread import ThreadPoolExecutor

# def parallel(websites):
    # lock = threading.Lock()
    # result_dict = {}

    # def multi_thread(website):
    #     d = mydns.DnsResolve("prefix1.txt")
    #     cdn = multifinder.CdnDetect("cname_cache.json","../top1m-multi-cdn/cdnlist.txt")
    #     dns_dict = d.process_resolve(website)
    #     result = cdn.identify_cdn(website,dns_dict)
    #     with lock:
    #         result_dict[website] = result

    # threads = []
    # for website in websites:
    #     thread = threading.Thread(target=multi_thread,args=(website,))
    #     threads.append(thread)
    #     thread.start()

    # while True:
    #     time.sleep(0.2)
    #     exit_counter = 0
    #     for thread in threads:
    #         if not thread.is_alive():
    #             exit_counter += 1
    #     if exit_counter == len(websites):
    #         if exit_counter != len(result_dict):
    #             raise Exception("something error")
    #         break
    # return result_dict

def fun(website):
    d = mydns.DnsResolve(get_resource_path("prefix1.txt"))
    cdn = multifinder.CdnDetect(get_resource_path("cname_cache.json"),get_resource_path("cdnlist.txt"))
    # dns_dict = d.process_resolve(website)
    dns_dict, ip_number = d.yzx_process_resolve(website)
    print(dns_dict)
    # result = cdn.pidentify_cdn(website,dns_dict)
    result = cdn.yzx_identify_cdn(website,dns_dict)

    key = cdn.key
    return (result, key, ip_number)
    

ans_dirpath="../ans"
tmp_dirpath="../tmp"
res_dirpath="../resource"

def get_resource_path(filename):
    return os.path.join(res_dirpath,filename)


if __name__ == "__main__":
    # d = mydns.DnsResolve("prefix1.txt")
    # cdn = multifinder.CdnDetect("cname_cache.json","../top1m-multi-cdn/cdnlist.txt")
    websites = pd.read_csv(get_resource_path("multicdn.csv"))["domain"][0:].to_list()
    websites = pd.read_csv(get_resource_path("top-1m.csv"))["domain"][0:10].to_list()

    stime = time.time()
    # print(parallel(websites))

    os.makedirs(ans_dirpath,exist_ok=True)
    os.makedirs(tmp_dirpath,exist_ok=True)

    result_dict = {}
    cnt=1
    for website in websites:
        # website = "www."+website

        print("\n"*2)
        print(f"{cnt}/{len(websites)}")
        print(website)
        cnt+=1
        result = fun(website)
        print(result)
        result_dict[website] = result[1]
        result_dict[website]['cdn'] = result[0]
        result_dict[website]['dns'] = result[2]

        with open(os.path.join(tmp_dirpath,f'{time.time()}.json'),"w")as f:
            json.dump(result_dict, f, indent=4)

    # executor =  ThreadPoolExecutor(max_workers=3)
    
        
    # i = 0
    # for result in executor.map(fun, websites):
    #     result_dict[websites[i]] = result[1]
    #     result_dict[websites[i]]['cdn'] = result[0]
    #     i += 1
    # #print(result_dict)
    with open(os.path.join(ans_dirpath,'ans.json'),'w') as f:
        json.dump(result_dict, f, indent=4)
    print(time.time() - stime)
    exit(0)
    # with ThreadPoolExecutor(max_workers=10) as executor:
    #     ans = [executor.submit(fun, website) for website in websites]
    #     for res in ans

    # website = "www.apple.com"
    # stime = time.time()
    # dns_dict = d.process_resolve(website)
    # print(time.time() - stime)
    # stime = time.time()
    # result = cdn.identify_cdn(website,dns_dict)
    # print(time.time() - stime)
    # print(result)
