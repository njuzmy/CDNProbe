from cdnprobe import CdnDetector, DnsResolver
from cdnprobe.paths import cdn_asset, dns_asset


def detect(domain, resolver=None, cname_cache_path=None, cdn_list_path=None, pattern_path=None):
    resolver = resolver or DnsResolver(dns_asset("prefix.txt"))
    detector = CdnDetector(
        cname_cache_path or cdn_asset("cname_cache.json"),
        cdn_list_path or cdn_asset("cdnlist.txt"),
        pattern_path=pattern_path,
    )
    dns_dict, ip_number = resolver.query_and_resolve_with_subnets(domain)
    print(dns_dict)
    identified_cdn = detector.identify_cdn(domain, dns_dict)
    return identified_cdn, detector.keys, ip_number
