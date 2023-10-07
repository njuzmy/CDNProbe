import sys
sys.path.append("..")
import src.mydns

domain = "www.uniqlo.com"
d = src.mydns.DnsResolve("../resource/prefix1.txt")
zdns_result = d.zdns(domain)
dig_result, ip_number = d.yzx_process_resolve(domain)

print(zdns_result.keys())
print(dig_result.keys())
