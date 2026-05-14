import argparse
import sys

if __package__ in (None, ""):
    import os

    sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from cli.utils import add_batch_arguments, normalize_domain, run_batch
from cdnprobe import DnsResolver
from cdnprobe.detect_cdn import detect
from cdnprobe.paths import artifact_path, dns_asset


DEFAULT_WITH_WWW_DIR = "detect_batch"
DEFAULT_WITHOUT_WWW_DIR = "detect_batch_wo_www"
DEFAULT_WITH_WWW_OUTPUT = "ans_www.json"
DEFAULT_WITHOUT_WWW_OUTPUT = "ans_wo_www.json"


def build_parser(default_with_www=True):
    parser = argparse.ArgumentParser(description="Run CDN detection for one domain or a domain slice.")
    return add_batch_arguments(
        parser,
        include_with_www=True,
        default_with_www=default_with_www,
        output_dir_help="Artifact subdirectory name under the project artifact root.",
        checkpoint_prefix="detect_batch",
    )


def output_defaults(with_www):
    if with_www:
        return DEFAULT_WITH_WWW_DIR, DEFAULT_WITH_WWW_OUTPUT
    return DEFAULT_WITHOUT_WWW_DIR, DEFAULT_WITHOUT_WWW_OUTPUT


def run(args):
    resolver = DnsResolver(dns_asset("prefix.txt"))
    return run_batch(
        args,
        output_defaults=lambda parsed_args: output_defaults(parsed_args.with_www),
        output_dir_factory=lambda _args: artifact_path(),
        domain_transformer=lambda domain, parsed_args: normalize_domain(
            domain, parsed_args.with_www, parsed_args.domain is not None
        ),
        probe=lambda domain, _args: _detect_payload(domain, resolver),
    )


def _detect_payload(domain, resolver):
    identified_cdn, keys, ip_number = detect(domain, resolver=resolver)
    keys["cdn"] = identified_cdn
    keys["dns"] = ip_number
    return keys


def main(default_with_www=True):
    parser = build_parser(default_with_www=default_with_www)
    run(parser.parse_args())


if __name__ == "__main__":
    main(default_with_www=True)
