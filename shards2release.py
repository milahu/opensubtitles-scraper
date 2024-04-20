#! /usr/bin/env python3

import sys
import os
import sqlite3
import glob
import time

total_t1 = time.time()

release_id = 95; release_version = "20240306"
release_id = 98; release_version = "20240420"

output_db_path = f"release/opensubtitles.org.dump.{release_id}00000.to.{release_id}99999.v{release_version}/{release_id}xxxxx.db"

print("output_db_path", repr(output_db_path))

assert os.path.exists(output_db_path) == False, f"error: output exists: {output_db_path}"

os.makedirs(os.path.dirname(output_db_path))

connection = sqlite3.connect(output_db_path)

cursor = connection.cursor()

# new-subs-archive.py
sqlite_page_size = 2**12 # 4096 = 4K = default

table_name = "zipfiles"

cursor.executescript(f"PRAGMA page_size = {sqlite_page_size}; VACUUM;")
cursor.execute("PRAGMA count_changes=OFF")
cursor.execute(
    f"CREATE TABLE {table_name} (\n"
    f"  num INTEGER PRIMARY KEY,\n"
    f"  name TEXT,\n"
    f"  content BLOB\n"
    f")"
)

# parsed from https://dl.opensubtitles.org/addons/export/subtitles_all.txt.gz
# with subtitles_all.txt.gz-parse.py
matadata_db_path = "subtitles_all.latest.db"

cursor.execute("ATTACH DATABASE ? as metadata_db", (matadata_db_path,))



def exit(rc=0):
    global connection
    global total_t1
    connection.commit()
    connection.close()
    total_t2 = time.time()
    print(f"everything done in {total_t2 - total_t1} seconds")
    sys.exit(rc)



for db_path in sorted(glob.glob(f"new-subs-repo-shards/shards/{release_id}xxxxx/*.db")):

    shard_id = int(os.path.basename(db_path)[:-6]) # remove "xxx.db" suffix
    shard_num_first = shard_id * 1000
    shard_num_last = shard_num_first + 999
    #print("db_path", db_path, "shard_num_range", shard_num_first, shard_num_last)

    t1 = time.time()

    cursor.execute("ATTACH DATABASE ? as source_db", (db_path,))

    # too simple: copy all data
    #cursor.execute(f"INSERT INTO main.{table_name} SELECT * FROM source_db.{table_name}")

    # no. false error:
    # FIXME missing nums in new-subs-repo-shards/shards/95xxxxx/9503xxx.db: [9503998]
    # 9503998 was deleted because DMCA
    # https://www.opensubtitles.org/en/subtitleserve/sub/9503998
    # redirects to
    # https://www.opensubtitles.org/en/msg-dmca
    # ... so metadata_db is not the source of truth
    # but still, when subs were deleted from metadata_db, dont copy them
    """
    print("compare")
    # make sure that all zipfiles listed in metadata exist in source_db
    # find missing nums in source_db. expected nums are in metadata_db
    sql_query = (
      f"select distinct metadata_db.subz_metadata.rowid from metadata_db.subz_metadata "
      f"where metadata_db.subz_metadata.rowid between {shard_num_first} and {shard_num_last} and not exists ("
      f"  select 1 from source_db.{table_name} "
      f"  where metadata_db.subz_metadata.rowid = source_db.{table_name}.rowid"
      f")"
    )
    missing_nums = cursor.execute(sql_query).fetchall()
    if len(missing_nums) > 0:
        missing_nums = list(map(lambda row: row[0], missing_nums))
        print(f"FIXME missing nums in {db_path}:", missing_nums[:1500])
        exit(1)
    # ok. all zipfiles listed in metadata exist in source_db
    #cursor.execute(f"INSERT INTO main.{table_name} SELECT * FROM source_db.{table_name}")
    # copy from source_db to main, filter by metadata_db.subz_metadata
    """

    # copy all nums that exist in source_db and metadata_db
    #print("copy")
    sql_query = (
      f"insert into main.{table_name} select * from source_db.{table_name} "
      f"where exists ("
      f"  select 1 from metadata_db.subz_metadata "
      f"  where metadata_db.subz_metadata.rowid = source_db.{table_name}.rowid"
      f")"
    )
    cursor.execute(sql_query)

    """
    print("check 1")
    # check 1
    sql_query = (
      f"select count(1) from metadata_db.subz_metadata "
      f"where metadata_db.subz_metadata.rowid between {shard_num_first} and {shard_num_last}"
    )
    num_expected = cursor.execute(sql_query).fetchone()[0]
    sql_query = (
      f"select count(1) from main.{table_name} "
      f"where main.{table_name}.rowid between {shard_num_first} and {shard_num_last}"
    )
    num_actual = cursor.execute(sql_query).fetchone()[0]
    if num_expected != num_actual:
        print("error: num_expected != num_actual: {num_expected} != {num_actual}")
        exit(1)

    print("check 2")
    # check 2
    sql_query = (
      f"select distinct metadata_db.subz_metadata.rowid from metadata_db.subz_metadata "
      f"where metadata_db.subz_metadata.rowid between {shard_num_first} and {shard_num_last} and not exists ("
      f"  select 1 from main.{table_name} where metadata_db.subz_metadata.rowid = main.{table_name}.rowid"
      f")"
    )
    missing_nums = cursor.execute(sql_query).fetchall()
    if len(missing_nums) > 0:
        missing_nums = list(map(lambda row: row[0], missing_nums))
        print(f"FIXME missing nums in {output_db_path}:", missing_nums)
        exit(1)
    """

    connection.commit()
    cursor.execute("DETACH DATABASE source_db")
    t2 = time.time()
    print(f"db_path {db_path} done in {t2 - t1} seconds")



print(f"done {output_db_path}")

exit()
