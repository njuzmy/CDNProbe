import os
import json
import pandas as pd

dirpath="datas"

ans ={}

filenames=os.listdir(dirpath)
filenames.sort()

for filename in filenames:
    filename=os.path.join(dirpath, filename)
    with open(filename,"r") as f:
        x=json.load(f)
    ans.update(x)

print(len(ans))
with open("ans.json","w") as f:      
    json.dump(ans, f, indent=4)

websites = pd.read_csv("top-1m.csv")["domain"][0:10000].to_list()

keys=list(ans.keys())
print(set(websites)-set(keys))

sum=0
for k,v in ans.items():
    if len(v["cdn"])!=0:
        print(k,v)
        sum+=1
print(sum)