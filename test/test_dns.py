import sys
sys.path.append("..")
import src.mydns

domain = "www.uniqlo.com"
test_domain = ['www.jd.com',
 'www.microsoft.com',
 'www.apple.com',
 'www.cctv.com',
 'www.ups.com',
 'www.samsung.com',
 'www.nike.com',
 'www.qoo10.sg',
 'www.taleo.net',
 'www.dhl.com',
 'www.marriott.com',
 'www.apple.com.cn',
 'www.delta.com',
 'www.uniqlo.com',
 'www.agoda.com',
 'www.playstation.com',
 'www.hermes.com',
 'www.fendi.com',
 'www.mi.com',
 'www.huawei.com',
 'www.prada.com',
 'www.celine.com',
 'www.lg.com',
 'www.miumiu.com',
 'www.sc.com',
 'www.lufthansa.com',
 'www.lightinthebox.com',
 'www.dhgate.com',
 'www.dealmoon.com',
 'www.singaporeair.com',
 'www.amd.com',
 'www.volvocars.com',
 'www.ana.co.jp',
 'www.cctv.cn',
 'www.hyatt.com',
 'www.redhat.com',
 'www.etihad.com',
 'www.intel.cn',
 'www.burberry.com',
 'www.nespresso.com',
 'www.netacad.com',
 'www.ti.com.cn',
 'www.zara.cn',
 'www.saxotrader.com',
 'www.lincoln.com.cn',
 'www.thermofisher.com',
 'www.abcam.cn']
# test_domain=["www.redhat.com"]
d = src.mydns.DnsResolve("../resource/test_prefix.txt")
inconsist_domain = []
for domain in test_domain[35:]:
    zdns_result = d.zdns(domain)
    zdns_prefix = d.dnsrecord
    dig_result, ip_number = d.process_resolve(domain)
    dig_prefix = d.dnsrecord
    # print(zdns_result.keys())
    # print(dig_result.keys())
    if zdns_result.keys()!=dig_result.keys():
        inconsist_domain.append(domain)
        print(domain)
        print(zdns_prefix)
        print(dig_prefix)
        for index in zdns_prefix.keys():
            if zdns_prefix[index] != dig_prefix[index]:
                print(index)
                print(zdns_prefix[index], dig_prefix[index])
print(inconsist_domain)
    #print(zdns_result.keys()==dig_result.keys())