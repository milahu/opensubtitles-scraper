#! /usr/bin/env python3

# sudo python -u new-subs-archive-benchmark.py | tee new-subs-archive-benchmark.txt

import subprocess
import glob
import sys
import os
import re
import time

import natsort


# compare cold cache vs warm cache
also_benchmark_warm_cache = True
also_benchmark_warm_cache = False


"""
page size has no effect on total file size:
$ du -b opensubtitles-9180519-9223801-pagesize* | sort -n
953827328       opensubtitles-9180519-9223801-pagesize1024.db
953827328       opensubtitles-9180519-9223801-pagesize16384.db
953827328       opensubtitles-9180519-9223801-pagesize2048.db
953827328       opensubtitles-9180519-9223801-pagesize32768.db
953827328       opensubtitles-9180519-9223801-pagesize4096.db
953827328       opensubtitles-9180519-9223801-pagesize512.db
953827328       opensubtitles-9180519-9223801-pagesize65536.db
953827328       opensubtitles-9180519-9223801-pagesize8192.db
"""

sqlite_files_regex = r"^opensubtitles.org.dump.(\d+).to.(\d+).eng.pagesize-(\d+).db$"
sqlite_files = glob.glob("*.db")
sqlite_files = natsort.natsorted(sqlite_files)
sqlite_files = list(filter(
    lambda f: re.match(sqlite_files_regex, f),
    sqlite_files
))
if False:
    sqlite_files = [
        "opensubtitles-9180519-9223801-pagesize512.db",
        "opensubtitles-9180519-9223801-pagesize4096.db",
        "opensubtitles-9180519-9223801-pagesize16384.db",
        "opensubtitles-9180519-9223801-pagesize65536.db",
    ]


# worst performance
tar_files = [
    "opensubtitles-9180519-9225080.tar",
]

iso_files = [
    "opensubtitles-9180519-9223641.iso",
]

test_files = (
    sqlite_files +
    # todo:
    tar_files +
    iso_files
)
test_files = sqlite_files


# this is only needed with subprocess.run(args, shell=True)
#time_exe = subprocess.check_output(["which", "time"], encoding="utf8").strip()
#print("time_exe", time_exe)


# how much time do you have?
repeat_count = 10
repeat_count = 3

results = []


# claim:
# "set page size" - random read access is fastest with smallest page size (512 bytes). this makes sense, because with small pages, more pages fit in the cache. when many interior pages (branch pages) are cached, finding a random key is faster. the difference can be factor 3, so ... do benchmarks – 
# https://stackoverflow.com/questions/12831504/optimizing-fast-access-to-a-readonly-sqlite-database


def drop_cache_linux():
    #sudo sh -c "sync; echo 3 > /proc/sys/vm/drop_caches"
    args = [
        "sudo",
        "sh",
        "-c",
        "sync; echo 3 > /proc/sys/vm/drop_caches",
    ]
    subprocess.run(args, check=True)


def benchmark_sqlite(db_path):
    global results
    db_filename = os.path.basename(db_path)
    print()
    print("db_filename", db_filename)
    m = re.match(
        sqlite_files_regex,
        db_filename
    )
    #if not m:
    #    continue
    page_size = int(m.group(3))
    benchmark_names = [
        "read_sequential_all", # no difference
        "read_random_all", # no diff
        "read_random_some", # todo
        "count", # sequential access of interior pages
    ]
    for benchmark_name in benchmark_names:
        args = [
            sys.executable, # python exe
            "new-subs-archive-benchmark-sqlite.py",
            db_path,
            benchmark_name,
        ]
        if False:
            # use /bin/time to get memory usage
            # no difference
            args = [
                #time_exe,
                "time",
                "-v", # verbose
            ] + args

        if also_benchmark_warm_cache:
            print("cold cache:")

        sum_dt = 0

        for repeat_step in range(repeat_count):

            # drop cache
            drop_cache_linux()

            # run benchmark with cold cache
            t1 = time.time()
            subprocess.run(args, check=True)
            t2 = time.time()
            dt = t2 - t1
            sum_dt += dt
            results.append({
                "db_path": db_path,
                "benchmark_name": benchmark_name,
                "dt": dt,
                "cache": False,
            })

        avg_dt = sum_dt / repeat_count
        if repeat_count > 1:
            print(f"average time: {avg_dt:.3f}sec")

        if also_benchmark_warm_cache:
            # run benchmark with warm cache
            # random read: 3x faster
            # count: 20x faster
            # dont repeat this benchmark
            print("warm cache:")
            t1 = time.time()
            subprocess.run(args, check=True)
            t2 = time.time()
            dt = t2 - t1
            results.append({
                "db_path": db_path,
                "benchmark_name": benchmark_name,
                "dt": dt,
                "cache": True,
            })


for test_file in test_files:
    extension = test_file.split(".")[-1]

    if extension == "db":
        benchmark_sqlite(test_file)

    elif extension == "tar":
        continue
        #print(f"todo: extension={extension}")
        #raise NotImplementedError

    elif extension == "iso":
        continue
        #print(f"todo: extension={extension}")
        #raise NotImplementedError


sys.exit()

# group results by file
print()
print("results")
for db_path in sqlite_files:
    print()
    print("db_path", db_path)
    for result in results:
        if result["db_path"] != db_path:
            continue
        print("result", result)
