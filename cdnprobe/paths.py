from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent

ASSETS_DIR = REPO_ROOT / "assets"
ASSETS_STATIC_DIR = ASSETS_DIR / "static"
ASSETS_INPUT_DIR = ASSETS_DIR / "input"
ASSETS_OUTPUT_DIR = ASSETS_DIR / "output"

ARTIFACTS_DIR = REPO_ROOT / "artifacts"
TMP_DIR = REPO_ROOT / "tmp"
TMP_RESULTS_DIR = TMP_DIR / "results"
TMP_CHECKPOINTS_DIR = TMP_DIR / "checkpoints"

THIRD_PARTY_DIR = REPO_ROOT / "3rdparty"
ZDNS_DIR = THIRD_PARTY_DIR / "zdns"
ZDNS_BIN = ZDNS_DIR / "zdns"


def ensure_runtime_dirs() -> None:
    TMP_DIR.mkdir(exist_ok=True)
    TMP_RESULTS_DIR.mkdir(exist_ok=True)
    TMP_CHECKPOINTS_DIR.mkdir(exist_ok=True)
    ARTIFACTS_DIR.mkdir(exist_ok=True)
    ASSETS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def asset_static(*parts: str) -> Path:
    return ASSETS_STATIC_DIR.joinpath(*parts)


def asset_input(*parts: str) -> Path:
    return ASSETS_INPUT_DIR.joinpath(*parts)


def asset_output(*parts: str) -> Path:
    return ASSETS_OUTPUT_DIR.joinpath(*parts)


def artifact_path(*parts: str) -> Path:
    return ARTIFACTS_DIR.joinpath(*parts)


def tmp_result_path(*parts: str) -> Path:
    return TMP_RESULTS_DIR.joinpath(*parts)


def tmp_checkpoint_path(*parts: str) -> Path:
    return TMP_CHECKPOINTS_DIR.joinpath(*parts)


def cdn_asset(filename: str) -> Path:
    return asset_static("cdn", filename)


def dns_asset(filename: str) -> Path:
    return asset_static("dns", filename)


def asn_asset(filename: str) -> Path:
    return asset_static("asn", filename)


def domain_input(*parts: str) -> Path:
    return asset_input("domains", *parts)


def tranco_input(*parts: str) -> Path:
    return asset_input("tranco", *parts)
