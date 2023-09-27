import json
import subprocess

def validate(domain, cdn_list):
    cdn_ip_dict = json.load(open("../resource/cdn_ip.json", 'r'))
    for cdn in cdn_list:
        try:
            http_code = subprocess.check_output(f"curl -m 3 -s -IL {cdn_ip_dict[cdn]} -H 'Host:{domain}' -k -o /dev/null -w %{'{http_code}'}", shell=True).decode('utf-8', "ignore")
            if int(http_code[0]) >= 3:
                return False
        except:
            pass
    return True
        