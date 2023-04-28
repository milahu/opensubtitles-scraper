#!/usr/bin/env python3


src_db_path = "opensubtitles.org.Actually.Open.Edition.2022.07.25/opensubs.db"
dst_db_dir = "opensubs-langs"
lang = "eng"

dst_db_path = f"{dst_db_dir}/{lang}.db"


import sqlite3
import os
import re


assert os.path.exists(dst_db_path) == False, f"error: output file exists: {dst_db_path}"

print(f"creating database {dst_db_path} ...")

src_con = sqlite3.connect(src_db_path)

os.makedirs(os.path.dirname(dst_db_path), exist_ok=True)
dst_con = sqlite3.connect(dst_db_path)

dst_con.execute(
    "CREATE TABLE subz (\n"
    "  num INTEGER PRIMARY KEY,\n"
    "  name TEXT,\n"
    "  file BLOB\n"
    ")\n"
)

dst_cur = dst_con.cursor()

insert_query = "INSERT INTO subz (num, name, file) VALUES (?, ?, ?)"

for row in src_con.execute(f"SELECT * FROM subz WHERE name LIKE '%.{lang}.%'"):
    # this can return false positive results
    # where lang is part of the movie name
    # so we still have to filter by lang
    name_parts = row[1].split(".")
    if name_parts[-4] != lang:
        continue
    dst_cur.execute(insert_query, row)

src_con.close()

dst_con.commit()
dst_con.close()

# make it read-only
os.chmod(dst_db_path, 0o444)

print(f"creating database {dst_db_path} done")
