import json
import subprocess
import re
import os
import time
import threading
import ipwhois
import random
import warnings
from datetime import datetime
from netaddr import IPNetwork
import intervaltree
import sys

resource_dirpath = "../resource"
def get_resource_path(filename):
    return os.path.join(resource_dirpath,filename)


class CdnDetect:
    def __init__(self, cname_file=None, cdn_file=None) -> None:
        self.key = {"cname": [],
                    "http_header": [],
                    "tls_cert": [],
                    "rdap_info": []}
        self.cdn_list = []
        self.cdn_total = []
        self.cidr_time = {}
        self.rdap_cache_ip = {}
        self.rdap_refresh = 60 * 60 * 24
        self.rdap_cache = intervaltree.IntervalTree()
        self.cname_cache = json.load(open(cname_file, 'r'))
        self.off_net = []
        self.dns_hijack = []
        with open(cdn_file, 'r') as file:
            for line in file.readlines():
                self.cdn_total.append(line.strip().lower())

    def cname(self, cname=None):
        if cname is None:
            return False, None
        for cdn, v in self.cname_cache.items():
            for cdn_cname in v['cname_substring'].split(' '):
                if cname.find(cdn_cname) != -1:
                    return True, cdn
        return False, None

    def get_http_header(self, domain, ip):
        try:
            # since some website may focus on one http protocol, so we crawl both http and https
            # print("curl -s -I https://%s -H 'Host:%s' -k " % (ip, domain))
            http_header = subprocess.check_output("curl -m 3 -s -IL %s -H 'Host:%s' -k " %
                                                   (ip, domain), shell=True).decode('utf-8', "ignore")
            https_header = subprocess.check_output("curl -m 3 -s -IL 'https://%s' -H 'Host:%s' -k " %
                                                   (ip, domain), shell=True).decode('utf-8', "ignore")
            #status_code = subprocess.check_output("curl -m 3 -s -IL https://%s -H 'Host:%s' -k -o /dev/null -w %{http_code} " %
            #                                       (ip, domain), shell=True).decode('utf-8', "ignore")    #get http_code
            #if status_code == 200:
            #    https_header = subprocess.check_output("curl -m 3 -s -IL https://%s -H 'Host:%s' -k " %
            #                                       (ip, domain), shell=True).decode('utf-8', "ignore")
            
        except Exception as e:
            http_header = ""
        #try:
        #    http_header = subprocess.check_output("curl -m 3 -s -IL http://%s -H 'Host:%s' -k " %
        #                                          (ip, domain), shell=True).decode('utf-8', "ignore")
        #except Exception as e:
        #    http_header = ""
        return http_header

    def get_tls_cert(self, domain, ip):
        try:
            # only https has the tls certificate
            tls_cert = subprocess.check_output(
                "curl --insecure -m 3 -v https://%s -H 'Host:%s' 2>&1 | awk 'BEGIN {cert=0 } /^\\* SSL connection/ { cert=1 } /^\\*/ { if (cert) print }' " %
                (ip, domain), shell=True).decode(
                'utf-8', "ignore")
            return tls_cert
        except subprocess.TimeoutExpired as time_e:
            return "None"
        except subprocess.CalledProcessError as call_e:
            print(call_e)
            return "None"

    def http_finger(self, header=None):
        def convert_reserved_regex_symbols(regex):
            reserved_regex_symbols = {
                "*": "[^:,]*",
                " ": "\\s+"
            }
            for k, v in reserved_regex_symbols.items():
                regex = regex.replace(k, v)
            return regex

        patterns = json.load(open(get_resource_path("pattern.json"), 'r'))
        regex = '''(%s)\\s*(:)\\s*(%s)\\s*,?'''
        cdns = []
        key_http_header = ""
        for hypergiant, header_pairs in patterns.items():
            for header_pair in header_pairs:
                name = header_pair[0]
                if len(header_pair) == 2:
                    value = header_pair[1]
                else:
                    value = "*"

                name = convert_reserved_regex_symbols(name)
                value = convert_reserved_regex_symbols(value)

                pattern = regex % (name, value)
                ans = re.search(pattern, header, re.IGNORECASE)
                if ans is not None:
                    cdns.append(hypergiant.lower())
                    key_http_header += "  "
                    key_http_header += ans.group()
        return key_http_header, list(set(cdns))

    def cert(self, cert=None):
        if cert is not None:
            cert = cert.lower()
            for cdn in self.cdn_total:
                s = cert.find(cdn)
                if s != -1:
                    return cdn
        return None

    def download_rdap_info(self, IP):
        rdap_info = None
        rdap_retries_counter = 3
        start_ts, end_ts = time.time(), time.time()
        if IP:
            while rdap_info is None and rdap_retries_counter > 0:
                try:
                    with warnings.catch_warnings():
                        warnings.filterwarnings("ignore", category=UserWarning)
                        rdap_info = ipwhois.IPWhois(IP).lookup_rdap(
                            rate_limit_timeout=10)
                except ipwhois.exceptions.HTTPRateLimitError as e:
                    r = random.randint(60, 90)
                    time.sleep(r)
                except ipwhois.exceptions.HTTPLookupError as e:
                    r = random.randint(10, 20)
                    time.sleep(r)
                    rdap_retries_counter -= 1
                except Exception as e:
                    break
        end_ts = time.time()
        return (rdap_info, start_ts, end_ts)

    def download_info_using_rdap_cache(self, IP):
        def ts_is_valid(PREFIX):
            if PREFIX in self.cidr_time:
                ts_fetched = self.cidr_time[PREFIX]
                return (time.time() - ts_fetched) < self.rdap_refresh
            return False

        def extract_cidr_from_rdapinfo(RDAP_INFO):
            cidr = None
            if RDAP_INFO is not None and \
                "network" in rdap_info and \
                    "cidr" in RDAP_INFO["network"]:
                cidr = rdap_info["network"]["cidr"]
                if "," in cidr:
                    cidr_list = [el.strip().split("/") for el in cidr.split(",")]
                    cidr_list = sorted(cidr_list, key=lambda t: int(t[1]), reverse=True)
                    cidr = "%s/%s" % (cidr_list[0][0], cidr_list[0][1])
                return cidr

        cache_hit = False
        start_ts = time.time()
        end_ts = start_ts
        if IP in self.rdap_cache_ip:
            cidr = "%s/32" % (IP)
            if ts_is_valid(cidr):
                rdap_info = self.rdap_cache_ip[IP]
                cache_hit = True
        if cache_hit is False:
            int_ip = IPNetwork(IP).first
            elems = list(self.rdap_cache[int_ip])
            if len(elems) > 1:
                list_elems = [(e, e.end - e.begin) for e in elems]
                list_elems = sorted(list_elems, key=lambda el: el[1])
                elems = [list_elems[0][0]]
            if len(elems) == 1:
                rdap_info = elems[0].data
                cidr = extract_cidr_from_rdapinfo(rdap_info)
                if cidr is not None and ts_is_valid(cidr):
                    cache_hit = True
        if cache_hit is False:
            (rdap_info, start_ts,
             end_ts) = self.download_rdap_info(IP)
            # then we have to update the cache with the new range
            cidr = extract_cidr_from_rdapinfo(rdap_info)
            if cidr is not None:
                ipnet = IPNetwork(cidr)
                range_start = ipnet.first
                range_end = ipnet.last
                if range_start != range_end:
                    self.rdap_cache[range_start:range_end] = rdap_info
                else:
                    self.rdap_cache_ip[IP] = rdap_info
                self.cidr_time[cidr] = time.time()
        return rdap_info

    def extract_rdap_info(self, rdap_info):  # keep asn, asn_description, object_name_list
        rdap_info_dict = {}
        if rdap_info:
            if "asn_description" in rdap_info:
                rdap_info_dict["asn_description"] = rdap_info['asn_description']
            else:
                rdap_info_dict["asn_description"] = None
            if "asn" in rdap_info:
                rdap_info_dict["asn"] = rdap_info['asn']
            else:
                rdap_info_dict["asn"] = None
            if "network" in rdap_info and rdap_info['network'] is not None:
                if 'remarks' in rdap_info['network']:
                    # print(rdap_info['network']['remarks'])
                    rdap_info_dict["remarks"] = rdap_info['network']['remarks']
                else:
                    rdap_info_dict["remarks"] = None
            # name_set = set([])
            # if 'objects' in rdap_info:
            #     for value in rdap_info['objects'].values():
            #         if 'contact' in value and value['contact'] is not None:
            #             contact = value['contact']
            #             if 'name' in contact and \
            #                contact['name'] is not None:
            #                 name_set.add(contact['name'])
            # name_list = list(name_set) if len(name_set) > 0 else None
            # rdap_info_dict['object_name_list'] = name_list
            return rdap_info_dict
        else:
            return None

    def rdap(self, rdap_info):
        rdap_info_text = ""
        if "asn_description" in rdap_info and rdap_info['asn_description'] is not None:
            rdap_info_text += str(rdap_info['asn_description']).lower()
        # if "object_name_list" in rdap_info and rdap_info["object_name_list"] != None:
        #     rdap_info_text += " "
        #     for name in rdap_info["object_name_list"]:
        #         rdap_info_text += name.lower()
        #         rdap_info_text += " "
        if 'remarks' in rdap_info and rdap_info['remarks'] is not None:
            rdap_info_text += str(rdap_info['remarks']).lower()
        if rdap_info_text != "":
            for cdn in self.cdn_total:
                s = rdap_info_text.find(cdn)
                if s != -1:
                    return cdn
        return None

    def identify_cdn_byip(self, domain, ip):
        try:
            http_header = self.get_http_header(domain, ip)
            http_key_header, http_header_cdn = self.http_finger(http_header)
        except Exception as e:
            print(e)
            print("http resolve error")
            http_header_cdn = None

        try:
            cert_info = self.get_tls_cert(domain, ip)
            cert_info_cdn = self.cert(cert_info)
        except Exception as e:
            print(e)
            print("TLS_cert resolve error")
            cert_info_cdn = None

        rdap_info = self.download_info_using_rdap_cache(ip)
        if rdap_info is not None:
            # get useful information of rdap info
            extracted_rdap_info = self.extract_rdap_info(rdap_info)
            if extracted_rdap_info is not None:
                rdap_info_cdn = self.rdap(extracted_rdap_info)
                

        if len(http_header_cdn) != 0:
            self.key["http_header"].append(http_key_header)
            if rdap_info_cdn == None or rdap_info_cdn not in http_header_cdn:
                self.key["off_net"].append(ip)
            return "http_header", http_header_cdn
        elif cert_info_cdn is not None:
            self.key["tls_cert"].append(cert_info)
            return "tls_cert", cert_info_cdn
        elif rdap_info_cdn is not None:
            self.key["rdap_info"].append(extracted_rdap_info)
            return "rdap_info", rdap_info_cdn
        # except Exception as e:
        #     print(e)
        #     print("RDAP info resolve error")
        #     rdap_info_cdn = None

        return "", ""

    def web_hosting(self, dns_dict):
        count_ip = sum(len(item) for key, item in dns_dict.items())
        anycast_cdn = ["cloudflare", "imperva", "edgio", "fastly", "microsoft", "cloudfront","ovh"]
        if count_ip == 1:
            if len(self.cdn_list) > 0 and self.cdn_list[0] not in anycast_cdn:
                return True
        return False

    def identify_cdn(self, domain, dns_dict):
        self.cdn_list = []
        # self.off_net = []
        # self.dns_hijack = []
        self.key = {"cname": [], "http_header": [], "tls_cert": [], "rdap_info": [], "off_net": [], "web_hosting":False}
        # ip_cdn_map = {}
        rdap_cdn = {}
        count_ip = sum(len(item) for key, item in dns_dict.items())

        for cname, ip_list in dns_dict.items():
            flag, cdn = self.cname(cname)

            if flag == True:
                self.cdn_list.append(cdn)
                self.key["cname"].append(cname)
                count_ip -= len(ip_list)
            else:
                lock = threading.Lock()
                threads = []

                def multi_thread(ip):
                    ki, cdn = self.identify_cdn_byip(domain, ip)
                    if ki == "http_header":
                        with lock:
                            self.cdn_list.extend(cdn)
                            # ip_cdn_map[ip] = cdn
                    elif ki == "tls_cert":
                        with lock:
                            self.cdn_list.append(cdn)
                            # ip_cdn_map[ip] = cdn
                    elif ki == "rdap_info":
                        with lock:
                            if cdn in rdap_cdn:
                                rdap_cdn[cdn] += 1
                                # ip_cdn_map[ip] = cdn
                            else:
                                rdap_cdn[cdn] = 1
                                # ip_cdn_map[ip] = cdn
                    # else:
                    #     ip_cdn_map[ip] = None

                for ip in ip_list:
                    thread = threading.Thread(target=multi_thread, args=(ip,))
                    threads.append(thread)
                    thread.start()

                stime = time.time()

                while True:
                    time.sleep(0.2)
                    exit_counter = 0
                    for thread in threads:
                        if not thread.is_alive():
                            exit_counter += 1
                    print("\r", end="")
                    print("%-10s Time:%.1f" % ("CDN",time.time() - stime),"progress: %5.1f%% %d/%d: " % (exit_counter / len(ip_list) * 100,exit_counter,len(ip_list)), "▋" * (exit_counter * 50 // len(ip_list)), end="")

                    sys.stdout.flush()
                    if exit_counter == len(ip_list):
                        break
                    if (time.time() - stime)>60:
                        break
                print()
                
        for index, number in rdap_cdn.items():
            if number > count_ip / 2:
                self.cdn_list.append(index)
        #if len(self.cdn_list) != 0:
            # self.key["dns_hijack"] = [x for x,y in ip_cdn_map.items() if y==None]
            # for ip, cdn in ip_cdn_map.items():
            #     if cdn == None
        if self.web_hosting(dns_dict):
            self.key["web_hosting"] = True
            return [cdn + " (likely hosted on cloud)" for cdn in list(set(self.cdn_list))]
        return list(set(self.cdn_list))
