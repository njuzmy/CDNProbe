import sys
sys.path.append("..")
import src.mydns
import src.multifinder
import time
import threading
import pandas as pd
import json
import os
from concurrent.futures.thread import ThreadPoolExecutor

def fun(website):
    d = src.mydns.DnsResolve("../resource/prefix1.txt")
    cdn = src.multifinder.CdnDetect("../resource/cname_cache.json","../resource/cdnlist.txt")
    # dns_dict = d.process_resolve(website)
    dns_dict, ip_number = d.yzx_process_resolve(website)
    print(dns_dict)
    # result = cdn.pidentify_cdn(website,dns_dict)
    result = cdn.yzx_identify_cdn(website,dns_dict)

    key = cdn.key
    return (result, key, ip_number)
    

if __name__ == "__main__":
    # d = mydns.DnsResolve("prefix1.txt")
    # cdn = multifinder.CdnDetect("cname_cache.json","../top1m-multi-cdn/cdnlist.txt")
    website = "www.uniqlo.com"
    result = fun(website)
    print(result)
    #stime = time.time()
    # print(parallel(websites))

    #os.makedirs(ans_dirpath,exist_ok=True)

    # result_dict = {}
    # cnt=1
    # for website in websites:
    #     # website = "www."+website
    #     print("\n"*2)
    #     print(f"{cnt}/{len(websites)}")
    #     print(website)
    #     cnt+=1
    #     result = fun(website)
    #     print(result)
    #     result_dict[website] = result[1]
    #     result_dict[website]['cdn'] = result[0]
    #     result_dict[website]['dns'] = result[2]

        # with open(os.path.join(ans_dirpath,f'9-21_{time.time()}.json'),"w")as f:
        #     json.dump(result_dict, f, indent=4)

    # executor =  ThreadPoolExecutor(max_workers=3)
    
        
    # i = 0
    # for result in executor.map(fun, websites):
    #     result_dict[websites[i]] = result[1]
    #     result_dict[websites[i]]['cdn'] = result[0]
    #     i += 1
    # #print(result_dict)
    # with open(os.path.join(ans_dirpath,'ans.json'),'w') as f:
    #     json.dump(result_dict, f, indent=4)
    # print(time.time() - stime)
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