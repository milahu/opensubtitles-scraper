#! /usr/bin/env python3


# optimization for lookup by sub_number
# similar to the sqlite database opensubs.db
# store zip files as f"{sub_number}.zip"
# store full names separately in filenames.txt

# $ du -h opensubtitles-9331440-9379715.iso
# 932M
# $ sudo mount -o loop,ro opensubtitles-9331440-9379715.iso mnt

# glob is 10x slower than direct access:
# $ time ls -U mnt/9331440.* | head -n1
# real    0m0.160s
# $ time ls -U mnt/"9331440.cobra.kai.s05.e08.taikai.(2022).tgl.1cd.zip" | head -n1
# real    0m0.016s

# $ ls -U mnt/ >filenames.txt
# $ du -h filenames.txt
# 2.8M


import os
import shlex

# folder with zip files (full names)
input_dir = "new-subs"

# folder with zip files (short names)
output_dir = "new-subs-num"

os.makedirs(output_dir, exist_ok=True)

print(f"linking files from {input_dir} to {output_dir} ...")
for input_name in os.listdir(input_dir):
    #print(input_name)
    if not input_name.endswith(".zip"):
        continue
    sub_number = input_name.split(".", 1)[0]
    output_path = f"{output_dir}/{sub_number}.zip"
    if os.path.exists(output_path):
        continue
    # create hardlink
    input_path = f"{input_dir}/{input_name}"
    #print(f"ln {shlex.quote(input_path)} {shlex.quote(output_path)}")
    os.link(input_path, output_path)
    #break # debug
