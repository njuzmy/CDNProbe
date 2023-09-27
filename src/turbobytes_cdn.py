import time
import threading
import pandas as pd
import json
import subprocess
import os

QTYPE_HTTP=0
QTYPE_HTTP_WWW=1
QTYPE_HOST=2
QTYPE_HOST_WWWW=3
QTYPE_HTTPS=4
QTYPE_HTTPS_WWW=5

base_dirpath="turbobytes_ans"
os.makedirs(base_dirpath,exist_ok=True)

def get_cmd(domain,qtype):
    cmds=[]
    cmds.append('''curl -X POST -d '{"url": "http://%s"}' -H "Content-Type: application/json" http://127.0.0.1:1337/''' % (domain))
    cmds.append('''curl -X POST -d '{"url": "http://www.%s"}' -H "Content-Type: application/json" http://127.0.0.1:1337/''' % (domain))
    cmds.append('''curl -X POST -d '{"hostname": "%s"}' -H "Content-Type: application/json" http://127.0.0.1:1337/hostname/''' % (domain))
    cmds.append('''curl -X POST -d '{"hostname": "www.%s"}' -H "Content-Type: application/json" http://127.0.0.1:1337/hostname/''' % (domain))
    cmds.append('''curl -X POST -d '{"url": "https://%s"}' -H "Content-Type: application/json" http://127.0.0.1:1337/''' % (domain))
    cmds.append('''curl -X POST -d '{"url": "https://www.%s"}' -H "Content-Type: application/json" http://127.0.0.1:1337/''' % (domain))
    return cmds[qtype]
    

def fun(domain):
    # try:
    #     cmd='''curl -X POST -d '{"url": "http://%s"}' -H "Content-Type: application/json" http://127.0.0.1:1337/''' % (domain)
    #     print(cmd)
    #     dns_message = subprocess.check_output(cmd, shell=True).decode('utf-8', "ignore")
    #     print(dns_message)

    #     ans=json.loads(dns_message)
    #     return ans
    # except Exception as e:
    #     print(e)
    #     with open("error.log","a") as f:
    #         f.write(domain+"\n")
        
    ans = {}
    error_counter=0
    for i in range(4):
        try:
            cmd=get_cmd(domain,i)
            print(cmd)
            dns_message = subprocess.check_output(cmd, shell=True).decode('utf-8', "ignore")

            try:
                msg=json.loads(dns_message)
            except:
                msg=dns_message

            ans[i]=msg
        except Exception as e:
            print(e)
            error_counter+=1

    if error_counter==4:
        with open(os.path.join(base_dirpath,"error.log"),"a") as f:
            f.write(domain+"\n")    
    return ans



if __name__ == "__main__":
    websites = pd.read_csv("top-1m.csv")["domain"][0:5000].to_list()
    stime = time.time()

    result_dict = {}
    cnt=1
    for website in websites:
        # website = "www."+website

        print("\n"*2)
        print(f"{cnt}/{len(websites)}")
        print(website)
        cnt+=1
        result = fun(website)
        result_dict[website] = result

        with open(os.path.join(base_dirpath,f"9-19_{time.time()}.json"),'w') as f:
            json.dump(result_dict, f, indent=4)

    with open(os.path.join(base_dirpath,'ans.json'), 'w') as f:
            json.dump(result_dict, f, indent=4)
    print(time.time() - stime)

