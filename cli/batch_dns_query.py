import argparse
import json
import signal
import sys
from pathlib import Path
from time import time

if __package__ in (None, ""):
    import os

    sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from cli.utils import (
    DEFAULT_DOMAIN_VARIANT,
    add_domain_batch_arguments,
    add_output_arguments,
    build_domains,
    checkpoint_dirpath,
    checkpoint_prefix,
    normalize_domain,
    output_dirpath,
    output_name,
)
from cdnprobe.paths import ensure_runtime_dirs
from cdnprobe.utils import query_and_resolve


DEFAULT_QTYPE = "CNAME"


def default_output_dir(qtype: str, variant: str) -> str:
    name = qtype.lower()
    return f"{name}_{variant}"


def default_output_name(qtype: str, variant: str) -> str:
    name = qtype.lower()
    return f"{name}_{variant}.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Batch query DNS records for a domain slice or one domain.")
    add_domain_batch_arguments(parser)
    add_output_arguments(parser)
    parser.add_argument(
        "--qtype",
        choices=("CNAME", "NS"),
        default=DEFAULT_QTYPE,
        help=f"DNS record type to query. Defaults to {DEFAULT_QTYPE}.",
    )
    parser.add_argument(
        "--dns-server",
        default="223.5.5.5",
        help="DNS server used for UDP queries.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="Per-domain timeout in seconds.",
    )
    return parser


def query_with_timeout(domain: str, qtype: str, dns_server: str, timeout: int) -> list[str]:
    def timeout_handler(_signum, _frame):
        raise TimeoutError

    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout)
    try:
        return query_and_resolve(domain, qtype, qtype == "CNAME", dns_server)
    except Exception:
        return []
    finally:
        signal.alarm(0)


def apply_dns_defaults(args: argparse.Namespace) -> None:
    if args.variant is None:
        args.variant = DEFAULT_DOMAIN_VARIANT
    args.method = args.qtype.lower()
    if args.output_dir is None:
        args.output_dir = default_output_dir(args.qtype, args.variant)
    if args.output_name is None:
        args.output_name = default_output_name(args.qtype, args.variant)
    if args.checkpoint_prefix is None:
        args.checkpoint_prefix = args.qtype.lower()


def main() -> dict[str, list[str]]:
    args = build_parser().parse_args()
    apply_dns_defaults(args)
    ensure_runtime_dirs()

    base_dirpath = output_dirpath(args)
    base_dirpath.mkdir(parents=True, exist_ok=True)
    checkpoint_dir = checkpoint_dirpath(args)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    final_output_name = output_name(args)
    checkpoint_name_prefix = checkpoint_prefix(args)

    raw_domains = build_domains(args)
    domains = [normalize_domain(domain, args.variant, args.domain is not None) for domain in raw_domains]

    result_dict: dict[str, list[str]] = {}
    prev_checkpoint: Path | None = None
    stime = time()

    for index, domain in enumerate(domains, start=1):
        print("\n" * 2)
        print(f"{index}/{len(domains)}")
        print(domain)

        result = query_with_timeout(domain, args.qtype, args.dns_server, args.timeout)

        print(result)
        result_dict[domain] = result
        checkpoint_path = checkpoint_dir / f"{checkpoint_name_prefix}_{time()}.json"
        with checkpoint_path.open("w") as f:
            json.dump(result_dict, f, indent=4)
        if prev_checkpoint is not None and prev_checkpoint.exists():
            prev_checkpoint.unlink()
        prev_checkpoint = checkpoint_path

    final_path = base_dirpath / final_output_name
    with final_path.open("w") as f:
        json.dump(result_dict, f, indent=4)
    print(final_path)
    print(time() - stime)
    return result_dict


if __name__ == "__main__":
    main()
