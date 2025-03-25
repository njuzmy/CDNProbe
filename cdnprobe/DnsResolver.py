from concurrent.futures import ThreadPoolExecutor
import json
import queue
import subprocess
import threading
import time
import dns
import clientsubnetoption
import asyncio
from cdnprobe.utils import create_progress


class DnsResolver:
    def __init__(self, filepath_prefixs=None, dns_server='223.5.5.5') -> None:
        self.dns_server = dns_server
        self.dns_records = {}
        self.prefixs = []
        self.subnets = []

        if filepath_prefixs is not None:
            with open(filepath_prefixs, 'r') as rel_file:
                res = rel_file.read()
                self.prefixs = res.strip().split(',')
                self.prefixs = [prefix.strip().strip("'") for prefix in self.prefixs]
                self.prefixs = [prefix for prefix in self.prefixs if prefix != ""]

                self.subnets = [self.convert_prefix_to_subnet(prefix) for prefix in self.prefixs]

        self.len_subnets = len(self.subnets)

    def convert_prefix_to_subnet(self, prefix):
        return prefix.split('/')[0]

    def resolve(self, domain, prefix=None):
        if prefix is not None:
            try:
                dns_message = subprocess.check_output("echo %s | ../zdns/zdns A --client-subnet %s --name-servers %s" % (
                    domain, prefix, self.dns_server), shell=True).decode('utf-8', "ignore")
                return dns_message
            except Exception as e:
                print(e)
                return None

    def zdns(self, domain):
        cname_prefix = {}
        for prefix in self.subnets:
            dns_message = self.resolve(domain, prefix)
            # print(dns_message)
            if dns_message is not None:
                cname, ip = self.resolve_response(json.loads(dns_message))
                if cname in cname_prefix.keys():
                    if ip not in cname_prefix[cname] and ip is not None:
                        cname_prefix[cname].append(ip)
                elif ip is not None:
                    cname_prefix[cname] = [ip]
                self.dns_records[prefix] = cname
        return cname_prefix

    def resolve_response(self, dns_message):
        if not isinstance(dns_message, str):
            dns_message = dns_message.to_text()
        if ";ANSWER" in dns_message:
            lines = dns_message.split("\n")
            is_in_answer = False
            a_record = None  # TODO: Mutlti A record
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

    def query_and_resolve_with_subnets(self, domain, qtype="A"):
        cname_prefix = {}
        ip_number = {}

        self.dns_record = {}

        response_queue = queue.Queue()

        def resolve_handler():
            while True:
                try:
                    subnet, response = response_queue.get(timeout=1)
                    if subnet is None:  # stop signal
                        break

                    if response is not None:
                        cname, ip = self.resolve_response(response)
                        if cname in cname_prefix.keys():
                            if ip not in cname_prefix[cname] and ip is not None:
                                cname_prefix[cname].append(ip)
                        elif ip is not None:
                            cname_prefix[cname] = [ip]
                        self.dns_records[subnet] = {"cname": cname, "ip": ip}
                        if ip in ip_number.keys():
                            ip_number[ip] += 1
                        else:
                            ip_number[ip] = 1

                except queue.Empty:
                    continue

        def query_with_subnet(domain, subnet):
            try:

                # TODO TODO
                subnet = subnet.strip(" '").split('/')[0]
                cso = clientsubnetoption.ClientSubnetOption(subnet)
                message = dns.message.make_query(domain, qtype)
                message.use_edns(options=[cso])
                response = dns.query.udp(message, self.dns_server, timeout=60)

            except Exception as e:
                print(f"# {subnet}: {e} {subnet}")
                response = None

            return response

        thread_resolve_handler = threading.Thread(target=resolve_handler)
        thread_resolve_handler.start()

        with ThreadPoolExecutor(max_workers=128) as executor:
            futures = {
                executor.submit(query_with_subnet, domain, subnet): subnet for subnet in self.subnets
            }

            stime = time.time()
            n_dones = 0

            with create_progress() as progress:
                progress_task = progress.add_task("DNS Resolve", total=self.len_subnets)

                while True:
                    time.sleep(0.2)

                    done_futures = []
                    for future, subnet in futures.items():
                        if future.done():
                            n_dones += 1
                            try:
                                response_queue.put((subnet, future.result()))
                            except Exception as e:
                                print(f"Error: {e}")
                                self.dns_records[subnet] = {"cname": None, "ip": None}

                            done_futures.append(future)

                    progress.update(progress_task, completed=n_dones)
                    for future in done_futures:
                        del futures[future]

                    if n_dones == len(self.subnets):
                        break
                    if (time.time() - stime) > 2 and (n_dones / self.len_subnets) > 0.99:
                        break
                    if (time.time() - stime) > 10 and (n_dones / self.len_subnets) > 0.95:
                        break
                    if (time.time() - stime) > 30:
                        break

        response_queue.put((None, None))
        thread_resolve_handler.join()

        return cname_prefix, ip_number

    async def async_process_resolve(self, domain, resolver):
        cname_prefix = {}
        ip_number = {}
        self.dns_records = {}

        async def async_resolve(domain, prefix):
            try:
                subnet = dns.edns.ECSOption.from_text(prefix.strip(" '"))
                message = dns.message.make_query(
                    domain, 'A', use_edns=0, options=[subnet])
                dns_message = await dns.asyncquery.udp(message, resolver, timeout=10)

            except Exception as e:
                # print(repr(e))
                return None

            if dns_message is not None:
                cname, ip = self.yzx_result(dns_message.to_text())
            else:
                return None

            return prefix, cname, ip

        threads = []
        for prefix in self.subnets:
            threads.append(asyncio.create_task(async_resolve(domain, prefix)))
        stime = time.time()
        n_done = 0
        while True:
            done, pending = await asyncio.wait(threads, timeout=0.2, return_when=asyncio.FIRST_COMPLETED)

            n_done += len(done)
            for thread in done:
                x = await thread
                if x:
                    prefix, cname, ip = x
                    cname_prefix.setdefault(cname, set()).add(ip)
                    self.dns_records[prefix] = cname
                    ip_number[ip] = ip_number.setdefault(ip, 0) + 1
            threads = pending
            print("\r", end="")
            print("%-10s Time:%.1f" % ("DNS", time.time() - stime), "progress: %5.1f%% %d/%d: " % ((n_done /
                  self.len_subnets) * 100, n_done, self.len_subnets), "▋" * (n_done * 50 // self.len_subnets), end="")

            if n_done == len(self.subnets):
                break
            if (time.time() - stime) > 2 and (n_done / self.len_subnets) > 0.99:
                break
            if (time.time() - stime) > 10 and (n_done / self.len_subnets) > 0.95:
                break
            if (time.time() - stime) > 30:
                break

        for thread in pending:
            thread.cancel()
        return cname_prefix, ip_number

    def dns_result_prefix(self, domain):  # unify the formats for analyze
        cname_prefix = {}
        for addr in self.subnets:
            result = self.resolve(domain, addr)
            if result is not None:
                cname, ip = self.resolve_response(json.loads(result))
                if cname in cname_prefix.keys():
                    if ip not in cname_prefix[cname] and ip is not None:
                        cname_prefix[cname].append(ip)
                elif ip is not None:
                    cname_prefix[cname] = [ip]

        return cname_prefix
