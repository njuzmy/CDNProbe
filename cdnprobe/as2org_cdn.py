import socket
import json
import jsonlines
import requests
import pyasn
import dnsResolver
import pandas as pd
import time
import os

asndb = pyasn.pyasn('../resource/20230101asb.db')
base_dirpath = "../result/as2org_ans"
os.makedirs(base_dirpath,exist_ok=True)

class As2Org():
    def __init__(self):
        self.cdn_total = []
        self.as_list = []
        self.as_info = {}
        self.cdn_list = []
        self.cname_cache = json.load(open("../resource/cname_cache.json", 'r'))
        with open("../resource/cdnlist.txt", 'r') as file:
            for line in file.readlines():
                self.cdn_total.append(line.strip().lower())
    
    def getAS(self, ip):
        try:
            return int(asndb.lookup(ip)[0])
        except:
            return 0
    
    def org(self, asn):
        with jsonlines.open('../resource/20230101.as-org2info.jsonl', mode='r') as reader:
            for row in reader:
                if 'asn' in row.keys():
                    if row['asn'] == asn:
                        return row
        return None

    def cname(self, cname=None):
        if cname is None:
            return False, None
        for cdn, v in self.cname_cache.items():
            for cdn_cname in v['cname_substring'].split(' '):
                if cname.find(cdn_cname) != -1:
                    return True, cdn
        return False, None

    def identify_cdn(self, dns_dict):
        for cname, ip_list in dns_dict.items():
            flag, cdn = self.cname(cname)
            if flag == True:
                self.cdn_list.append(cdn)
            else:
                for ip in ip_list:
                    self.as_list.append(self.getAS(ip))
                self.as_list = list(set(self.as_list))
                for asn in self.as_list:
                    org_dict = self.org(str(asn))
                    self.as_info[asn] = org_dict
                    #print(org_dict)
                    if org_dict != None and "name" in org_dict.keys():
                        for cdn in self.cdn_total:
                            if org_dict['name'].lower().find(cdn) != -1:
                                self.cdn_list.append(cdn)

        if len(list(set(self.cdn_list))) > 0:
            return list(set(self.cdn_list))

if __name__ == "__main__":
    websites = pd.read_csv("../resource/top-1m.csv")["domain"][2608:10000].to_list()
    # print(websites)
    result_dict = json.load(open("../result/as2org_ans/9-26_1696770254.007474.json"))
    cnt=1
    try:
        for website in websites:
            website = "www."+website

            print(f"{cnt}/{len(websites)}")
            print(website)
            cnt+=1

            d = DnsResolver.DnsResolver("../resource/prefix1.txt")
            a = As2Org()
            result = a.identify_cdn(d.query_and_resolve_with_subnets(website)[0])
            result_dict[website] = a.as_info
            result_dict[website]["cdn"] = result
            with open(os.path.join(base_dirpath,f"9-26_{time.time()}.json"),'w') as f:
                json.dump(result_dict, f, indent=4)
    except Exception as e:
        print(e)
        print(website)
        # with open(os.path.join(base_dirpath,'ans_w_www.json'), 'w') as f:
        #     json.dump(result_dict, f, indent=4)

    with open(os.path.join(base_dirpath,'as2org_w_www.json'), 'w') as f:
            json.dump(result_dict, f, indent=4)