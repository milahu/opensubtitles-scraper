#! /usr/bin/env python3

# generate 404.txt and dcma.txt

# 404 = subtitle was deleted by moderators
# because of spam or bad quality or duplication

# dcma = subtitle was deleted after DCMA takedown request
# by copyright trolls

import os

new_subs_dir = "new-subs"

output_404_path = "new-subs-404.txt"
output_dcma_path = "new-subs-dcma.txt"

assert os.path.exists(output_404_path) == False, f"error: output file exists: {output_404_path}"
assert os.path.exists(output_dcma_path) == False, f"error: output file exists: {output_dcma_path}"

nums_404 = []
nums_dcma = []

for filename in os.listdir(new_subs_dir):
    if filename.endswith(".not-found"):
        num = int(filename.split(".")[0])
        nums_404.append(num)
        continue
    if filename.endswith(".dcma"):
        num = int(filename.split(".")[0])
        nums_dcma.append(num)
        continue

nums_404 = sorted(nums_404)
nums_dcma = sorted(nums_dcma)

with open(output_404_path, "w") as f:
    f.write("".join(map(lambda num: f"{num}\n", nums_404)))

with open(output_dcma_path, "w") as f:
    f.write("".join(map(lambda num: f"{num}\n", nums_dcma)))

print("done output files:")
print(output_404_path)
print(output_dcma_path)
