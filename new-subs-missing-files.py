#! /usr/bin/env python3

input_dir = "new-subs"

import os

nums = []
for filename in os.listdir(input_dir):
    try:
        num = int(filename.split(".", 1)[0])
    except ValueError:
        continue
    nums.append(num)

nums = sorted(nums)

for idx in range(0, len(nums) - 1):
    if nums[idx] + 1 == nums[idx + 1]:
        continue
    #if nums[idx + 1] == 9511453: # outlier
    #    break
    #missing_len = nums[idx + 1] - nums[idx] + 1
    #print(f"# range from {nums[idx] + 1} to {nums[idx + 1] - 1} = {missing_len} nums")
    for num in range(nums[idx] + 1, nums[idx + 1]):
        print(num)
