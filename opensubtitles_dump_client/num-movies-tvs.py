#! /usr/bin/env python3
# count both MovieKind: movie and tv
import json
with open("index-grouped/index.txt.grouped.eng") as f:
    o = json.load(f)
print(len(o.keys()))
# 301457 = 301_457
