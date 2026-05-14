import argparse
import sys
from dataclasses import dataclass
from typing import Callable
import json
from pathlib import Path
from time import time

from rich.console import Console
from rich.panel import Panel
from rich.table import Table


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
from cdnprobe import DnsResolver
from cdnprobe.paths import asn_asset, cdn_asset, dns_asset, domain_input, ensure_runtime_dirs

from cdnprobe.cdnprobe import detect as detect_cdnprobe
from cdnprobe.others.as2org_cdnfinder import detect as detect_as2org
from cdnprobe.others.turbobytes_cdnfinder import DEFAULT_TURBOBYTES_BASE_URL, detect as detect_turbobytes

ProbeFactory = Callable[[argparse.Namespace], Callable[[str, argparse.Namespace], object]]
DomainTransformer = Callable[[str, argparse.Namespace], str]
ProbeRunner = Callable[[str, argparse.Namespace], object]
console = Console()

@dataclass(frozen=True)
class MethodConfig:
    default_variant: str
    probe_factory: ProbeFactory


def make_cdnprobe_probe(_args: argparse.Namespace):
    resolver = DnsResolver(_args.dns_prefix_file or dns_asset("prefix.txt"))

    def probe(domain: str, _parsed_args: argparse.Namespace):
        identified_cdn, keys, ip_number = detect_cdnprobe(
            domain,
            resolver=resolver,
            cname_cache_path=_parsed_args.cname_cache_file,
            cdn_list_path=_parsed_args.cdn_list_file,
            pattern_path=_parsed_args.http_pattern_file,
        )
        keys["cdn"] = identified_cdn
        keys["dns"] = ip_number
        return keys

    return probe


def make_as2org_probe(_args: argparse.Namespace):
    resolver = DnsResolver(_args.dns_prefix_file or dns_asset("prefix.txt"))

    def probe(domain: str, _parsed_args: argparse.Namespace):
        return detect_as2org(
            domain,
            resolver=resolver,
            cname_cache_path=_parsed_args.cname_cache_file,
            cdn_list_path=_parsed_args.cdn_list_file,
            asn_db_path=_parsed_args.asn_db_file,
            as_org_path=_parsed_args.as_org_file,
        )

    return probe


def make_turbobytes_probe(_args: argparse.Namespace):
    def probe(domain: str, parsed_args: argparse.Namespace):
        error_log_path = checkpoint_dirpath(parsed_args) / "error.log"
        return detect_turbobytes(
            domain,
            error_log_path=error_log_path,
            base_url=parsed_args.turbobytes_base_url,
        )

    return probe


METHOD_CONFIGS = {
    "cdnprobe": MethodConfig(default_variant=DEFAULT_DOMAIN_VARIANT, probe_factory=make_cdnprobe_probe),
    "as2org": MethodConfig(default_variant=DEFAULT_DOMAIN_VARIANT, probe_factory=make_as2org_probe),
    "turbobytes": MethodConfig(default_variant=DEFAULT_DOMAIN_VARIANT, probe_factory=make_turbobytes_probe),
}


def format_duration(seconds: float) -> str:
    seconds = max(0, int(seconds))
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}h {minutes}m {secs}s"
    if minutes:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def format_percent(current: int, total: int) -> str:
    return f"{current / total * 100:.1f}%" if total else "0.0%"


def resolved_resource_paths(args: argparse.Namespace) -> dict[str, Path]:
    return {
        "Domains CSV": Path(args.domains_file or domain_input("top-1m.csv")),
        "DNS prefixes": Path(args.dns_prefix_file or dns_asset("prefix.txt")),
        "CNAME cache": Path(args.cname_cache_file or cdn_asset("cname_cache.json")),
        "CDN list": Path(args.cdn_list_file or cdn_asset("cdnlist.txt")),
        "HTTP patterns": Path(args.http_pattern_file or cdn_asset("pattern.json")),
        "ASN DB": Path(args.asn_db_file or asn_asset("20230101asb.db")),
        "AS org map": Path(args.as_org_file or asn_asset("20230101.as-org2info.jsonl")),
    }


def resources_for_method(args: argparse.Namespace) -> dict[str, Path]:
    resources = resolved_resource_paths(args)
    if args.method == "cdnprobe":
        return {
            "Domains CSV": resources["Domains CSV"],
            "DNS prefixes": resources["DNS prefixes"],
            "CNAME cache": resources["CNAME cache"],
            "CDN list": resources["CDN list"],
            "HTTP patterns": resources["HTTP patterns"],
        }
    if args.method == "as2org":
        return {
            "Domains CSV": resources["Domains CSV"],
            "DNS prefixes": resources["DNS prefixes"],
            "CNAME cache": resources["CNAME cache"],
            "CDN list": resources["CDN list"],
            "ASN DB": resources["ASN DB"],
            "AS org map": resources["AS org map"],
        }
    return {
        "Domains CSV": resources["Domains CSV"],
        "TurboBytes URL": args.turbobytes_base_url,
    }


def summarize_result(result: object) -> str:
    if not isinstance(result, dict):
        return type(result).__name__

    summary_parts: list[str] = []
    for key in ("cdn", "dns", "asn", "org", "organization"):
        if key not in result:
            continue
        value = result[key]
        if isinstance(value, (list, tuple, set)):
            value_text = ", ".join(str(item) for item in value) if value else "none"
        elif isinstance(value, dict):
            value_text = f"{len(value)} item(s)"
        else:
            value_text = str(value)
        summary_parts.append(f"{key}={value_text}")

    if summary_parts:
        return "; ".join(summary_parts)

    return f"{len(result)} key(s): {', '.join(map(str, list(result)[:5]))}"


def print_run_header(
    args: argparse.Namespace,
    *,
    total_domains: int,
    output_directory: Path,
    checkpoint_directory: Path,
    final_output_name: str,
    checkpoint_name_prefix: str,
) -> None:
    table = Table.grid(padding=(0, 2))
    table.add_column(style="bold cyan", no_wrap=True)
    table.add_column()
    table.add_row("Method", args.method)
    table.add_row("Mode", "single domain" if args.domain is not None else "batch slice")
    if args.domain is None:
        table.add_row("Input slice", f"top-1m.csv[{args.start}:{args.end}]")
    table.add_row("Domains", str(total_domains))
    table.add_row("Domain variant", args.variant)
    table.add_row("Output dir", str(output_directory))
    table.add_row("Final file", final_output_name)
    table.add_row("Checkpoint dir", str(checkpoint_directory))
    table.add_row("Checkpoint prefix", checkpoint_name_prefix)
    for label, path in resources_for_method(args).items():
        if args.domain is not None and label == "Domains CSV":
            continue
        table.add_row(label, str(path))
    console.print(Panel(table, title="CDNProbe run", border_style="cyan"))


def print_domain_start(index: int, total: int, domain: str) -> None:
    console.rule(f"[bold]Domain {index}/{total} ({format_percent(index, total)})")
    console.print(f"[bold cyan]Target:[/bold cyan] {domain}")


def print_domain_success(
    *,
    elapsed: float,
    total_elapsed: float,
    eta: float,
    checkpoint_path: Path,
    result: object,
) -> None:
    table = Table.grid(padding=(0, 2))
    table.add_column(style="bold green", no_wrap=True)
    table.add_column()
    table.add_row("Status", "done")
    table.add_row("Result", summarize_result(result))
    table.add_row("Domain time", format_duration(elapsed))
    table.add_row("Elapsed", format_duration(total_elapsed))
    table.add_row("ETA", format_duration(eta))
    table.add_row("Checkpoint", str(checkpoint_path))
    console.print(table)


def print_domain_error(domain: str, exc: Exception, elapsed: float) -> None:
    console.print(
        Panel(
            f"[bold red]Target:[/bold red] {domain}\n"
            f"[bold red]Error:[/bold red] {type(exc).__name__}: {exc}\n"
            f"[bold red]Domain time:[/bold red] {format_duration(elapsed)}",
            title="Probe failed",
            border_style="red",
        )
    )


def print_run_footer(
    *,
    total_domains: int,
    elapsed: float,
    final_path: Path,
) -> None:
    table = Table.grid(padding=(0, 2))
    table.add_column(style="bold cyan", no_wrap=True)
    table.add_column()
    table.add_row("Completed", f"{total_domains} domain(s)")
    table.add_row("Total time", format_duration(elapsed))
    table.add_row("Average", format_duration(elapsed / total_domains) if total_domains else "0s")
    table.add_row("Output", str(final_path))
    console.print(Panel(table, title="CDNProbe complete", border_style="green"))


def build_parser():
    parser = argparse.ArgumentParser(description="Run CDNProbe workflows for one domain or a domain slice.")
    parser.add_argument(
        "--method",
        choices=sorted(METHOD_CONFIGS),
        required=True,
        help="Workflow to run.",
    )

    add_domain_batch_arguments(parser)
    add_output_arguments(parser)
    parser.add_argument(
        "--dns-prefix-file",
        default=None,
        help="DNS ECS prefix file. Defaults to assets/static/dns/prefix.txt.",
    )
    parser.add_argument(
        "--cname-cache-file",
        default=None,
        help="CNAME cache JSON file. Defaults to assets/static/cdn/cname_cache.json.",
    )
    parser.add_argument(
        "--cdn-list-file",
        default=None,
        help="CDN name list file. Defaults to assets/static/cdn/cdnlist.txt.",
    )
    parser.add_argument(
        "--http-pattern-file",
        default=None,
        help="HTTP header pattern JSON file. Defaults to assets/static/cdn/pattern.json.",
    )
    parser.add_argument(
        "--asn-db-file",
        default=None,
        help="pyasn database file. Defaults to assets/static/asn/20230101asb.db.",
    )
    parser.add_argument(
        "--as-org-file",
        default=None,
        help="ASN organization JSONL file. Defaults to assets/static/asn/20230101.as-org2info.jsonl.",
    )
    parser.add_argument(
        "--turbobytes-base-url",
        default=DEFAULT_TURBOBYTES_BASE_URL,
        help=f"TurboBytes service base URL. Defaults to {DEFAULT_TURBOBYTES_BASE_URL}.",
    )
    return parser


def run_batch(
    args: argparse.Namespace,
    *,
    probe: ProbeRunner,
    domain_transformer: DomainTransformer | None = None,
) -> dict[str, object]:
    ensure_runtime_dirs()

    base_dirpath = output_dirpath(args)
    base_dirpath.mkdir(parents=True, exist_ok=True)
    checkpoint_dir = checkpoint_dirpath(args)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    final_output_name = output_name(args)
    checkpoint_name_prefix = checkpoint_prefix(args)

    domains = build_domains(args)
    result_dict: dict[str, object] = {}
    prev_checkpoint: Path | None = None

    print_run_header(
        args,
        total_domains=len(domains),
        output_directory=base_dirpath,
        checkpoint_directory=checkpoint_dir,
        final_output_name=final_output_name,
        checkpoint_name_prefix=checkpoint_name_prefix,
    )

    stime = time()
    for index, raw_domain in enumerate(domains, start=1):
        domain = domain_transformer(raw_domain, args) if domain_transformer else raw_domain
        print_domain_start(index, len(domains), domain)

        domain_stime = time()
        try:
            result = probe(domain, args)
        except Exception as exc:
            print_domain_error(domain, exc, time() - domain_stime)
            raise

        result_dict[domain] = result

        checkpoint_path = checkpoint_dir / f"{checkpoint_name_prefix}_{time()}.json"
        with checkpoint_path.open("w") as f:
            json.dump(result_dict, f, indent=4)
        if prev_checkpoint is not None and prev_checkpoint.exists():
            prev_checkpoint.unlink()
        prev_checkpoint = checkpoint_path

        total_elapsed = time() - stime
        avg_elapsed = total_elapsed / index
        eta = avg_elapsed * (len(domains) - index)
        print_domain_success(
            elapsed=time() - domain_stime,
            total_elapsed=total_elapsed,
            eta=eta,
            checkpoint_path=checkpoint_path,
            result=result,
        )

    final_path = base_dirpath / final_output_name
    with final_path.open("w") as f:
        json.dump(result_dict, f, indent=4)
    print_run_footer(total_domains=len(domains), elapsed=time() - stime, final_path=final_path)
    return result_dict


def main():
    parser = build_parser()
    args = parser.parse_args()
    config = METHOD_CONFIGS[args.method]

    if args.variant is None:
        args.variant = config.default_variant

    return run_batch(
        args,
        probe=config.probe_factory(args),
        domain_transformer=lambda domain, parsed_args: normalize_domain(
            domain, parsed_args.variant, parsed_args.domain is not None
        ),
    )


if __name__ == "__main__":
    main()
