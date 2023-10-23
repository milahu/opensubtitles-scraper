#!/usr/bin/env python3

import sys
import os
import re
import sqlite3

if len(sys.argv) != 3:
  print("usage:")
  print("  python3 opensubs-db-split-by-lang.py opensubs.db opensubs-by-lang")
  print("  (this takes some hours)")
  sys.exit(1)

src_db_path = sys.argv[1]
dst_db_dir = sys.argv[2]

assert os.path.exists(src_db_path) == True, f"error: missing input file: {src_db_path}"

assert os.path.exists(dst_db_dir) == False, f"error: output dir exists: {dst_db_dir}"

src_con = sqlite3.connect(src_db_path)

os.makedirs(dst_db_dir, exist_ok=True)

class Dst():
    db_path = None
    cur = None
    con = None
    def __init__(self, dst_db_dir, lang):
        self.db_path = f"{dst_db_dir}/{lang}.db"
        print(f"creating {self.db_path}")
        self.con = sqlite3.connect(self.db_path)
        # same schema as the source datbase
        self.con.execute(
            "CREATE TABLE subz (\n"
            "  num INTEGER PRIMARY KEY,\n"
            "  name TEXT,\n"
            "  file BLOB\n"
            ")\n"
        )
        self.cur = self.con.cursor()

dst_by_lang = dict()

insert_query = "INSERT INTO subz VALUES (?, ?, ?)"

for row in src_con.execute(f"SELECT num, name, file FROM subz ORDER BY num ASC"):
    lang = row[1].split(".")[-4]
    if not lang in dst_by_lang:
        dst_by_lang[lang] = Dst(dst_db_dir, lang)
    dst = dst_by_lang[lang]
    dst.cur.execute(insert_query, row)
    if row[0] % 100000 == 0:
        print(f"done {row[0]}")
        for lang in dst_by_lang:
            dst = dst_by_lang[lang]
            print(f"writing {dst.db_path}")
            dst.con.commit()

src_con.close()

for lang in dst_by_lang:
    dst = dst_by_lang[lang]
    dst.con.commit()
    dst.con.close()
    # make it read-only
    os.chmod(dst.db_path, 0o444)
    print(f"done {dst.db_path}")
