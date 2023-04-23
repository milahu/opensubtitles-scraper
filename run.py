#! /usr/bin/env python3

import os
import subprocess
import sys
import sqlite3
#from urllib.request import urlretrieve
import urllib.request
import gzip


opensubs_db_path = "opensubs.db"
metadata_db_path = "opensubs-metadata.db"
zipfiles_db_path = "opensubs-zipfiles.db"
zipfiles_parsed_db_path = "opensubs-zipfiles-parsed.db"
movie_names_db_path = "opensubs-movie-names.db"
imdb_title_basics_tsv_gz_path = "title.basics.tsv.gz"
imdb_title_episode_tsv_gz_path = "title.episode.tsv.gz"
imdb_title_basics_db_path = "title.basics.db"
imdb_title_episode_db_path = "title.episode.db"


if os.path.exists(metadata_db_path):
    print("found metadata_db")
else:
    print("building metadata_db ...")
    args = [
        sys.executable, # python exe
        "subtitles_all/subtitles_all.txt.gz-parse.py",
        metadata_db_path,
    ]
    subprocess.run(
        args,
        check=True,
    )
    print("building metadata_db done")
assert os.path.getsize(metadata_db_path) > 0
con = sqlite3.connect(metadata_db_path)
cur = con.cursor()
metadata_db_count, = cur.execute("select count() from subz_metadata").fetchone()
print("metadata_db_count:", metadata_db_count)


if os.path.exists(zipfiles_db_path):
    print("found zipfiles_db")
else:
    #assert False
    print("building zipfiles_db ...")
    src_con = sqlite3.connect(opensubs_db_path)
    src_cur = src_con.cursor()
    dst_con = sqlite3.connect(zipfiles_db_path)
    dst_cur = dst_con.cursor()
    # substring:
    # a: attachment; filename="alien.3.(1992).eng.2cd.(1).zip"
    # b: alien.3.(1992).eng.2cd.(1).zip
    dst_cur.execute("create table subz_zipfiles(num INTEGER PRIMARY KEY, zipfile TEXT)")
    num_done = 0
    for num, zipfile in src_cur.execute("select num, substring(name, 23, length(name) - 23) from subz"):
        dst_cur.execute("insert into subz_zipfiles(num, zipfile) values(?, ?)", (num, zipfile))
        num_done += 1
        if num_done % 10000 == 0:
            print("done", num_done)
    dst_con.commit()
    dst_con.close()
    print("building zipfiles_db done")
assert os.path.getsize(zipfiles_db_path) > 0
con = sqlite3.connect(zipfiles_db_path)
cur = con.cursor()
zipfiles_db_count, = cur.execute("select count() from subz_zipfiles").fetchone()
print("zipfiles_db_count:", zipfiles_db_count)
missing_metadata = zipfiles_db_count - metadata_db_count
if missing_metadata > 0:
    print(f"warning: missing metadata for {missing_metadata} zipfiles")


if os.path.exists(zipfiles_parsed_db_path):
    print("found zipfiles_parsed_db")
else:
    print("building zipfiles_parsed_db ...")
    args = [
        sys.executable, # python exe
        "opensubtitles_dump_client/parse-zipnames.py",
        #zipfiles_db_path,
        #zipfiles_parsed_db_path,
    ]
    subprocess.run(
        args,
        check=True,
    )
    print("building zipfiles_parsed_db done")
assert os.path.getsize(zipfiles_parsed_db_path) > 0
con = sqlite3.connect(zipfiles_parsed_db_path)
cur = con.cursor()
zipfiles_parsed_db_count, = cur.execute("select count() from subz_zipfiles_parsed").fetchone()
print("zipfiles_parsed_db_count:", zipfiles_parsed_db_count)
missing_metadata = zipfiles_parsed_db_count - metadata_db_count
if missing_metadata > 0:
    print(f"warning: missing metadata for {missing_metadata} zipfiles")


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
fetch_url("https://datasets.imdbws.com/title.basics.tsv.gz", imdb_title_basics_tsv_gz_path)
fetch_url("https://datasets.imdbws.com/title.episode.tsv.gz", imdb_title_episode_tsv_gz_path)


src = imdb_title_basics_tsv_gz_path
dst = imdb_title_basics_db_path
if os.path.exists(dst):
    print(f"found {dst}")
else:
    print(f"building {dst} ...")
    con = sqlite3.connect(dst)
    cur = con.cursor()
    with gzip.open(src, "rt") as f:
        # TODO better? first line vs other lines
        # read first line
        line = next(f)
        line = line[0:-1] # all lines end with "\n"
        cols = line.split("\t")
        #print("line", repr(line))
        #print("cols", repr(cols))
        assert cols == ['tconst', 'titleType', 'primaryTitle', 'originalTitle', 'isAdult', 'startYear', 'endYear', 'runtimeMinutes', 'genres'], f"actual cols {cols}"
        cur.execute("\n".join([
            "CREATE TABLE imdb_title_basics (",
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
        insert_sql_query = f"""INSERT INTO imdb_title_basics({",".join(cols)}) VALUES({",".join(["?" for _ in cols])})"""
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
    con.commit()
    con.close()
    print(f"building {dst} done")
assert os.path.getsize(dst) > 0
con = sqlite3.connect(dst)
cur = con.cursor()
imdb_title_basics_db_count, = cur.execute("select count() from imdb_title_basics").fetchone()
print("imdb_title_basics_db_count:", imdb_title_basics_db_count)


src = imdb_title_episode_tsv_gz_path
dst = imdb_title_episode_db_path
if os.path.exists(dst):
    print(f"found {dst}")
else:
    print(f"building {dst} ...")
    con = sqlite3.connect(dst)
    cur = con.cursor()
    with gzip.open(src, "rt") as f:
        # TODO better? first line vs other lines
        # read first line
        line = next(f)
        line = line[0:-1] # all lines end with "\n"
        cols = line.split("\t")
        #print("line", repr(line))
        #print("cols", repr(cols))
        assert cols == ['tconst', 'parentTconst', 'seasonNumber', 'episodeNumber'], f"actual cols {cols}"
        cur.execute("\n".join([
            "CREATE TABLE imdb_title_basics (",
            "  tconst INTEGER PRIMARY KEY,",
            "  parentTconst INTEGER,",
            "  seasonNumber INTEGER,",
            "  episodeNumber INTEGER",
            ")",
        ]))
        insert_sql_query = f"""INSERT INTO imdb_title_basics({",".join(cols)}) VALUES({",".join(["?" for _ in cols])})"""
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
    con.commit()
    con.close()
    print(f"building {dst} done")
assert os.path.getsize(dst) > 0
con = sqlite3.connect(dst)
cur = con.cursor()
imdb_title_episode_db_count, = cur.execute("select count() from imdb_title_basics").fetchone()
print("imdb_title_episode_db_count:", imdb_title_episode_db_count)


if os.path.exists(movie_names_db_path):
    print("found movie_names_db")
else:
    raise NotImplementedError("TODO create movie_names_db from IMDB")
    # TODO index-compress.py
    # how was this generated? f"index-grouped/index.txt.grouped.{lang_code}"
    # ./opensubtitles_dump_client/num-movies-tvs.py:4:with open("index-grouped/index.txt.grouped.eng") as f:
    # ./opensubtitles_dump_client/repack.py:31:#index_file = f"index-grouped/index.txt.grouped.{lang_code}"
    # ./opensubtitles_dump_client/readme.md:10:Command being timed: "python -u index-compress.py group index.txt index.txt.grouped"
    print("building movie_names_db ...")
    src_con = sqlite3.connect(zipfiles_db_path)
    src_cur = src_con.cursor()
    dst_con = sqlite3.connect(movie_names_db_path)
    dst_cur = dst_con.cursor()
    dst_cur.execute("create table subz_movie_names(name, year, kind)")
    num_done = 0
    for num, zipfile in src_cur.execute("select num, zipfile from subz_zipfiles"):
        dst_cur.execute("insert into subz_zipfiles(num, zipfile) values(?, ?)", (num, zipfile))
        num_done += 1
        if num_done % 10000 == 0:
            print("done", num_done)
    dst_con.commit()
    dst_con.close()
    print("building movie_names_db done")
assert os.path.getsize(movie_names_db_path) > 0
con = sqlite3.connect(movie_names_db_path)
cur = con.cursor()
movie_names_db_count, = cur.execute("select count() from subz_movie_names").fetchone()
print("movie_names_db_count:", movie_names_db_count)


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
