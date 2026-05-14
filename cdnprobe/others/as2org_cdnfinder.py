import json

from cdnprobe import DnsResolver
from cdnprobe.paths import asn_asset, cdn_asset, dns_asset


ASN_DB = None
ASN_DB_PATH = None


def get_asn_db(asn_db_path=None):
    global ASN_DB, ASN_DB_PATH
    resolved_path = asn_db_path or asn_asset("20230101asb.db")
    if ASN_DB is None or ASN_DB_PATH != resolved_path:
        import pyasn

        ASN_DB = pyasn.pyasn(str(resolved_path))
        ASN_DB_PATH = resolved_path
    return ASN_DB


class As2Org:
    def __init__(self, cname_cache_path=None, cdn_list_path=None, asn_db_path=None, as_org_path=None):
        self.cdn_total = []
        self.as_list = []
        self.as_info = {}
        self.cdn_list = []
        self.asn_db_path = asn_db_path
        self.as_org_path = as_org_path or asn_asset("20230101.as-org2info.jsonl")
        self.cname_cache = json.load(open(cname_cache_path or cdn_asset("cname_cache.json"), "r"))
        with open(cdn_list_path or cdn_asset("cdnlist.txt"), "r") as file:
            for line in file.readlines():
                self.cdn_total.append(line.strip().lower())

    def getAS(self, ip):
        try:
            return int(get_asn_db(self.asn_db_path).lookup(ip)[0])
        except Exception:
            return 0

    def org(self, asn):
        import jsonlines

        with jsonlines.open(self.as_org_path, mode="r") as reader:
            for row in reader:
                if "asn" in row.keys() and row["asn"] == asn:
                    return row
        return None

    def cname(self, cname=None):
        if cname is None:
            return False, None
        for cdn, value in self.cname_cache.items():
            for cdn_cname in value["cname_substring"].split(" "):
                if cname.find(cdn_cname) != -1:
                    return True, cdn
        return False, None

    def identify_cdn(self, dns_dict):
        for cname, ip_list in dns_dict.items():
            flag, cdn = self.cname(cname)
            if flag is True:
                self.cdn_list.append(cdn)
            else:
                for ip in ip_list:
                    self.as_list.append(self.getAS(ip))
                self.as_list = list(set(self.as_list))
                for asn in self.as_list:
                    org_dict = self.org(str(asn))
                    self.as_info[asn] = org_dict
                    if org_dict is not None and "name" in org_dict.keys():
                        for cdn_name in self.cdn_total:
                            if org_dict["name"].lower().find(cdn_name) != -1:
                                self.cdn_list.append(cdn_name)
        if self.cdn_list:
            return list(set(self.cdn_list))
        return None


def detect(domain, resolver=None, cname_cache_path=None, cdn_list_path=None, asn_db_path=None, as_org_path=None):
    resolver = resolver or DnsResolver(dns_asset("prefix.txt"))
    detector = As2Org(
        cname_cache_path=cname_cache_path,
        cdn_list_path=cdn_list_path,
        asn_db_path=asn_db_path,
        as_org_path=as_org_path,
    )
    result = detector.identify_cdn(resolver.query_and_resolve_with_subnets(domain)[0])
    detector.as_info["cdn"] = result
    return detector.as_info
