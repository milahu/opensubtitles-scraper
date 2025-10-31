#! /usr/bin/env python3

# join shards to a single database

# TODO after: release2torrent.sh
# TODO after: release_add_to_git.py $torrent
# TODO after: reddit_add_torrent.py $torrent

# TODO merge all these scripts
# TODO call from main.sh

import sys
import os
import re
import sqlite3
import glob
import time
import datetime
import subprocess
import shlex
import argparse

import torf

parser = argparse.ArgumentParser(
    prog='shards2release',
    #description='Fetch subtitles',
    #epilog='Text at the bottom of help',
)

parser.add_argument(
    '--min-release-id',
    dest="min_release_id", # options.min_release_id
    default=0,
    type=int,
    metavar="N",
    help=f"minimum release_id. example: 100 -> start from release 100xxxxx",
)

options = parser.parse_args()

total_t1 = time.time()

new_subs_repo_path = "opensubtitles-scraper-new-subs"
# new_subs_repo_modified = False
new_subs_repo_remove_paths = []

trackers = None

def get_trackers():
    # https://github.com/ngosang/trackerslist
    url = "https://github.com/ngosang/trackerslist/raw/refs/heads/master/trackers_best_ip.txt"
    print("fetching", url)
    import requests
    response = requests.get(url)
    assert response.status_code == 200, f"response.status_code {response.status_code}"
    trackers = re.findall(r"^[a-z]+\S+", response.text, re.M)
    trackers = trackers[:5] # top 5
    return trackers

def run(args, **kwargs):
    print(">", shlex.join(args))
    return subprocess.run(args, **kwargs)

#shard_dir_list = os.listdir(new_subs_repo_path + "/shards")
shard_dir_list = glob.glob(new_subs_repo_path + "/shards/*xxxxx")

# numeric sort in descending order
# -5: remove "xxxxx" suffix
shard_dir_list.sort(key=lambda shard_dir: -1 * int(os.path.basename(shard_dir)[:-5]))

#print("shard_dir_list", shard_dir_list)

files_per_shard = 100

for shard_dir in shard_dir_list:

    release_id = int(os.path.basename(shard_dir)[:-5])
    #print("release_id", release_id)

    if release_id < options.min_release_id:
        continue

    shard_file_list = glob.glob(shard_dir + "/*xxx.db")
    if len(shard_file_list) != files_per_shard:
        # ignore incomplete shard dir
        print(f"shard dir {shard_dir} is incomplete (done {len(shard_file_list)} of {files_per_shard} shards) -> ignoring")
        continue

    torrent_files = (
        glob.glob(f"release/opensubtitles.org.dump.{release_id}00000.to.{release_id}99999.v*.torrent") +
        glob.glob(f"release/opensubtitles.org.dump.{release_id}xxxxx.v*.torrent")
    )

    if len(torrent_files) > 0:
        print(f"shard dir {shard_dir} has release -> removing shard_dir from new_subs_repo")
        p = f"shards/{release_id}xxxxx"
        new_subs_repo_remove_paths.append(p)
        continue

    release_version = datetime.datetime.fromtimestamp(os.path.getmtime(shard_dir)).strftime("%Y%m%d")
    #print("release_version", release_version)

    # release_name = f"opensubtitles.org.dump.{release_id}00000.to.{release_id}99999.v{release_version}"
    release_name = f"opensubtitles.org.dump.{release_id}xxxxx.v{release_version}"

    output_dir = f"release/{release_name}"

    if os.path.exists(output_dir):
        # TODO verify that the release is complete = count subtitles
        print(f"shard dir {shard_dir} is complete -> keeping existing {output_dir}")
        continue

    print(f"shard dir {shard_dir} is complete -> adding release {release_name}")

    # output_db_path = f"release/opensubtitles.org.dump.{release_id}00000.to.{release_id}99999.v{release_version}/{release_id}xxxxx.db"
    output_db_path = f"{output_dir}/{release_id}xxxxx.db"
    print("output_db_path", repr(output_db_path))
    assert os.path.exists(output_db_path) == False, f"error: output exists: {output_db_path}"

    output_torrent_path = f"{output_dir}.torrent"
    print("output_torrent_path", output_torrent_path)
    assert os.path.exists(output_torrent_path) == False, f"error: output exists: {output_torrent_path}"

    os.makedirs(os.path.dirname(output_db_path) or ".", exist_ok=True)
    os.makedirs(os.path.dirname(output_torrent_path) or ".", exist_ok=True)

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
    matadata_db_path = "subtitles_all.db"

    assert os.path.exists(matadata_db_path)
    assert os.path.getsize(matadata_db_path) > 0

    print(f"attaching {matadata_db_path!r} as metadata_db")
    cursor.execute("ATTACH DATABASE ? as metadata_db", (matadata_db_path,))



    def exit(rc=0):
        global connection
        global total_t1
        connection.commit()
        connection.close()
        total_t2 = time.time()
        print(f"everything done in {total_t2 - total_t1} seconds")
        sys.exit(rc)



    # note: no need for numeric sort because of the release_id prefix
    for db_path in sorted(glob.glob(f"{new_subs_repo_path}/shards/{release_id}xxxxx/{release_id}*.db")):

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



    # add some info ...

    info_txt = "".join(map(lambda line: line + "\n", [
        "generated by",
        "https://github.com/milahu/opensubtitles-scraper",
    ]))

    output_dir = os.path.dirname(output_db_path)
    #info_dir = output_dir + "/info"
    info_dir = output_dir # dont create subdirectory for only one file
    os.makedirs(info_dir, exist_ok=True)

    with open(info_dir + "/info.txt", "w") as f:
        f.write(info_txt)

    print("writing", output_torrent_path)
    if not trackers:
        trackers = get_trackers()
    torrent = torf.Torrent(
        path=output_dir,
        trackers=trackers,
    )
    torrent.generate()
    torrent.write(output_torrent_path)

if len(new_subs_repo_remove_paths) > 0:
    print("removing paths from new_subs_repo:", new_subs_repo_remove_paths)
    args = ["bash", "remove-shards.sh"]
    rest_paths = []
    for path in new_subs_repo_remove_paths:
        if re.fullmatch(r"shards/[0-9]+xxxxx", path):
            args.append(path)
        else:
            rest_paths.append(path)
    run(args, cwd=new_subs_repo_path)
    if rest_paths:
        print(f"FIXME remove rest_paths {rest_paths}")
