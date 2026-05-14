# CDNProbe

CDNProbe is a Python toolkit for DNS-based CDN detection, batch probing, and
supporting analysis workflows.

## Repository layout

- `cdnprobe/`: importable package code
- `cli/`: direct-run entrypoints for operational workflows
- `scripts/`: data collection and analysis helpers
- `tests/`: real automated tests only
- `assets/`: static assets and input datasets
- `tmp/results/`: default transient outputs
- `tmp/checkpoints/`: resumability/debug files from in-progress CLI runs
- `artifacts/`: curated outputs intended to be kept
- `3rdparty/zdns/`: vendored `zdns` source and binary

## Installation
Recommand to use a virtual environment. Then, from the repository root:
```sh
conda create -n cdnprobe python=3.10
conda activate cdnprobe
```


```sh
python -m pip install -e .
```

## Running

Batch CDN detection:

```sh
python cli/batch_probe.py --method cdnprobe
```

Run a specific slice from `top-1m.csv`:

```sh
python cli/batch_probe.py --method cdnprobe --start 100 --end 200
```

Run the naked-domain variant:

```sh
python cli/batch_probe.py --method cdnprobe --variant naked
```

Single-domain detection:

```sh
python cli/batch_probe.py --method cdnprobe --domain www.example.com
```

Single-domain detection with custom output location:

```sh
python cli/batch_probe.py --method cdnprobe --domain microsoft.com --output-dir debug_run --output-name microsoft.json
```

Batch outputs are written to `tmp/results/{method}_www/ans_www.json` by default,
or `tmp/results/{method}_naked/ans_naked.json` with `--variant naked`.
In-progress checkpoints are written under the matching `tmp/checkpoints/`
subdirectory.

### Other methods

ASN/organization batch detection:

```sh
python cli/batch_probe.py --method as2org
```

ASN/organization batch detection for naked domains:

```sh
python cli/batch_probe.py --method as2org --variant naked
```

TurboBytes batch probing:

```sh
python cli/batch_probe.py --method turbobytes
```

TurboBytes single-domain probing:

```sh
python cli/batch_probe.py --method turbobytes --domain example.com
```

### DNS Record Collection
Batch DNS record collection:

```sh
python cli/batch_dns_query.py --qtype CNAME
python cli/batch_dns_query.py --qtype NS
```

DNS collection accepts the same domain selection arguments as batch probing:
`--start`, `--end`, `--variant`, `--domain`, and `--domains-file`. CNAME
results default to `tmp/results/cname_www/cname_www.json`; NS results default to
`tmp/results/ns_www/ns_www.json`. In-progress checkpoints go to
`tmp/checkpoints/cname_www/` or `tmp/checkpoints/ns_www/`.
