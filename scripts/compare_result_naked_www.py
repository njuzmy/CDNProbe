import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cdnprobe.paths import artifact_path


filename_patterns = {
    "naked": "ans_{data}_naked.json",
    "www": "ans_{data}_www.json",
}

variant = "www"
filename_pattern = filename_patterns[variant]


def read_ans(path):
    with open(path, "r") as f:
        return json.load(f)


def stat(ans):
    result = {"single_cdn": {}, "multiple_cdn": {}}
    for domain, data in ans.items():
        if len(data["cdn"]) == 1:
            result["single_cdn"][domain] = data["cdn"]
        elif len(data["cdn"]) > 1:
            result["multiple_cdn"][domain] = data["cdn"]
    return result


def compare_stat(a_stat, b_stat):
    a_single = set(a_stat["single_cdn"].keys())
    a_multi = set(a_stat["multiple_cdn"].keys())
    b_single = set(b_stat["single_cdn"].keys())
    b_multi = set(b_stat["multiple_cdn"].keys())

    print("A single cdn:", len(a_single))
    print("B single cdn:", len(b_single))
    print("A multiple cdn:", len(a_multi))
    print("B multiple cdn:", len(b_multi))
    print("A single cdn - B single cdn:", len(a_single - b_single))
    print("B single cdn - A single cdn:", len(b_single - a_single))
    print("A multiple cdn - B multiple cdn:", len(a_multi - b_multi))
    print("B multiple cdn - A multiple cdn:", len(b_multi - a_multi))


def main():
    a = "20231110"
    b = "20250318"
    a_ans = read_ans(artifact_path(filename_pattern.format(data=a)))
    b_ans = read_ans(artifact_path(filename_pattern.format(data=b)))
    print("A:", a)
    print("B:", b)
    compare_stat(stat(a_ans), stat(b_ans))


if __name__ == "__main__":
    main()
