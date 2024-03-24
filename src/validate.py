import json
import subprocess
import re
import os
import utils
import threading

res_dirpath = "../resource"
cdn_to_ns_filename = "cdn_to_ns_ans.json"


def get_resource_path(filename):
    return os.path.join(res_dirpath, filename)


def validate(domain, cdn_list):
    cdn_ip_dict = json.load(open("../resource/cdn_ip.json", 'r'))
    validated = []
    for cdn in cdn_list:
        cdn = re.sub('\(.*?\)', '', cdn).strip()
        try:
            http_code = subprocess.check_output(
                f"curl -m 3 -s -I {cdn_ip_dict[cdn]} -H 'Host:{domain}' -k -o /dev/null -w %{'{http_code}'}", shell=True).decode('utf-8', "ignore")
            https_code = subprocess.check_output(
                f"curl -m 3 -s -H 'Cache-Control: no-cache' -H 'Host:{domain}' -I --resolve {domain}:443:{cdn_ip_dict[cdn]} https://{domain} -k -o /dev/null -w %{'{http_code}'}", shell=True).decode('utf-8', "ignore")
            print(http_code, https_code)
            if int(http_code[0]) == 2:
                validated.append(cdn)
        except Exception as e:
            print(e)
            pass
    return validated


def validate_cname_ns(domain, cdn_list):
    cdn_ns_dist = json.load(open(get_resource_path("cdn_to_ns_ans.json"), "r"))
    validate_ans = []
    lock = threading.Lock()

    def get_ans_key(domain, ns):
        return str(domain) + "@" + str(ns)

    def validate_query(domain, ns, res):
        try:
            ns_ip = utils.query_and_resolve(ns, "A")[0]
            ans = utils.query_and_resolve(domain, "A", False, ns_ip)
        except:
            ans = []
        with lock:
            res[get_ans_key(domain, ns)] = ans

    for cdn in cdn_list:
        print("##################")
        print("##################")
        cdn = re.sub('\(.*?\)', '', cdn).strip()
        cname = utils.query_and_resolve(domain, "CNAME", True)
        domain = cname[0] if cname else domain
        print(domain)
        cdn_ns_dist.setdefault(cdn, [])
        validated = False
        res = {}
        for ns in cdn_ns_dist[cdn]:
            print(ns)
            thread = threading.Thread(target=validate_query,
                                      args=(domain, ns, res), daemon=True)
            thread.start()
            thread.join(3)
            if thread.is_alive():
                ans = []
            else:
                with lock:
                    ans = res[get_ans_key(domain, ns)]

            if ans:
                validated = True
                break
        validate_ans.append(validated)
    return validate_ans


if __name__ == "__main__":
    # print(validate("www.playsport.cc", [
    #       "cloudflare", "google (dsfds)", "facebook", "chinanetcenter"]))
    print(validate_cname_ns("www.playsport.cc", [
          "cloudflare", "google", "facebook", "chinanetcenter"]))
    exit(0)
