#!/usr/bin/env python3

# FIXME dont create empty shards

# python -u ./new-subs-repo-git2sqlite.py 2>&1 | tee -a new-subs-repo-git2sqlite.py.log

# convert from "a million files in a million git branches"
# to "a million files in 1000 sqlite databases"

# compare new-subs-repo/ with opensubs-metadata.db

# actual files are in new-subs-repo/
# expected files are in opensubs-metadata.db

# see also
# new-subs-missing-files.py
# new-subs-repo-find-missing-subs.py
# opensubs-find-missing-subs.py

import os
import sqlite3
import subprocess # why?
import math
import shlex
import time
import glob


"""
    why not store a million files in a million git branches?

    1. "git push" and "git pull" become painfully slow

    2. adding new files is slow, about 1 file per second

    3. this would create a million files in .git

    $ ls -U .git/logs/refs/remotes/origin/nums/ | wc -l
    231910

    $ ls -U .git/logs/refs/heads/nums | wc -l
    18249

    see also

    https://stackoverflow.com/questions/28849302/impact-of-large-number-of-branches-in-a-git-repo
"""

is_debug = True
is_debug = False

debug_shard_id = None
#debug_shard_id = 10294

debug_print = lambda *a, **k: None

if is_debug:
    debug_print = print

# tmpfs
# watch tempdir:
# while true; do ls /run/user/$(id -u)/new-subs-repo-git2sqlite/nums/; sleep 1; done
tempdir = f"/run/user/{os.getuid()}/new-subs-repo-git2sqlite"
os.makedirs(tempdir, exist_ok=True)
print(f"tempdir: {tempdir}")

new_subs_path = "new-subs"
new_subs_repo_path = "new-subs-repo"
new_subs_repo_shards_path = "new-subs-repo-shards"
new_subs_trash_path = "new-subs-trash"



os.makedirs(new_subs_trash_path, exist_ok=True)



# dont use tmpfs
# no. git is equally slow on disk and ram
#tempdir = new_subs_repo_path

files_txt_path = f"{new_subs_repo_path}/files.txt"

metadata_db_default_table = "subz_metadata"

# FIXME weekly auto update from
# https://dl.opensubtitles.org/addons/export/subtitles_all.txt.gz
metadata_db_list = [
  #dict(path = "opensubs-metadata.db"),
  #dict(path = "opensubs-metadata.month.20240129T134426Z.db"),
  #dict(path = "subtitles_month.txt.gz.20240205T145227Z.db"),
  #dict(path = "subtitles_all.txt.gz.20240210T152428Z.db"),
  #dict(path = "subtitles_all.txt.gz.20240223T095232Z.db"),
  dict(path = "subtitles_all.latest.db"),
]

#metadata_db_path = "opensubs-metadata.db"
#metadata_db_table = "subz_metadata"

def shard_id_of_num(num):
    # 1000 files per shard
    # so 1 shard has about 20 MByte
    return math.floor(num / 1000)

num_info_list_by_shard_id = dict()

not_found_num_list = []
dmca_num_list = []

"""
print(f"parsing {files_txt_path}")
with open(files_txt_path) as f:
    for line in f.readlines():
        filename = line.strip()
        try:
            num = int(filename.split(".", 1)[0])
        except ValueError:
            # FIXME support the "legacy file format"
            # aka: orignal filename format
            # ignoring file 'new-subs/snowfall.s01.e05.sevenfour.(2017).pol.1cd.(7420734).zip'
            print(f"ignoring file {files_txt_path}: {repr(filename)}")
            continue
        # NOTE "dcma" is wrong
        if (
            filename == f"{num}.dmca" or
            filename == f"{num}.not-found-dmca" or
            filename == f"{num}.dcma" or
            filename == f"{num}.not-found-dcma" or
            False
        ):
            # example: 9540221.dcma
            dmca_num_list.append(num)
            continue
        if filename == f"{num}.not-found":
            # example: 1234567788.not-found
            not_found_num_list.append(num)
            continue
        shard_id = shard_id_of_num(num)
        # FIXME filter shards earlier
        if not shard_id in num_info_list_by_shard_id:
            num_info_list_by_shard_id[shard_id] = list()
        # True: file is stored in new_subs_repo_path
        num_is_stored_in_git = True
        num_info = (num, num_is_stored_in_git)
        num_info_list_by_shard_id[shard_id].append(num_info)
"""

print(f"parsing {new_subs_path}")
# based on new-subs-repo-find-missing-subs.py
# FIXME cache os.listdir(new_subs_path)
for filename in os.listdir(new_subs_path):
    # NOTE this will ignore all original filenames
    # where the sub num is in the filename suffix
    # FIXME support the "legacy file format"
    # aka: orignal filename format
    # TODO rename file to new format
    # ignoring file 'new-subs/snowfall.s01.e05.sevenfour.(2017).pol.1cd.(7420734).zip'
    # quickfix:
    # mv 'new-subs/snowfall.s01.e05.sevenfour.(2017).pol.1cd.(7420734).zip' 'new-subs/7420734.snowfall.s01.e05.sevenfour.(2017).pol.1cd.zip'
    try:
        num = int(filename.split(".", 1)[0])
    except ValueError:
        path = f"{new_subs_path}/{filename}"
        print(f"ignoring file {repr(path)}")

        # based on fetch-subs.py
        """
        match = re.fullmatch(r"([0-9]+)\.(zip|not-found|dmca|not-found-dmca|.*\.zip)", filename)
        if match:
            # new format in f"{new_subs_repo_dir}/files.txt"
            num = int(match.group(1))
            nums_done.append(num)
        match = re.fullmatch(r".*\.\([0-9]*\)\.[a-z]{3}\.[0-9]+cd\.\(([0-9]+)\)\.zip", filename)
        if match:
            # original format in new_subs_dir
            num = int(match.group(1))
            nums_done.append(num)
        """

        continue

    if (
        filename == f"{num}.dmca" or
        filename == f"{num}.not-found-dmca" or
        filename == f"{num}.dcma" or
        filename == f"{num}.not-found-dcma" or
        False
    ):
        # example: 9540221.dcma
        dmca_num_list.append(num)
        continue

    if filename == f"{num}.not-found":
        # example: 1234567788.not-found
        not_found_num_list.append(num)
        continue

    shard_id = shard_id_of_num(num)
    # FIXME filter shards earlier
    if not shard_id in num_info_list_by_shard_id:
        num_info_list_by_shard_id[shard_id] = list()
    # False: file is stored in new_subs_path
    num_is_stored_in_git = False
    num_info = (num, num_is_stored_in_git)
    num_info_list_by_shard_id[shard_id].append(num_info)

print(f"sorting num_info_list_by_shard_id")
num_files = 0
for num_info_list in num_info_list_by_shard_id.values():
    # by default. sort will sort the list by num_info[0] == num
    num_info_list.sort()
    num_files += len(num_info_list)

# stats
print(f"reduced {num_files} files to {len(num_info_list_by_shard_id)} shards")


# TODO write text files with
# not_found_num_list
# dmca_num_list

not_found_num_set = set(not_found_num_list)
dmca_num_set = set(dmca_num_list)

# find complete shards
# shard: a continuous range of files
# the range must be continuous, so it is immutable

# loop shards in ascending order
shard_id_list = list(num_info_list_by_shard_id.keys())
shard_id_list.sort()
#print("shard_id_list", shard_id_list[:20], "...")

def get_shard_range(shard_id):
    # shard 0:    0 to  999
    # shard 1: 1000 to 1999
    # shard 2: 2000 to 2999
    shard_first_num = shard_id * 1000
    shard_last_num = (shard_id + 1) * 1000 - 1
    return shard_first_num, shard_last_num

def get_shard_name(shard_id):
    #return str(shard_id)
    # last 3 digits range from 000 to 999
    return f"{shard_id}xxx"

def get_shard_path(shard_id):
    """
        123456  -> 12/34/56xxx.db
        0       -> 00/00/00xxx.db
        1234567 -> error: out of range

        limit: 1 million shards = 20 TByte = 3000 years

              99/99xxx.db -> 100**2 * 1000 files =  190 GByte over 100**2 days =   30 years
           99/99/99xxx.db -> 100**3 * 1000 files =   18 TByte over 100**3 days = 3000 years
        99/99/99/99xxx.db -> 100**4 * 1000 files = 1800 TByte over 100**4 days = 300K years
    """
    assert shard_id >= 0
    assert shard_id < 1_000_000
    shard_id_str = f"{shard_id:06d}"
    shard_path = "/".join([
        shard_id_str[0:2],
        shard_id_str[2:4],
        shard_id_str[4:6] + "xxx.db",
    ])
    return shard_path

# 12345 -> 123xxxxx
def get_shard_dir(shard_id):
    shard_name = get_shard_name(shard_id)
    shard_dir = shard_name[:-5] + "xxxxx"
    if shard_dir == "xxxxx":
        shard_dir = "0xxxxx"
    return shard_dir

for shard_id in shard_id_list:

    # old
    shard_name = get_shard_name(shard_id)
    shard_dir = get_shard_dir(shard_id)
    shard_db_path = f"{new_subs_repo_shards_path}/shards/{shard_dir}/{shard_name}.db"
    # TODO
    # new
    """
    shard_db_path = f"{new_subs_repo_shards_path}/shards/" + get_shard_path(shard_id)
    """

    shard_temp_db_path = shard_db_path + ".tmp"

    #if True:
    if debug_shard_id and shard_id == debug_shard_id:
        print("shard_id", shard_id)
        print("shard_name", shard_name)
        print("shard_dir", shard_dir)
        print("shard_db_path", shard_db_path)

    if os.path.exists(shard_db_path):
        # FIXME filter shards earlier
        # cleanup from previous runs
        # move done zip files to trash

        if debug_shard_id and shard_id == debug_shard_id:
            print("keeping shard_db_path")

        # based on new-subs-repo-find-missing-subs.py
        # FIXME cache os.listdir(new_subs_path)
        for filename in os.listdir(new_subs_path):
            # NOTE this will ignore all original filenames
            # where the sub num is in the filename suffix
            # FIXME support the "legacy file format"
            # aka: orignal filename format
            # TODO rename file to new format
            # ignoring file 'new-subs/snowfall.s01.e05.sevenfour.(2017).pol.1cd.(7420734).zip'
            # quickfix:
            # mv 'new-subs/snowfall.s01.e05.sevenfour.(2017).pol.1cd.(7420734).zip' 'new-subs/7420734.snowfall.s01.e05.sevenfour.(2017).pol.1cd.zip'
            try:
                num = int(filename.split(".", 1)[0])
            except ValueError:
                path = f"{new_subs_path}/{filename}"
                print(f"ignoring file {repr(path)}")

        # cleanup: move files to trash: *.zip and *.not-found
        # shard name 12345xxx -> glob pattern 12345[0-9][0-9][0-9].*
        for file_path in glob.glob(f"{new_subs_path}/{shard_id}[0-9][0-9][0-9].*"):
            file_name = os.path.basename(file_path)
            trash_file_path = f"{new_subs_trash_path}/{file_name}"
            #os.makedirs(os.path.dirname(trash_file_path), exist_ok=True)
            os.rename(file_path, trash_file_path)

        #print(f"ignoring existing shard {shard_id}")

        continue

    if debug_shard_id and shard_id == debug_shard_id:
        print("writing shard_db_path")

    shard_first_num, shard_last_num = get_shard_range(shard_id)
    # get list of expected nums
    # WHERE IDSubtitle < {last_num}
    # the BETWEEN operator is inclusive: a <= b <= c
    expected_num_list = []
    for metadata_db in metadata_db_list:
        #print("metadata_db", metadata_db)
        metadata_db_table = metadata_db["table"] if "table" in metadata_db else metadata_db_default_table
        query = f"""
            SELECT IDSubtitle
            FROM {metadata_db_table}
            WHERE IDSubtitle BETWEEN {shard_first_num} AND {shard_last_num}
            ORDER BY IDSubtitle ASC
        """
        metadata_db_conn = sqlite3.connect(metadata_db["path"])
        metadata_db_cur = metadata_db_conn.cursor()
        #print("query", repr(query))
        for (num,) in metadata_db_cur.execute(query):
            expected_num_list.append(num)
        if False:
            print("shard_id", shard_id)
            print("expected_num_list", expected_num_list)
            import sys
            sys.exit()

    if len(expected_num_list) == 0:
        print(f"ignoring empty shard {shard_id} - TODO update metadata_db")
        continue

    num_info_list = num_info_list_by_shard_id[shard_id]
    if len(num_info_list) == 0:
        print(f"ignoring empty shard {shard_id}")
        continue

    actual_num_list = []
    for num_info in num_info_list:
        num = num_info[0]
        actual_num_list.append(num)

    actual_num_set = set(actual_num_list)

    #if True:
    #if debug_shard_id and shard_id == debug_shard_id:
    if False:
        print("shard_id", shard_id)
        print("expected_num_list", expected_num_list)
        print("actual_num_list", actual_num_list)
        #import sys; sys.exit()

    # diff lists
    shard_is_complete = True
    for expected_num in expected_num_list:
        if expected_num in not_found_num_set:
            print(f"TODO verify: num is in metadata but was not found. num {expected_num}. reason: not found. TODO update metadata")
            # FIXME check nums range of metadata_db
            if True:
            #if False:
                os.unlink(f"new-subs/{expected_num}.not-found") # wrong not-found file
            continue
        if expected_num in dmca_num_set:
            print(f"TODO verify: num is in metadata but was not found. num {expected_num}. reason: dmca")
            continue
        if not expected_num in actual_num_set:
            shard_is_complete = False
            # stop at first missing num
            # TODO debug: show all missing nums
            # verbose
            if debug_shard_id and shard_id == debug_shard_id:
                print(f"shard {shard_id}: missing num {expected_num}")
            # TODO collect more missing nums and write missing_nums.txt
            # if less than 100 are missing per shard
            if False:
                if shard_id == 9533:
                    import sys
                    sys.exit()
            break
    if not shard_is_complete:
        if debug_shard_id and shard_id == debug_shard_id:
            print(f"ignoring incomplete shard {shard_id}")
            # TODO print missing nums
        continue

    #print("expected_num_list", expected_num_list)
    #print("actual_num_list", actual_num_list)

    # TODO why is this so slow?
    # 250 seconds per 1000 files each 20 KB

    # shard is complete
    # move expected files to sqlite
    # move unexpected files to trash
    shard_db_t1 = time.time()
    print(f"writing {shard_db_path} ...")
    os.makedirs(os.path.dirname(shard_db_path), exist_ok=True)
    #shard_db_conn = sqlite3.connect(shard_db_path)
    if os.path.exists(shard_temp_db_path):
        os.unlink(shard_temp_db_path)
    shard_db_conn = sqlite3.connect(shard_temp_db_path)
    con = shard_db_conn
    cur = con.cursor()
    # same schema as in opensubtitles.org.dump.9180519.to.9521948.by.lang.2023.04.26
    # see also: new-subs-archive.py: pack_files_sqlite(archive_path, lang_files, table_name)
    # https://sqlite.org/intern-v-extern-blob.html
    # page size 4096 seems to give best performance for 20KB files
    # but that benchmark was done with an old version of sqlite
    sqlite_page_size = 4096 # default page size of sqlite
    page_size = sqlite_page_size
    cur.executescript(f"PRAGMA page_size = {sqlite_page_size}; VACUUM;")
    cur.execute("PRAGMA count_changes=OFF")
    table_name = "zipfiles"
    cur.execute(
        f"CREATE TABLE {table_name} (\n"
        f"  num INTEGER PRIMARY KEY,\n"
        f"  name TEXT,\n"
        f"  content BLOB\n"
        f")"
    )
    query = f"INSERT INTO {table_name} VALUES (?, ?, ?)"
    #for file_path in sum_files:
    num_info_dict = dict()
    for num_info in num_info_list:
        num = num_info[0]
        num_info_dict[num] = num_info
    for expected_num in expected_num_list:
        # again...
        if expected_num in not_found_num_set:
            continue
        if expected_num in dmca_num_set:
            continue
        num_info = num_info_dict[expected_num]
        (num, num_is_stored_in_git) = num_info
        assert num == expected_num # duh...
        file_path = None
        if num_is_stored_in_git == False:
            # simple
            # FIXME cache os.listdir(new_subs_path)
            for filename in os.listdir(new_subs_path):
                # NOTE this will ignore all original filenames
                # where the sub num is in the filename suffix
                try:
                    num = int(filename.split(".", 1)[0])
                except ValueError:
                    continue
                if num == expected_num:
                    # found file
                    file_path = new_subs_path + "/" + filename
                    break
            assert file_path != None, f"FIXME file was not found: {new_subs_path}/{num}.*"

        else:
            # num_is_stored_in_git == True

            # this is really slow
            # which is the very reason why im moving from git to sqlite
            # maybe this is faster if i know the git blob hash
            # and use "git cat-file blob xxxxxxxxxxxxxxxxxxxxxxxx"

            # faster when git garbage collection is disabled

            worktree_ref = f"nums/{num}"

            old_worktree_path_list = [
                new_subs_repo_path + "/" + worktree_ref,
                new_subs_repo_path + "/new-subs-repo/" + worktree_ref,
            ]

            # use tmpfs to reduce disk writes
            worktree_path = tempdir + "/" + worktree_ref
            worktree_path = os.path.abspath(worktree_path)

            #print("worktree_path", repr(worktree_path))

            # based on new-subs-push.py

            for this_worktree_path in [worktree_path] + old_worktree_path_list:
                if os.path.exists(this_worktree_path):
                    # this should be rare
                    # unmount
                    print(f"unmounting worktree {this_worktree_path}")
                    args = [
                        "git",
                        "-C", new_subs_repo_path,
                        "worktree",
                        "remove",
                        #"--quiet",
                        "--force",
                        # fix: fatal: cannot remove a locked working tree, lock reason: initializing
                        # TODO why initializing? wait and retry?
                        "--force",
                        this_worktree_path,
                    ]
                    debug_print(shlex.join(args))
                    proc = subprocess.run(
                        args,
                        check=True,
                        timeout=9999,
                    )

            """

            FIXME ignore dmca nums

            $ ./new-subs-repo-git2sqlite.py 
            parsing new-subs-repo/files.txt
            parsing new-subs
            ignoring file 'new-subs/snowfall.s01.e05.sevenfour.(2017).pol.1cd.(7420734).zip'
            sorting num_info_list_by_shard_id
            reduced 235721 files to 525 shards
            writing new-subs-shards/shards/9540.db ...
            fatal: invalid reference: nums/9540221
            Traceback (most recent call last):
            File "/home/user/src/milahu/opensubtitles-scraper/./new-subs-repo-git2sqlite.py", line 254, in <module>
                "add",
            File "/nix/store/pzf6dnxg8gf04xazzjdwarm7s03cbrgz-python3-3.10.12/lib/python3.10/subprocess.py", line 526, in run
                raise CalledProcessError(retcode, process.args,
            subprocess.CalledProcessError: Command '['git', '-C', 'new-subs-repo', 'worktree', 'add', '--quiet', 'nums/9540221', 'nums/9540221']' returned non-zero exit status 128.

            $ grep ^9540221 new-subs-repo/files.txt
            9540221.dcma

            $ sqlite3  opensubs-metadata.db "select * from subz_metadata where IDSubtitle = 9540221" 
            9540221|Ain't She Tweet|1952|English|en|2023-05-06 02:24:54|44339|srt|1|Ain't She Tweet.DVD.NonHI.en.cc.WB|29.97|0|0|0|movie|http://www.opensubtitles.org/subtitles/9540221/ain-t-she-tweet-en

            """

            debug_print("worktree_path", repr(worktree_path))
            debug_print("worktree_ref", repr(worktree_ref))

            # NOTE relative worktree_path is relative to the "-C" argument

            args = [
                "git",
                "-C", new_subs_repo_path,
                "worktree",
                "add",
                worktree_path,
                worktree_ref,
            ]
            if not is_debug:
                args += ["--quiet"]
            debug_print(shlex.join(args))
            proc = subprocess.run(
                args,
                check=True,
                timeout=9999,
            )

            file_list = os.listdir(worktree_path)
            file_list = list(filter(lambda n: n != ".git" and n != ".gitattributes", file_list))
            if len(file_list) == 0:
                raise NotImplementedError(f"file not found in worktree {worktree_path}")
            if len(file_list) > 1:
                raise NotImplementedError(f"found multiple files in worktree {worktree_path}: {file_list}")
            file_path = worktree_path + "/" + file_list[0]

        assert file_path != None, f"FIXME file was not found: {num}.*"

        file_name = os.path.basename(file_path)

        trash_file_path = f"{new_subs_trash_path}/{file_name}"

        #os.makedirs(os.path.dirname(trash_file_path), exist_ok=True)

        name_parts = file_name.split(".")
        num = int(name_parts[0])
        assert name_parts[-1] == "zip", f"not a zip file: {file_path}"
        # no. this should NEVER happen
        # because opensubs-metadata.db has only "found" nums
        """
        if name_parts[-1] == "zip":
            print(f"ignoring non-zip file {file_path}")
            continue
        """
        # check for legacy file format before new-subs-rename-remove-num-part.py
        assert name_parts[-2] != f"({num})", f"bad filename format: {file_path}"
        # remove f"{num}." prefix and ".zip" suffix
        name = ".".join(name_parts[1:-1])

        # too complex
        # store only files here
        # and use a separate DB for all metadata
        #lang = name_parts[-3]
        #assert re.match(r"^[a-z]{3}$", lang)

        with open(file_path, "rb") as f:
            content = f.read()

        if num_is_stored_in_git:
            # done reading the file
            # now we can remove the worktree
            args = [
                "git",
                "-C", new_subs_repo_path,
                "worktree",
                "remove",
                #"--quiet", # error: unknown option `quiet'
                #"--force",
                worktree_path,
            ]
            debug_print(shlex.join(args))
            proc = subprocess.run(
                args,
                check=True,
                timeout=9999,
            )

        """
        file_name = os.path.basename(file_path)

        trash_file_path = f"{new_subs_trash_path}/{file_name}"

        #os.makedirs(os.path.dirname(trash_file_path), exist_ok=True)
        os.makedirs(new_subs_trash_path, exist_ok=True)
        """

        # dont. move the zip file to trash
        if not num_is_stored_in_git:
            os.rename(file_path, trash_file_path)

        args = (num, name, content)
        cur.execute(query, args)

    print(f"writing {shard_db_path} commit ...")
    con.commit()
    con.close()
    # atomic write, because tempfile is on the same filesystem
    os.rename(shard_temp_db_path, shard_db_path)
    shard_db_t2 = time.time()
    shard_db_dt = shard_db_t2 - shard_db_t1
    print(f"writing {shard_db_path} done in {shard_db_dt} sec")

    # cleanup: move files to trash: *.zip and *.not-found
    # shard name 12345xxx -> glob pattern 12345[0-9][0-9][0-9].*
    for file_path in glob.glob(f"{new_subs_path}/{shard_id}[0-9][0-9][0-9].*"):
        file_name = os.path.basename(file_path)
        trash_file_path = f"{new_subs_trash_path}/{file_name}"
        #os.makedirs(os.path.dirname(trash_file_path), exist_ok=True)
        os.rename(file_path, trash_file_path)

    # writing new-subs-shards/shards/9540xxx.db done in 438.5243573188782 sec
    # writing new-subs-shards/shards/9541xxx.db done in 476.93698239326477 sec
    # = almost 10 minutes
    # 1000 subs per day
    # 200 days unreleased subs
    # 200 x 10 minutes = 33 hours
    #break # debug: stop after first shard
