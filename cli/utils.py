from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from cdnprobe.paths import domain_input, tmp_checkpoint_path, tmp_result_path

DOMAIN_VARIANTS = ("naked", "www")
DEFAULT_DOMAIN_VARIANT = "www"


def add_domain_batch_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--start", type=int, default=0, help="Inclusive start index in top-1m.csv.")
    parser.add_argument("--end", type=int, default=10000, help="Exclusive end index in top-1m.csv.")
    parser.add_argument(
        "--variant",
        choices=DOMAIN_VARIANTS,
        default=None,
        help="Domain variant to probe. Defaults to www.",
    )
    parser.add_argument(
        "--domain",
        default=None,
        help="Run for a single domain and ignore --start/--end.",
    )
    parser.add_argument(
        "--domains-file",
        default=None,
        help="CSV file used in batch mode. Defaults to assets/input/domains/top-1m.csv.",
    )


def add_output_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Result subdirectory name under tmp/results.",
    )
    parser.add_argument(
        "--output-name",
        default=None,
        help="Final JSON filename written under the output directory.",
    )
    parser.add_argument(
        "--checkpoint-prefix",
        default=None,
        help="Filename prefix for checkpoint JSON files. Defaults to the command method.",
    )


def build_domains(args: argparse.Namespace) -> list[str]:
    if args.domain is not None:
        return [args.domain]
    domains_file = getattr(args, "domains_file", None) or domain_input("top-1m.csv")
    return pd.read_csv(domains_file)["domain"][args.start:args.end].to_list()


def normalize_domain(domain: str, variant: str, explicit_domain: bool) -> str:
    if explicit_domain:
        return domain
    return f"www.{domain}" if variant == "www" else domain


def default_output_dir(method: str, variant: str) -> str:
    return f"{method}_{variant}"


def default_output_name(variant: str) -> str:
    return f"ans_{variant}.json"


def output_dirpath(args: argparse.Namespace) -> Path:
    output_dir_name = args.output_dir or default_output_dir(args.method, args.variant)
    return tmp_result_path(output_dir_name)


def checkpoint_dirpath(args: argparse.Namespace) -> Path:
    output_dir_name = args.output_dir or default_output_dir(args.method, args.variant)
    return tmp_checkpoint_path(output_dir_name)


def output_name(args: argparse.Namespace) -> str:
    return args.output_name or default_output_name(args.variant)


def checkpoint_prefix(args: argparse.Namespace) -> str:
    return args.checkpoint_prefix or args.method
