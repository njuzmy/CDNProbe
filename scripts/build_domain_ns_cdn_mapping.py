import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cdnprobe.paths import artifact_path


def cdn_to_domain(filename, ans=None):
    mapping = {} if ans is None else ans
    with open(artifact_path(filename), "r") as f:
        txt = json.load(f)
    for domain, value in txt.items():
        cdns = value["cdn"]
        if len(cdns) > 1:
            print(domain)
            continue
        for cdn in cdns:
            mapping.setdefault(cdn, set())
            mapping[cdn].add(domain)
    return mapping


def domain_to_cname(filename, ans=None):
    mapping = {} if ans is None else ans
    with open(artifact_path(filename), "r") as f:
        txt = json.load(f)
    for domain, cnames in txt.items():
        mapping.setdefault(domain, set())
        mapping[domain].update(cnames)
    return mapping


def domain_to_ns(filename, ans=None):
    mapping = {} if ans is None else ans
    with open(artifact_path(filename), "r") as f:
        txt = json.load(f)
    for domain, nss in txt.items():
        mapping.setdefault(domain, set())
        mapping[domain].update(nss)
    return mapping


def cdn_to_ns(map_cdn_to_domain, map_domain_to_ns, squeeze=True):
    mapping = {}
    for cdn, domains in map_cdn_to_domain.items():
        mapping[cdn] = {}
        for domain in domains:
            mapping[cdn][domain] = map_domain_to_ns.get(domain, set())
    if squeeze:
        squeezed_map = {}
        for cdn, domains in mapping.items():
            squeezed_map[cdn] = set()
            for domain in domains:
                squeezed_map[cdn].update(mapping[cdn][domain])
        mapping = squeezed_map
    return mapping


def main():
    map_cdn_to_domain = {}
    for filename in ("ans_20231110_naked.json", "ans_20231110_www.json"):
        if artifact_path(filename).exists():
            cdn_to_domain(filename, map_cdn_to_domain)
    with open(artifact_path("map_cdn_to_domain.json"), "w") as f:
        json.dump(map_cdn_to_domain, f, indent=4, default=list)

    map_domain_to_cname = {}
    for filename in ("cname_naked.json", "cname_www.json"):
        if artifact_path(filename).exists():
            domain_to_cname(filename, map_domain_to_cname)
    with open(artifact_path("map_domain_to_cname.json"), "w") as f:
        json.dump(map_domain_to_cname, f, indent=4, default=list)

    map_domain_to_ns = {}
    for filename in ("ns_naked.json", "ns_www.json"):
        if artifact_path(filename).exists():
            domain_to_ns(filename, map_domain_to_ns)
    with open(artifact_path("map_domain_to_ns.json"), "w") as f:
        json.dump(map_domain_to_ns, f, indent=4, default=list)

    with open(artifact_path("map_cdn_to_ns.json"), "w") as f:
        json.dump(cdn_to_ns(map_cdn_to_domain, map_domain_to_ns), f, indent=4, default=list)


if __name__ == "__main__":
    main()
