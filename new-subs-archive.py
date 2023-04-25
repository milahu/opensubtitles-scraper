#! /usr/bin/env python3

import subprocess
import os
import glob

import natsort

max_size = 1000 * 1000 * 1000 # 1 GB

size_tolerance = 0.05 # reserve 5% for tar headers

continue_from = 1
#continue_from = 9275856 + 1
continue_from = 9331439 + 1

def pack_files(sum_files):
    prefix_len = len("new-subs/")
    first_file = sum_files[0][prefix_len:]
    last_file = sum_files[-1][prefix_len:]
    print(f"first_file {first_file}")
    print(f"last_file {last_file}")
    first_num = int(first_file.split(".")[0])
    last_num = int(last_file.split(".")[0])
    archive_path = f"opensubtitles-{first_num}-{last_num}.tar"
    print(f"packing {len(sum_files)} files to {archive_path}")
    sum_files_file = "new-subs-archive.py-sum_files.txt"
    with open(sum_files_file, "w") as f:
        f.write("\n".join(sum_files) + "\n")
    args = [
        "tar",
        # all these options are required to create reproducible archives
        # https://reproducible-builds.org/docs/archives/
        # TODO create reproducible archives with python tarfile
        # so this also works on windows
        "--format=gnu",
        "--sort=name", # sort filenames, independent of locale. tar v1.28
        "--mtime=0",
        "--owner=0",
        "--group=0",
        "--numeric-owner",
        "-c",
        "-f", archive_path,
        "-T", sum_files_file,
    ]
    subprocess.run(
        args,
        check=True,
    )


sum_size = 0
sum_files = []

max_size_tolerant = max_size * (1 - size_tolerance)

for zip_file in natsort.natsorted(glob.glob(f"new-subs/*.zip")):
    prefix_len = len("new-subs/")
    num = int(zip_file[prefix_len:].split(".")[0])
    if num < continue_from:
        continue
    size = os.path.getsize(zip_file)
    #print(size, zip_file)
    if size == 0:
        continue
    sum_size += size
    if sum_size < max_size_tolerant:
        sum_files.append(zip_file)
    else:
        sum_size -= size
        print(f"packing at sum_size {sum_size}")
        pack_files(sum_files)
        sum_size = size
        sum_files = [zip_file]
        print()

pack_files(sum_files)
