import json
import os
filename_pattern_www = "ans_{data}_www.json"
filename_pattern_wo = "ans_{data}_wo.json"

with_www = True

filename_pattern = filename_pattern_www if with_www else filename_pattern_wo

def FILEPATH_ANS(filename):
    return os.path.join("../ans", filename)


def read_ans(path):
    with open(path, 'r') as f:
        ans = json.load(f)
    return ans

def stat(ans):
    stat = {'single_cdn': {}, 'multiple_cdn': {}}
    for domain, data in ans.items():
        if len(data['cdn']) == 1:
            stat['single_cdn'][domain] = data['cdn']
        elif len(data['cdn']) > 1:
            stat['multiple_cdn'][domain] = data['cdn']

    return stat

def compare_stat(A_stat, B_stat):
    A_single_cdn = set(A_stat['single_cdn'].keys())
    A_multiple_cdn = set(A_stat['multiple_cdn'].keys())

    B_single_cdn = set(B_stat['single_cdn'].keys())
    B_multiple_cdn = set(B_stat['multiple_cdn'].keys())

    print("A single cdn:", len(A_single_cdn))
    print("B single cdn:", len(B_single_cdn))
    print("A multiple cdn:", len(A_multiple_cdn))
    print("B multiple cdn:", len(B_multiple_cdn))

    print("A single cdn - B single cdn:", len(A_single_cdn - B_single_cdn))
    print("B single cdn - A single cdn:", len(B_single_cdn - A_single_cdn))

    print("A multiple cdn - B multiple cdn:", len(A_multiple_cdn - B_multiple_cdn))
    print("B multiple cdn - A multiple cdn:", len(B_multiple_cdn - A_multiple_cdn))

    print("A single cdn - B multiple cdn:", len(A_single_cdn - B_multiple_cdn))
    print("B single cdn - A multiple cdn:", len(B_single_cdn - A_multiple_cdn))

    print("A multiple cdn - B single cdn:", len(A_multiple_cdn - B_single_cdn))
    print("B multiple cdn - A single cdn:", len(B_multiple_cdn - A_single_cdn))

    print("B multiple cdn - A single cdn:", len(B_multiple_cdn - A_single_cdn))

    now_B_multiple_from_A_single = A_single_cdn.intersection(B_multiple_cdn)
    now_B_multiple_from_A_multiple = A_multiple_cdn.intersection(B_multiple_cdn)
    now_B_multiple_new = B_multiple_cdn.difference(A_single_cdn.union(A_multiple_cdn))
    print("now_B_multiple_from_A_single:", len(now_B_multiple_from_A_single))
    print("now_B_multiple_from_A_multiple:", len(now_B_multiple_from_A_multiple))
    print("now_B_multiple_new:", len(now_B_multiple_new))
    print(now_B_multiple_from_A_single)
    print(now_B_multiple_new)



A = "20231110"
B = "20250318"

A_filename = filename_pattern.format(data=A)
B_filename = filename_pattern.format(data=B)

A_ans = read_ans(FILEPATH_ANS(A_filename))
B_ans = read_ans(FILEPATH_ANS(B_filename))

A_stat = stat(A_ans)

B_stat = stat(B_ans)

print("A:", A)
print("B:", B)
compare_stat(A_stat, B_stat)