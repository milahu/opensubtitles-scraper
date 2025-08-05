#! /usr/bin/env python3


# central script to run all other scripts
# but usually, you just need these scripts:
# - fetch-subs.py
# - new-subs-archive.py
# - new-subs-404-dcma-files.py


import os
import subprocess
import sys
import sqlite3
#from urllib.request import urlretrieve
import urllib.request
import gzip


zipfiles_db_path = "opensubtitles.org.Actually.Open.Edition.2022.07.25/opensubs.db"
zipfiles_db_count_txt = "opensubs-count.txt"
zipfiles_table_name = "subz"
zipfile_names_table_name = "zipfile_names"
zipfile_names_parsed_table_name = "zipfile_names_parsed"

# rebuild table: opensubs-metadata-rebuild-metadata.sh
# https://dl.opensubtitles.org/addons/export/
# https://dl.opensubtitles.org/addons/export/subtitles_all.txt.gz
# TODO incremental update with day/week/month release
# https://dl.opensubtitles.org/addons/export/subtitles_day.txt.gz
# https://dl.opensubtitles.org/addons/export/subtitles_week.txt.gz
# https://dl.opensubtitles.org/addons/export/subtitles_month.txt.gz
subtitles_all_txt_gz_path = "opensubtitles.org.Actually.Open.Edition.2022.07.25/subtitles_all.txt.gz"
subtitles_all_table_name = "subz_metadata" # TODO rename to subtitles_all

# http://www.opensubtitles.org/addons/export_languages.php
# https://trac.opensubtitles.org/projects/opensubtitles/wiki/XMLRPC

metadata_db_path = "opensubs-metadata.db"
metadata_table_name = "subz_xxxxxxxx"

# kaggle.com requires login before download
# user must download the files manually
# https://www.kaggle.com/datasets/ashirwadsangwan/imdb-dataset
#imdb_title_basics_tsv_gz_url = "https://datasets.imdbws.com/title.basics.tsv.gz"
imdb_title_basics_tsv_gz_url = None
imdb_title_basics_tsv_gz_path = "title.basics.tsv.gz"
imdb_title_basics_table_name = "imdb_title_basics"

#imdb_title_episode_tsv_gz_url = "https://datasets.imdbws.com/title.episode.tsv.gz"
imdb_title_episode_tsv_gz_url = None
imdb_title_episode_tsv_gz_path = "title.episode.tsv.gz"
imdb_title_episode_table_name = "imdb_title_episode"

min_db_size = 4096 * 10 # sqlite db with at least 10 pages

"""
zipfiles_con = sqlite3.connect(zipfiles_db_path)
zipfiles_cur = zipfiles_con.cursor()

metadata_con = sqlite3_connect_readonly(metadata_db_path)
metadata_cur = metadata_con.cursor()
"""


def sqlite3_connect_readonly(db_path):
    uri = f"file://{os.path.abspath(db_path)}?mode=ro"
    return sqlite3.connect(uri, uri=True)


def has_table(db_path, table_name):
    con = sqlite3_connect_readonly(db_path)
    cur = con.cursor()
    try:
        cur.execute(f"SELECT 1 FROM {table_name} limit 1")
    except sqlite3.OperationalError:
        con.close()
        return False
    con.close()
    return True


if not os.path.exists(metadata_db_path):
    raise FileNotFoundError(metadata_db_path)


table_name = subtitles_all_table_name
if has_table(metadata_db_path, table_name):
    print(f"found table {table_name}")
else:
    print(f"building table {table_name} ...")
    args = [
        sys.executable, # python exe
        "subtitles_all.txt.gz-parse.py",
        metadata_db_path,
        table_name,
        subtitles_all_txt_gz_path,
        "subtitles_all.txt.gz-parse-errors.txt",
        "subtitles_all.txt.gz-parse-debug.txt",
    ]
    subprocess.run(
        args,
        check=True,
    )
    print(f"building table {table_name} done")
con = sqlite3_connect_readonly(metadata_db_path)
cur = con.cursor()
subtitles_all_count, = cur.execute(f"SELECT COUNT() FROM {table_name}").fetchone()
print(f"size of table {table_name}", subtitles_all_count)
con.close()


# this is slow, so cache the result
if os.path.exists(zipfiles_db_count_txt):
    with open(zipfiles_db_count_txt, "r") as f:
        zipfiles_db_count = int(f.read())
else:
    con = sqlite3_connect_readonly(zipfiles_db_path)
    cur = con.cursor()
    print("zipfiles_db_count ...")
    sql_query = f"SELECT COUNT() FROM {zipfiles_table_name}"
    print("query:", sql_query)
    zipfiles_db_count, = cur.execute(sql_query).fetchone()
    con.close()
    with open(zipfiles_db_count_txt, "w") as f:
        f.write(f"{zipfiles_db_count}\n")
print("zipfiles_db_count:", zipfiles_db_count)
missing_metadata = zipfiles_db_count - subtitles_all_count
if missing_metadata > 0:
    print(f"warning: missing metadata for {missing_metadata} zipfiles")


table_name = zipfile_names_table_name
table_name_tmp = f"{table_name}_tmp"
if has_table(metadata_db_path, table_name):
    print(f"found table {table_name}")
else:
    print(f"building table {table_name} ...")
    assert os.path.exists(zipfiles_db_path), "missing input file"
    src_con = sqlite3_connect_readonly(zipfiles_db_path)
    src_cur = src_con.cursor()
    dst_con = sqlite3_connect_readonly(metadata_db_path)
    dst_cur = dst_con.cursor()
    if has_table(metadata_db_path, table_name_tmp):
        print(f"deleting tmp table {table_name_tmp}")
        dst_cur.execute(f"DROP TABLE {table_name_tmp}")
        dst_con.commit()
    dst_cur.execute(f"CREATE TABLE {table_name_tmp}(num INTEGER PRIMARY KEY, zipfile_name TEXT)")
    num_done = 0
    # substring:
    # a: attachment; filename="alien.3.(1992).eng.2cd.(1).zip"
    # b: alien.3.(1992).eng.2cd.(1).zip
    for num, zipfile_name in src_cur.execute(f"SELECT num, SUBSTRING(name, 23, LENGTH(name) - 23) FROM {zipfiles_table_name}"):
        dst_cur.execute(f"insert into {table_name_tmp}(num, zipfile_name) values(?, ?)", (num, zipfile_name))
        num_done += 1
        if num_done % 10000 == 0:
            print("done", num_done)
    dst_cur.execute(f"alter table {table_name_tmp} rename to {table_name}")
    dst_con.commit()
    dst_con.close()
    src_con.close()
    print(f"building table {table_name} done")
con = sqlite3_connect_readonly(metadata_db_path)
cur = con.cursor()
zipfile_names_count, = cur.execute(f"SELECT COUNT() FROM {table_name}").fetchone()
print(f"size of table {table_name}", zipfile_names_count)
con.close()


# in most cases, we use IMDB to get movie names
# only if the IMDB-number is missing, we fall back to zipfiles_parsed_db
if os.path.exists(metadata_db_path):
    print("found zipfiles_parsed_db")
else:
    print("building zipfiles_parsed_db ...")
    args = [
        sys.executable, # python exe
        "opensubtitles_dump_client/parse-zipnames.py",
        metadata_db_path,
        zipfile_names_table_name,
        zipfile_names_parsed_table_name,
    ]
    subprocess.run(
        args,
        check=True,
    )
    print("building zipfiles_parsed_db done")
con = sqlite3_connect_readonly(metadata_db_path)
cur = con.cursor()
zipfiles_parsed_db_count, = cur.execute(f"SELECT COUNT() FROM {zipfile_names_parsed_table_name}").fetchone()
print("zipfiles_parsed_db_count:", zipfiles_parsed_db_count)
assert zipfiles_parsed_db_count == zipfiles_db_count
con.close()


# imdb
# https://opendata.stackexchange.com/questions/1073/where-to-get-imdb-datasets
# https://github.com/Chessbrain/IMDB-DB-Dump-Projects
#   https://datasets.imdbws.com/ # TODO how old is the data?
#     name.basics.tsv.gz = actor names
#     title.akas.tsv.gz = movie alias-names?
#     title.basics.tsv.gz = movie: title, year, minutes, genre
#     title.crew.tsv.gz = crew names?
#     title.episode.tsv.gz = parent, season, episode
#     title.principals.tsv.gz = relations between titles and names. ex: A is director of movie B
#     title.ratings.tsv.gz = movie ratings
# https://www.kaggle.com/datasets/ashirwadsangwan/imdb-dataset
#   2023-04-23 (weekly updates)
#   download requires login (TODO mirror over torrent, one torrent per tsv file)
# https://stackoverflow.com/questions/16694907/download-large-file-in-python-with-requests
def fetch_url(url, dst):
    if os.path.exists(dst):
        print(f"found {dst}")
    else:
        print(f"fetching {dst} ...")
        urllib.request.urlretrieve(url, dst)
        print(f"fetching {dst} done")
#fetch_url(imdb_title_basics_tsv_gz_url, imdb_title_basics_tsv_gz_path)
#fetch_url(imdb_title_episode_tsv_gz_url, imdb_title_episode_tsv_gz_path)
if not os.path.exists(imdb_title_basics_tsv_gz_path):
    raise Exception(f"please download {imdb_title_basics_tsv_gz_path} from https://www.kaggle.com/datasets/ashirwadsangwan/imdb-dataset")
if not os.path.exists(imdb_title_episode_tsv_gz_path):
    raise Exception(f"please download {imdb_title_episode_tsv_gz_path} from https://www.kaggle.com/datasets/ashirwadsangwan/imdb-dataset")


src = imdb_title_basics_tsv_gz_path
dst = metadata_db_path
table_name = imdb_title_basics_table_name
table_name_tmp = f"{table_name}_tmp"
if os.path.exists(dst):
    print(f"found table {table_name}")
else:
    print(f"building table {table_name} ...")
    con = sqlite3.connect(dst)
    cur = con.cursor()
    if has_table(metadata_db_path, table_name_tmp):
        print(f"deleting tmp table {table_name_tmp}")
        cur.execute(f"DROP TABLE {table_name_tmp}")
        con.commit()
    with gzip.open(src, "rt") as f:
        # read first line
        line = next(f)
        line = line[0:-1] # all lines end with "\n"
        cols = line.split("\t")
        #print("line", repr(line))
        #print("cols", repr(cols))
        assert cols == ['tconst', 'titleType', 'primaryTitle', 'originalTitle', 'isAdult', 'startYear', 'endYear', 'runtimeMinutes', 'genres'], f"actual cols {cols}"
        cur.execute("\n".join([
            f"CREATE TABLE {table_name_tmp} (",
            "  tconst INTEGER PRIMARY KEY,",
            "  titleType TEXT,", # TODO enum?
            "  primaryTitle TEXT,",
            "  originalTitle TEXT,",
            "  isAdult TEXT,", # TODO bool?
            "  startYear INTEGER,", # TODO \N -> 0
            "  endYear INTEGER,", # TODO \N -> 0
            "  runtimeMinutes INTEGER,", # TODO \N -> 0
            "  genres TEXT",
            ")",
        ]))
        insert_sql_query = f"""INSERT INTO {table_name_tmp}({",".join(cols)}) VALUES({",".join(["?" for _ in cols])})"""
        # read other lines
        for line in f:
            line = line[0:-1] # all lines end with "\n"
            cols = line.split("\t")
            #print("line", repr(line))
            #print("cols", repr(cols))
            # "\\N" means "no value"
            cols = list(map(lambda col: "" if col == "\\N" else col, cols))
            assert cols[0].startswith("tt") # tconst
            cols[0] = int(cols[0][2:]) # tconst
            cols[5] = int(cols[5] or "0") # startYear
            cols[6] = int(cols[6] or "0") # endYear
            cur.execute(insert_sql_query, cols)
    cur.execute(f"ALTER TABLE {table_name_tmp} RENAME TO {table_name}")
    con.commit()
    con.close()
    print(f"building table {table_name} done")
assert os.path.getsize(dst) > min_db_size
con = sqlite3.connect(dst)
cur = con.cursor()
imdb_title_basics_db_count, = cur.execute(f"SELECT COUNT() FROM {imdb_title_basics_table_name}").fetchone()
print("imdb_title_basics_db_count:", imdb_title_basics_db_count)
con.close()


src = imdb_title_episode_tsv_gz_path
dst = metadata_db_path
table_name = imdb_title_episode_table_name
table_name_tmp = f"{table_name}_tmp"
if os.path.exists(dst):
    print(f"found table {table_name}")
else:
    print(f"building table {table_name} ...")
    con = sqlite3.connect(dst)
    cur = con.cursor()
    if has_table(metadata_db_path, table_name_tmp):
        print(f"deleting tmp table {table_name_tmp}")
        cur.execute(f"DROP TABLE {table_name_tmp}")
        con.commit()
    with gzip.open(src, "rt") as f:
        # read first line
        line = next(f)
        line = line[0:-1] # all lines end with "\n"
        cols = line.split("\t")
        #print("line", repr(line))
        #print("cols", repr(cols))
        assert cols == ['tconst', 'parentTconst', 'seasonNumber', 'episodeNumber'], f"actual cols {cols}"
        cur.execute("\n".join([
            f"CREATE TABLE {table_name_tmp} (",
            "  tconst INTEGER PRIMARY KEY,",
            "  parentTconst INTEGER,",
            "  seasonNumber INTEGER,",
            "  episodeNumber INTEGER",
            ")",
        ]))
        insert_sql_query = f"""INSERT INTO {table_name_tmp}({",".join(cols)}) VALUES({",".join(["?" for _ in cols])})"""
        # read other lines
        for line in f:
            line = line[0:-1] # all lines end with "\n"
            cols = line.split("\t")
            #print("line", repr(line))
            #print("cols", repr(cols))
            # "\\N" means "no value"
            cols = list(map(lambda col: "" if col == "\\N" else col, cols))
            assert cols[0].startswith("tt") # tconst
            assert cols[1].startswith("tt") # parentTconst
            cols[0] = int(cols[0][2:]) # tconst
            cols[1] = int(cols[1][2:]) # parentTconst
            cols[2] = int(cols[2] or "0") # seasonNumber
            cols[3] = int(cols[3] or "0") # episodeNumber
            cur.execute(insert_sql_query, cols)
    cur.execute(f"ALTER TABLE {table_name_tmp} RENAME TO {table_name}")
    con.commit()
    con.close()
    print(f"building table {table_name} done")
assert os.path.getsize(dst) > min_db_size
con = sqlite3.connect(dst)
cur = con.cursor()
imdb_title_episode_db_count, = cur.execute(f"SELECT COUNT() FROM {imdb_title_basics_table_name}").fetchone()
print("imdb_title_episode_db_count:", imdb_title_episode_db_count)
con.close()


"""
if os.path.exists(metadata_db_path):
    print("found movie_names_db")
else:
    # TODO index-compress.py
    # how was this generated? f"index-grouped/index.txt.grouped.{lang_code}"
    # ./opensubtitles_dump_client/num-movies-tvs.py:4:with open("index-grouped/index.txt.grouped.eng") as f:
    # ./opensubtitles_dump_client/repack.py:31:#index_file = f"index-grouped/index.txt.grouped.{lang_code}"
    # ./opensubtitles_dump_client/readme.md:10:Command being timed: "python -u index-compress.py group index.txt index.txt.grouped"
    print("building movie_names_db ...")
    assert os.path.exists(metadata_db_path)
    src_con = sqlite3_connect_readonly(metadata_db_path)
    src_cur = src_con.cursor()
    dst_con = sqlite3_connect_readonly(metadata_db_path)
    dst_cur = dst_con.cursor()
    dst_cur.execute("create table subz_movie_names(name, year, kind)")
    num_done = 0
    for num, zipfile_name in src_cur.execute("SELECT num, zipfile_name FROM subz_zipfiles"):
        dst_cur.execute("insert into subz_zipfiles(num, zipfile_name) values(?, ?)", (num, zipfile_name))
        num_done += 1
        if num_done % 10000 == 0:
            print("done", num_done)
    dst_con.commit()
    dst_con.close()
    print("building movie_names_db done")
assert os.path.getsize(metadata_db_path) > min_db_size
con = sqlite3_connect_readonly(metadata_db_path)
cur = con.cursor()
movie_names_db_count, = cur.execute("SELECT COUNT() FROM subz_movie_names").fetchone()
print("movie_names_db_count:", movie_names_db_count)
"""


raise NotImplementedError("TODO store all generated tables in one db")


# TODO condition?
if True:
    print("repacking archives ...")
    args = [
        sys.executable, # python exe
        "opensubtitles_dump_client/repack.py"
    ]
    subprocess.run(
        args,
        check=True,
    )
    print("repacking archives done")
