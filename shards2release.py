#! /usr/bin/env python3

# join shards to a single database

# TODO after: release2torrent.sh
# TODO after: release_add_to_git.py $torrent
# TODO after: reddit_add_torrent.py $torrent

# TODO merge all these scripts
# TODO call from main.sh

import sys
import os
import sqlite3
import glob
import time
import datetime
import subprocess
import shlex

total_t1 = time.time()

# FIXME auto detect from files in release/
release_id = 95; release_version = "20240306"
release_id = 98; release_version = "20240420"
release_id = 99; release_version = "20240609"
release_id=100; release_version="20240820" # actually 20240803
release_id=101; release_version="20241003"
release_id=102; release_version="20241124"

new_subs_repo_path = "new-subs-repo-shards"
# new_subs_repo_modified = False
new_subs_repo_remove_paths = []

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

    shard_file_list = glob.glob(shard_dir + "/*xxx.db")
    if len(shard_file_list) != files_per_shard:
        # ignore incomplete shard dir
        print(f"shard dir {shard_dir} is incomplete (done {len(shard_file_list)} of {files_per_shard} shards) -> ignoring")
        continue

    release_id = int(os.path.basename(shard_dir)[:-5])
    #print("release_id", release_id)

    torrent_files = glob.glob(f"release/opensubtitles.org.dump.{release_id}00000.to.{release_id}99999.v*.torrent")

    if len(torrent_files) > 0:
        print(f"shard dir {shard_dir} has release -> removing shard_dir from new_subs_repo")
        p = f"shards/{release_id}xxxxx"
        new_subs_repo_remove_paths.append(p)
        continue

    release_version = datetime.datetime.fromtimestamp(os.path.getmtime(shard_dir)).strftime("%Y%m%d")
    #print("release_version", release_version)

    release_name = f"opensubtitles.org.dump.{release_id}00000.to.{release_id}99999.v{release_version}"

    print(f"shard dir {shard_dir} is complete -> adding release {release_name}")



    output_db_path = f"release/opensubtitles.org.dump.{release_id}00000.to.{release_id}99999.v{release_version}/{release_id}xxxxx.db"

    print("output_db_path", repr(output_db_path))

    assert os.path.exists(output_db_path) == False, f"error: output exists: {output_db_path}"

    os.makedirs(os.path.dirname(output_db_path) or ".", exist_ok=True)

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

    info_txt = """\
    generated by
    https://github.com/milahu/opensubtitles-scraper
    """

    output_dir = os.path.dirname(output_db_path)
    info_dir = output_dir + "/info"
    os.makedirs(info_dir, exist_ok=True)

    with open(info_dir + "/info.txt", "w") as f:
        f.write(info_txt)


########


if len(new_subs_repo_remove_paths) > 0:
    # remove shard_dir from git repo + force-push git repo
    # based on new-subs-repo-shards/remove-shards.sh
    print("removing paths from new_subs_repo:", new_subs_repo_remove_paths)
    run(["git", "-C", new_subs_repo_path, "checkout", "main"], check=True)
    t = datetime.datetime.now(datetime.UTC).strftime("%Y%m%dT%H%M%SZ")
    run(["git", "-C", new_subs_repo_path, "branch", "bak-main-" + t], check=True)
    args = ["git", "-C", new_subs_repo_path, "filter-repo", "--force", "--refs", "main", "--invert-paths"]
    for path in new_subs_repo_remove_paths:
        args += ["--path", path]
    run(args, check=True)
    print("pushing new_subs_repo")
    # git -C new-subs-repo-shards/ remote show
    git_remote_list = run(["git", "-C", new_subs_repo_path, "remote", "show"], check=True, stdout=subprocess.PIPE, text=True).stdout
    for git_remote in git_remote_list.strip().split("\n"):
        # git -C new-subs-repo-shards/ push --force github
        run(["git", "-C", new_subs_repo_path, "push", "--force", git_remote]) # , check=True)


