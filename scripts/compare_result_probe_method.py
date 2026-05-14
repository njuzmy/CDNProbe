import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cdnprobe import DnsResolver
from cdnprobe.paths import dns_asset


test_domain = [
    "www.jd.com",
    "www.microsoft.com",
    "www.apple.com",
    "www.cctv.com",
    "www.ups.com",
    "www.samsung.com",
    "www.nike.com",
    "www.qoo10.sg",
    "www.taleo.net",
    "www.dhl.com",
    "www.marriott.com",
    "www.apple.com.cn",
    "www.delta.com",
    "www.uniqlo.com",
    "www.agoda.com",
    "www.playstation.com",
    "www.hermes.com",
    "www.fendi.com",
    "www.mi.com",
    "www.huawei.com",
    "www.prada.com",
    "www.celine.com",
    "www.lg.com",
    "www.miumiu.com",
    "www.sc.com",
    "www.lufthansa.com",
    "www.lightinthebox.com",
    "www.dhgate.com",
    "www.dealmoon.com",
    "www.singaporeair.com",
    "www.amd.com",
    "www.volvocars.com",
    "www.ana.co.jp",
    "www.cctv.cn",
    "www.hyatt.com",
    "www.redhat.com",
    "www.etihad.com",
    "www.intel.cn",
    "www.burberry.com",
    "www.nespresso.com",
    "www.netacad.com",
    "www.ti.com.cn",
    "www.zara.cn",
    "www.saxotrader.com",
    "www.lincoln.com.cn",
    "www.thermofisher.com",
    "www.abcam.cn",
]


def main():
    resolver = DnsResolver(dns_asset("test_prefix.txt"))
    inconsist_domain = []
    for domain in test_domain[35:]:
        zdns_result = resolver.zdns(domain)
        zdns_prefix = resolver.dns_record
        dig_result, _ = resolver.query_and_resolve_with_subnets(domain)
        dig_prefix = resolver.dns_record
        if zdns_result.keys() != dig_result.keys():
            inconsist_domain.append(domain)
            print(domain)
            print(zdns_prefix)
            print(dig_prefix)
            for index in zdns_prefix.keys():
                if zdns_prefix[index] != dig_prefix[index]:
                    print(index)
                    print(zdns_prefix[index], dig_prefix[index])
    print(inconsist_domain)


if __name__ == "__main__":
    main()
