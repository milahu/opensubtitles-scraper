#! /usr/bin/env python3

import sqlite3
import sys
import os
import re
import random
import time

db_path = sys.argv[1]
#sql_query = sys.argv[2]
benchmark_name = sys.argv[2]

# open in read-only mode
db_uri = "file://" + os.path.abspath(db_path) + "?mode=ro"

con = sqlite3.connect(db_uri, uri=True)
cur = con.cursor()

#cur.executescript(f"PRAGMA page_size = {sqlite_page_size}; VACUUM;")
cur.execute("PRAGMA journal_mode=OFF")
cur.execute("PRAGMA synchronous=OFF")
cur.execute("PRAGMA locking_mode=EXCLUSIVE")

# opensubtitles-9180519-9223801.db
# opensubtitles-9180519-9223801-pagesize4096.db
db_filename = os.path.basename(db_path)
sqlite_files_regex = r"^opensubtitles.org.dump.(\d+).to.(\d+).eng.pagesize-(\d+).db$"
m = re.match(sqlite_files_regex, db_filename)
first_num = int(m.group(1))
last_num = int(m.group(2))
# opensubtitles_9180519_9223801
table_name = "zipfiles"

if benchmark_name == "read_sequential_all":
    sql_query = f"SELECT * FROM {table_name}"
    done_content_size = 0
    t1 = time.time()
    for num, name, content in cur.execute(sql_query):
        done_content_size += len(content)
    t2 = time.time()
    print(f"done sequential reading {done_content_size/1000/1000:.0f}MB in {t2-t1:.3f}sec")

elif benchmark_name == "read_random_all":
    nums = list(range(first_num, last_num))
    random.shuffle(nums)
    nums = nums[:]
    done_content_size = 0
    t1 = time.time()
    for num in nums:
        sql_query = f"SELECT * FROM {table_name} WHERE num = {num}"
        result = cur.execute(sql_query).fetchone()
        if not result:
            continue
        num, name, content = result
        done_content_size += len(content)
    t2 = time.time()
    print(f"done random reading {done_content_size/1000/1000:.0f}MB from all rows in {t2-t1:.3f}sec")

elif benchmark_name == "read_random_some":
    nums_count = 1000
    nums = list(range(first_num, last_num))
    random.shuffle(nums)
    nums = nums[0:nums_count]
    done_content_size = 0
    t1 = time.time()
    for num in nums:
        sql_query = f"SELECT * FROM {table_name} WHERE num = {num}"
        result = cur.execute(sql_query).fetchone()
        if not result:
            continue
        num, name, content = result
        done_content_size += len(content)
    t2 = time.time()
    print(f"done random reading {done_content_size/1000/1000:.0f}MB from {nums_count} rows in {t2-t1:.3f}sec")

elif benchmark_name == "count":
    sql_query = f"SELECT count() FROM {table_name}"
    t1 = time.time()
    count, = cur.execute(sql_query).fetchone()
    t2 = time.time()
    print(f"done counting {count} rows in {t2-t1:.3f}sec")

else:
    raise Exception("unknown benchmark_name")
