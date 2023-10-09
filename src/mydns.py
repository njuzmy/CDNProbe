import json
import subprocess
import threading
import time
import dns
import clientsubnetoption


class DnsResolve:
    def __init__(self, file=None, resolver='223.5.5.5') -> None:
        self.resolver = resolver
        self.dnsrecord = {}
        self.comvp = []
        if file is not None:
            with open(file, 'r') as rel_file:
                res = rel_file.read()
                self.comvp = res.strip().split(',')
                self.comvp = self.comvp
        self.comvplen = len(self.comvp)

    def resolve(self, domain, prefix=None):
        if prefix is not None:
            try:
                dns_message = subprocess.check_output("echo %s | ../zdns/zdns A --client-subnet %s --name-servers %s" % (domain, prefix, self.resolver), shell=True).decode('utf-8', "ignore")
                return dns_message
            except Exception as e:
                print(e)
                return None

    def zdns(self, domain):
        cname_prefix = {}
        for prefix in self.comvp:
            dns_message = self.resolve(domain, prefix)
            #print(dns_message)
            if dns_message != None:
                cname, ip = self.result(json.loads(dns_message))
                if cname in cname_prefix.keys():
                    if ip not in cname_prefix[cname] and ip is not None:
                        cname_prefix[cname].append(ip)
                elif ip is not None:
                    cname_prefix[cname] = [ip]
                self.dnsrecord[prefix] = cname
        return cname_prefix

    def result(self, dns_message):
        if dns_message['status'] == "NOERROR" and "answers" in dns_message["data"].keys():
            rr = [v["type"] for k, v in enumerate(dns_message["data"]["answers"]) if 'type' in v.keys()]
            if "CNAME" in rr:
                cname_index = [k for k, v in enumerate(dns_message["data"]['answers']) if v['type'] == "CNAME"]
                cname = dns_message['data']['answers'][cname_index[-1]]['answer']  # get the last CNAME
            else:
                cname = None
            if "A" in rr:
                a_index = [k for k, v in enumerate(dns_message["data"]['answers']) if v['type'] == "A"]
                ip = dns_message['data']['answers'][a_index[0]]['answer']  # get A record of the domain
            else:
                ip = None
            return (cname, ip)
        else:
            return (None, None)

    def yzx_result(self, dns_message):
        if ";ANSWER" in dns_message:
            lines = dns_message.split("\n")
            is_in_answer = False
            a_record = None
            cname = None
            for line in lines:
                if is_in_answer:
                    res = line.split()[-1]
                    if " IN A" in line:
                        if a_record is None:
                            a_record = res
                    if " IN CNAME" in line:
                        cname = res
                    if " IN "not in line:
                        break
                elif line == ";ANSWER":
                    is_in_answer = True

            return (cname, a_record)
        else:
            return (None, None)

    def process_resolve(self, domain):
        cname_prefix = {}
        lock = threading.Lock()

        def resolve(domain, prefix):
            try:
                # print(domain, prefix, self.resolver)
                # TODO
                dns_message = subprocess.check_output("echo %s | ../zdns/zdns A --client-subnet %s --name-servers %s" % (domain, prefix, self.resolver), shell=True).decode('utf-8', "ignore")
            except Exception as e:
                print(e)
                dns_message = None

            with lock:
                print(dns_message)
                # dnsresults.append(json.loads(dns_message))
                if dns_message != None:
                    cname, ip = self.result(json.loads(dns_message))
                    if cname in cname_prefix.keys():
                        if ip not in cname_prefix[cname] and ip is not None:
                            cname_prefix[cname].append(ip)
                    elif ip is not None:
                        cname_prefix[cname] = [ip]
                    self.dnsrecord[prefix] = cname

        threads = []
        for prefix in self.comvp:
            thread = threading.Thread(target=resolve, args=(domain, prefix))
            threads.append(thread)
            thread.start()

        while True:
            time.sleep(0.2)
            exit_counter = 0
            # for i in range(len(dnsresults)):
            #     if isinstance(dnsresults[i], dict):
            #         done_counter+=1
            #     exit_counter = 0
            for thread in threads:
                if not thread.is_alive():
                    exit_counter += 1

            if exit_counter == len(self.comvp):
                break
        return cname_prefix

    def yzx_process_resolve(self, domain):
        cname_prefix = {}
        ip_number = {}
        lock = threading.Lock()
        stop_signal=False
        self.dnsrecord={}

        def is_stopped():
            return stop_signal

        def resolve(domain, prefix):
            try:
                # print(domain, prefix, self.resolver)

                # TODO TODO
                subnet = prefix.strip(" '").split('/')[0]
                cso = clientsubnetoption.ClientSubnetOption(subnet)
                message = dns.message.make_query(domain, 'A')
                message.use_edns(options=[cso])
                dns_message = dns.query.udp(message, self.resolver)

            except Exception as e:
                print(e)
                dns_message = None
            if is_stopped():
                return

            # TODO TODO
            if dns_message is not None:
                cname, ip = self.yzx_result(dns_message.to_text())

            # dnsresults.append(json.loads(dns_message))
            # cname, ip = self.result(json.loads(dns_message))
                if cname in cname_prefix.keys():
                    if ip not in cname_prefix[cname] and ip is not None:
                        with lock:
                            cname_prefix[cname].append(ip)
                elif ip is not None:
                    with lock:
                        cname_prefix[cname] = [ip]
                with lock:
                    self.dnsrecord[prefix] = cname
                if ip in ip_number.keys():
                    ip_number[ip] += 1
                else:
                    ip_number[ip] = 1

        
        threads = []
        for prefix in self.comvp:
            thread = threading.Thread(target=resolve, args=(domain, prefix))
            threads.append(thread)
            thread.start()

        stime = time.time()
        while True:
            time.sleep(0.2)
            exit_counter = 0
            # for i in range(len(dnsresults)):
            #     if isinstance(dnsresults[i], dict):
            #         done_counter+=1
            #     exit_counter = 0






            for thread in threads:
                if not thread.is_alive():
                    exit_counter += 1
            print("\r", end="")
            print("%-10s Time:%.1f" % ("DNS",time.time() - stime), "progress: %5.1f%% %d/%d: " % ((exit_counter / self.comvplen) * 100, exit_counter, self.comvplen), "▋" * (exit_counter * 50 // self.comvplen), end="")

            if exit_counter == len(self.comvp):
                break
            if (time.time() - stime)>2 and (exit_counter / self.comvplen)> 0.99:
                break
            if (time.time() - stime)>10 and (exit_counter / self.comvplen)> 0.95:
                break
            if (time.time() - stime)>30:                
                break
        stop_signal = True
        print()
        return cname_prefix, ip_number

    def dns_result_prefix(self, domain):  # unify the formats for analyze
        cname_prefix = {}
        for addr in self.comvp:
            result = self.resolve(domain, addr)
            if result is not None:
                cname, ip = self.result(json.loads(result))
                if cname in cname_prefix.keys():
                    if ip not in cname_prefix[cname] and ip is not None:
                        cname_prefix[cname].append(ip)
                elif ip is not None:
                    cname_prefix[cname] = [ip]

        return cname_prefix
