import json
import subprocess
import re

def validate(domain, cdn_list):
    cdn_ip_dict = json.load(open("../resource/cdn_ip.json", 'r'))
    validated = []
    for cdn in cdn_list:
        cdn = re.sub('\(.*?\)','',cdn).strip()
        try:
            http_code = subprocess.check_output(f"curl -m 3 -s -I {cdn_ip_dict[cdn]} -H 'Host:{domain}' -k -o /dev/null -w %{'{http_code}'}", shell=True).decode('utf-8', "ignore")
            https_code = subprocess.check_output(f"curl -m 3 -s -H 'Cache-Control: no-cache' -H 'Host:{domain}' -I --resolve {domain}:443:{cdn_ip_dict[cdn]} https://{domain} -k -o /dev/null -w %{'{http_code}'}", shell=True).decode('utf-8', "ignore")
            print(http_code, https_code)
            if int(http_code[0]) == 2:
                validated.append(cdn)
        except Exception as e:
            print(e)
            pass
    return validated
        
if __name__=="__main__":
    print(validate("www.playsport.cc",["cloudflare", "google (dsfds)", "facebook","chinanetcenter"]))
