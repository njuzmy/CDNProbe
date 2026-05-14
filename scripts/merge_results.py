import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cdnprobe.paths import artifact_path, asset_output, tmp_checkpoint_path
from cli.utils import DEFAULT_DOMAIN_VARIANT, DOMAIN_VARIANTS


DEFAULT_DOMAIN_LIST = asset_output("multicdn.csv")


def default_input_dir(variant: str) -> Path:
    return tmp_checkpoint_path(f"cdnprobe_{variant}")


def default_output(variant: str) -> Path:
    return artifact_path(f"ans_{variant}.json")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Merge CDNProbe JSON checkpoints into one artifact.")
    parser.add_argument(
        "--variant",
        choices=DOMAIN_VARIANTS,
        default=DEFAULT_DOMAIN_VARIANT,
        help=f"Domain variant to merge. Defaults to {DEFAULT_DOMAIN_VARIANT}.",
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=None,
        help="Directory containing JSON checkpoint files. Defaults to tmp/checkpoints/cdnprobe_{variant}.",
    )
    parser.add_argument(
        "--domain-list",
        type=Path,
        default=DEFAULT_DOMAIN_LIST,
        help=f"Optional CSV used to report missing domains. Defaults to {DEFAULT_DOMAIN_LIST}.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Merged JSON output path. Defaults to artifacts/ans_{variant}.json.",
    )
    return parser


def read_json_results(input_dir: Path) -> dict:
    ans = {}
    filenames = sorted(input_dir.glob("*.json"))

    for filename in filenames:
        with filename.open("r") as f:
            ans.update(json.load(f))

    return ans


def main():
    args = build_parser().parse_args()
    args.input_dir = args.input_dir or default_input_dir(args.variant)
    args.output = args.output or default_output(args.variant)
    ans = read_json_results(args.input_dir)
    print(len(ans))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w") as f:
        json.dump(ans, f, indent=4)

    if args.domain_list.exists():
        websites = pd.read_csv(args.domain_list)["domain"].to_list()
        print(set(websites) - set(ans.keys()))

    count = 0
    for key, value in ans.items():
        if len(value["cdn"]) != 0:
            print(key, value)
            count += 1
    print(count)


if __name__ == "__main__":
    main()
