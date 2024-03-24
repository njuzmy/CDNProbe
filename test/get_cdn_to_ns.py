import json
import os


ans_dirpath = "../ans"


def cdn_to_domain(filename, ans={}):
    with open(os.path.join(ans_dirpath, filename), "r") as f:
        txt = json.load(f)
    for domain, v in txt.items():
        cdns = v["cdn"]
        if len(cdns) > 1:
            print(domain)
            continue
        for cdn in cdns:
            ans.setdefault(cdn, set())
            ans[cdn].add(domain)
    return ans


def domain_to_cname(filename, ans={}):
    with open(os.path.join(ans_dirpath, filename), "r") as f:
        txt = json.load(f)
    for domain, cnames in txt.items():
        ans.setdefault(domain,set())
        ans[domain].update(cnames)
    return ans


def domain_to_ns(filename, ans={}):
    with open(os.path.join(ans_dirpath, filename), "r") as f:
        txt = json.load(f)
    for domain, nss in txt.items():
        ans.setdefault(domain, set())
        ans[domain].update(nss)
    return ans


def cdn_to_ns(cdn_to_domain_ans, domain_to_ns_ans, squeeze=True):
    ans = {}
    for cdn, domains in cdn_to_domain_ans.items():
        ans[cdn] = {}
        for domain in domains:
            ans[cdn][domain] = domain_to_ns_ans.get(domain, set())
    if squeeze:
        sans = {}
        for cdn, domains in ans.items():
            sans[cdn] = set()
            for domain in domains:
                sans[cdn].update(ans[cdn][domain])
        ans = sans
    return ans


if __name__ == "__main__":
    cdn_to_domain_ans = {}
    cdn_to_domain("ans.json", cdn_to_domain_ans)
    cdn_to_domain("ans_www.json", cdn_to_domain_ans)
    with open(os.path.join(ans_dirpath, "cdn_to_domain_ans.json"), "w") as f:
        json.dump(cdn_to_domain_ans, f, indent=4,default=list)

    domain_to_cname_ans = {}
    domain_to_cname("cname.json", domain_to_cname_ans)
    domain_to_cname("cname_www.json", domain_to_cname_ans)
    with open(os.path.join(ans_dirpath, "domain_to_cname_ans.json"), "w") as f:
        json.dump(domain_to_cname_ans, f, indent=4,default=list)

    domain_to_ns_ans = {}
    domain_to_ns("ns.json", domain_to_ns_ans)
    domain_to_ns("ns_www.json", domain_to_ns_ans)
    with open(os.path.join(ans_dirpath, "domain_to_ns_ans.json"), "w") as f:
        json.dump(domain_to_ns_ans, f, indent=4,default=list)

    cdn_to_ns_ans = cdn_to_ns(cdn_to_domain_ans, domain_to_ns_ans)

    with open(os.path.join(ans_dirpath, "cdn_to_ns_ans.json"), "w") as f:
        json.dump(cdn_to_ns_ans, f, indent=4,default=list)
