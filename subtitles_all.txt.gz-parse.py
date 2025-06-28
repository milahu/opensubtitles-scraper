#!/usr/bin/env python3

# parse subtitles_all.txt.gz to opensubs-metadata.db

# this runs about 1 hour
# on a 300MB input file
# and creates a 2GB output file



import os
import sys
import time
import gzip
import json
import re
import math
import sqlite3

#import guessit



create_tmp_table = False

debug = False
#debug = True



"""
txt_path=subtitles_all.txt.gz.20240714T173551Z
db_path=$txt_path.db
s=$(stat -c%s "$txt_path")
n=$(sqlite3 "$db_path" "select count(1) from subz_metadata")
echo $s $n | awk '{ print ($1 / $2) }'
"""

# subtitles_all.txt.gz size per subtitle
estimate_bytes_per_sub = 52.0074



# full text search
# https://sqlite.org/fts5.html
create_fts_index = True



debug_sub_number = 0 # invalid
# edge cases:
#debug_sub_number = 6
#debug_sub_number = 277
#debug_sub_number = 4473142
#debug_sub_number = 4531264
#debug_sub_number = 8724405 # empty MovieName
debug_sub_number = 85844 # MovieReleaseName is "\tAppurush" # FIXME
#debug_sub_number = 226696 # MovieReleaseName has "\r" (old mac line format)
#debug_sub_number = 5899534 # SubFormat = "oth"
#debug_sub_number = 7587300 # MovieName has "\t" (only for this sub)
#debug_sub_number = 9211279 # empty SubFormat
#debug_sub_number = 9211278 # empty SubFormat



def has_table(db_path, table_name):
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    try:
        cur.execute(f"select 1 from {table_name} limit 1")
    except sqlite3.OperationalError:
        con.close()
        return False
    con.close()
    return True


deadloop_counter = 0

metadata_db_path = sys.argv[1]
table_name = sys.argv[2]
subtitles_all_txt_gz_path = sys.argv[3]
errfile = sys.argv[4]
dbgfile = sys.argv[5]

table_name_tmp = table_name
if create_tmp_table:
    table_name_tmp = f"{table_name}_tmp"

assert os.path.exists(subtitles_all_txt_gz_path), f"missing input file: {subtitles_all_txt_gz_path!r}"

assert os.path.exists(metadata_db_path) == False, f"existing output file: {metadata_db_path!r}"

estimate_num_subs = round(os.path.getsize(subtitles_all_txt_gz_path) / estimate_bytes_per_sub)

assert has_table(metadata_db_path, table_name) == False, f"output table exists: {table_name!r}"

sqlite_connection = sqlite3.connect(
    metadata_db_path,
    # https://www.sqlite.org/lang_transaction.html#deferred_immediate_and_exclusive_transactions
    # EXCLUSIVE is similar to IMMEDIATE in that a write transaction is started immediately.
    # EXCLUSIVE and IMMEDIATE are the same in WAL mode, but in other journaling modes,
    # EXCLUSIVE prevents other database connections from reading the database while the transaction is underway.
    #isolation_level="EXCLUSIVE",
)
# default: rows are tuples
sqlite_connection.row_factory = sqlite3.Row # rows are dicts
sqlite_cursor = sqlite_connection.cursor()

# default header of ".dump" command
sqlite_cursor.execute("PRAGMA foreign_keys=OFF")

# BEGIN TRANSACTION -> ... -> COMMIT
#sqlite_cursor.execute("BEGIN TRANSACTION")

if has_table(metadata_db_path, table_name_tmp):
    print(f"deleting tmp table {table_name_tmp}")
    sqlite_cursor.execute(f"DROP TABLE {table_name_tmp}")
    sqlite_connection.commit()


col_names = [
    # zcat subtitles_all.txt.gz | head -n1 | tr '\t' '\n' | grep -n . | sed -E 's/^([0-9]+):(.*)$/"\2", # \1/'
    "IDSubtitle", # 1
    "MovieName", # 2
    "MovieYear", # 3
    "LanguageName", # 4
    "ISO639", # 5
    "SubAddDate", # 6
    "ImdbID", # 7
    "SubFormat", # 8
    "SubSumCD", # 9
    "MovieReleaseName", # 10
    "MovieFPS", # 11
    "SeriesSeason", # 12
    "SeriesEpisode", # 13
    "SeriesIMDBParent", # 14
    "MovieKind", # 15
    "URL", # 16
]

len_col_names = len(col_names)

expected_num_cols = len_col_names

idx_IDSubtitle = col_names.index("IDSubtitle")
idx_MovieName = col_names.index("MovieName")
idx_MovieReleaseName = col_names.index("MovieReleaseName")
idx_MovieYear = col_names.index("MovieYear")

# use only these columns
# remove some columns to make the db smaller
#use_col_names = None # use all columns
#use_col_names = col_names # use all columns
use_col_names = [
    "IDSubtitle", # 1
    "MovieName", # 2
    "_MovieNameClean", # derived from MovieName. see get_clean_movie_name
    "MovieYear", # 3
    #"LanguageName", # 4
    "ISO639", # 5
    # needed for last-sub-add-date.txt.sh
    "SubAddDate", # 6
    "ImdbID", # 7
    #"SubFormat", # 8
    "SubSumCD", # 9
    "MovieReleaseName", # 10
    #"MovieFPS", # 11
    "SeriesSeason", # 12
    "SeriesEpisode", # 13
    "SeriesIMDBParent", # 14
    "MovieKind", # 15
    #"URL", # 16
]

def get_clean_movie_name(parsed_cols):
    movie_name = parsed_cols[idx_MovieName]
    return movie_name.replace(
        "'", "" # Don't -> Dont
    )


def get_clean_release_name(parsed_cols):
    """
    reduce release name to title and year
    example:
    a: Dont.Look.Up.2009.BDRip.XviD-FRAGMENT
    b: Dont Look Up 2009
    """
    # shortcut. faster than guessit
    """
    release = "Dont.Look.Up.2009.BDRip.XviD-FRAGMENT"
    year = 2009
    release_title = release.split(str(year), 1)[0] # Dont.Look.Up.
    """
    release = parsed_cols[idx_MovieReleaseName]
    if release == None:
        return None
    year = parsed_cols[idx_MovieYear]
    if year != None:
        release = release.split(str(year), 1)[0]
    return release
    # guessit is waaay too slow
    # guessit makes this script about 100x slower...
    # https://github.com/guessit-io/guessit/issues/389
    """
    parsed = guessit.guessit(col_value)
    if not "title" in parsed:
        return None
    new_value = parsed["title"]
    if "year" in parsed:
        new_value += " " + str(parsed["year"])
    return new_value
    """

derived_col_getters = {
    # derived from MovieName, alternative to MovieReleaseName
    "_MovieNameClean": get_clean_movie_name,
}

# create full text search index for these columns
fts_col_names = [
    "MovieName",
    "_MovieNameClean",
    "MovieReleaseName",
]

use_col_ids = None
if use_col_names and use_col_names != col_names:
    use_col_ids = []
    # use order of use_col_names
    for name in use_col_names:
        try:
            id = col_names.index(name)
        except ValueError:
            # derived column
            id = name
        use_col_ids.append(id)

def filter_cols(parsed_cols, use_col_ids):
    res = []
    # use order of use_col_names
    for id in use_col_ids:
        if isinstance(id, str):
            # id is str -> derived column
            col_value = derived_col_getters[id](parsed_cols)
            res.append(col_value)
            continue
        # id is int
        col_value = parsed_cols[id]
        if id == idx_MovieReleaseName:
            col_value = get_clean_release_name(parsed_cols)
        res.append(col_value)
    return res

# done?
# TODO list -> dict
col_exprs = {
    "IDSubtitle": r"\d{1,9}", # between 1 and 9180517
    "MovieName": r".*",
    "MovieYear": r"\d{0,4}", # can be empty or 0 or 1 or 666 or ...
    "LanguageName": r".*",
    "ISO639": r"([a-z]{2})?", # Language Code
    "SubAddDate": r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", # example: 2006-11-19 04:26:07
    "ImdbID": r"\d*",
    "SubFormat": r"(srt|sub|txt|mpl|smi|ssa|tmp|vtt|oth|)", # TODO more
    "SubSumCD": r"\d+",
    "MovieReleaseName": None, # can contain "\t" -> parse until next valid field
    "MovieFPS": r"\d{1,3}\.\d{3}", # values: 0.000 15.000 23.000 23.976 23.977 23.980 24.000 25.000 29.970 30.000
    "SeriesSeason":r"\d*",
    "SeriesEpisode": r"\d*",
    "SeriesIMDBParent": r"\d*",
    "MovieKind": r"(movie|tv)", # TODO more
    "URL": r"http://www.opensubtitles.org/subtitles/\d+/.*",
}

col_exprs_list = list(col_exprs.values())

# expected count:
# $ ./opensubs.db-count.sh 
# 5719123 opensubtitles_dump_client/index.txt
# actual count with col_exprs_list[0:6]: ID, name, year, languageName, languageCode, date
# $ grep -P '^\d{1,7}\t.+\t\d{4}\t.+\t[a-z]{2}\t\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}' subtitles_all.txt | wc -l
# 5706193
# actual count with col_exprs_list[0:5]: ID, name, year, languageName, languageCode
# $ grep -P '^\d{1,7}\t.+\t\d{4}\t.+\t[a-z]{2}' subtitles_all.txt | wc -l
# 5706223 # max?
# actual count with col_exprs_list[0:4]: ID, name, year, languageName
# $ grep -P '^\d{1,7}\t.+\t\d{4}\t.+' subtitles_all.txt | wc -l
# 5706223 # max?
# actual count with col_exprs_list[0:3]: ID, name, year
# $ grep -P '^\d{1,7}\t.+\t\d{4}' subtitles_all.txt | wc -l
# 5729486 # too much? more than 5719123
# $ diff -u <(grep -P '^\d{1,7}\t.+\t\d{4}\t.+' subtitles_all.txt) <(grep -P '^\d{1,7}\t.+\t\d{4}' subtitles_all.txt) >count.diff
#line_start_expr = r"\t".join(col_exprs_list[0:6])
#line_start_expr = r"^" + r"\t".join(col_exprs_list[0:5]) + r"\t"
#print("line_start_expr", line_start_expr); sys.exit()

# TODO assert
# we assume that the input file is well-formed
# so that ALL lines end with "\n", also the last line
# $ tail -c1 subtitles_all.txt | xxd -ps
# 0a
# $ printf "\n" | xxd -ps
# 0a
line_end_expr = r"\t" + r"\t".join(col_exprs_list[-1:]) + r"\n$"

# get all language names
# $ grep -P '^\d{1,7}\t.+\t\d{4}\t.+\t[a-z]{2}' subtitles_all.txt | cut -d$'\t' -f4 | grep . | sort | uniq >subtitles_all.txt-language-names.txt

# done?
# TODO list -> dict
col_types = {
    "IDSubtitle": int,
    "MovieName": str,
    "_MovieNameClean": str,
    "MovieYear": int,
    "LanguageName": str,
    "ISO639": str,
    "SubAddDate": str,
    "ImdbID": int,
    "SubFormat": str,
    "SubSumCD": int,
    "MovieReleaseName": str,
    "MovieFPS": float,
    "SeriesSeason": int,
    "SeriesEpisode": int,
    "SeriesIMDBParent": int,
    "MovieKind": str,
    "URL": str,
}

col_names_types = []
for col_name in use_col_names:
    col_type = col_types[col_name]
    sql_type = ""
    if col_type == int:
        sql_type = "INTEGER"
    elif col_type == float:
        sql_type = "FLOAT"
    elif col_type == str:
        sql_type = "TEXT"
    sql_extra = ""
    if col_name == "IDSubtitle":
        sql_extra = " PRIMARY KEY"
    col_names_types.append(f"{col_name} {sql_type}{sql_extra}")

create_query = f"CREATE TABLE {table_name_tmp} (\n  "
create_query += ",\n  ".join(col_names_types)
create_query += "\n)"
#print(create_query); raise NotImplementedError("todo")
sqlite_cursor.execute(create_query)

t1 = time.time()
num_lines = 0

def escape_line(line):
    assert line[-1] == "\n", f"line must end with newline. line = {repr(line)}"
    return line[0:-1].replace("\n", "\\n") + "\n"

print(f"parsing {subtitles_all_txt_gz_path} ...")

with (
    gzip.open(subtitles_all_txt_gz_path, "rt") as inf,
    open(dbgfile, "w") as dbgf,
    open(errfile, "w") as errf
):
    # first line is not wrapped
    first_line = inf.readline()
    #print("first_line", repr(first_line))
    expected_cols = len(first_line.split("\t"))
    expected_first_line = "\t".join(col_names) + "\n"
    assert (
        first_line == expected_first_line
    ), (
        f"unexpected first line.\nactual  : {repr(first_line)}\nexpected: {repr(expected_first_line)}"
    )
    buf = []
    #buf_cols = {}
    # TODO why replace? why not insert?
    #insert_query = f"""replace into {table_name_tmp}({",".join(col_names)}) values({",".join(["?"] * len_col_names)})"""
    insert_query = f"""replace into {table_name_tmp}({",".join(use_col_names)}) values({",".join(["?"] * len(use_col_names))})"""
    deadloop_counter_max = 20
    deadloop_counter_raise = 30
    deadloop_counter = 0
    last_sub_number = 0
    num_done = 0

    # offset of the current row (not line)
    file_offset = len(first_line.encode("utf8"))

    #print("inf.readlines")
    #for line in inf.readlines(): # slow
    for line in inf:

        #print("line", repr(line))

        # replace("\r\n", "\n"): convert from windows line format to unix line format
        # replace("\r", "\n"): convert from old mac line format to unix line format
        line = line.replace("\r\n", "\n").replace("\r", "\n")

        buf += [line] # note: keep "\n"

        if debug:
            print("buf2", buf)

        if len(buf) > 1000:
            raise Exception(f"deadloop: buffer is too large at offset {file_offset}")

        # buf contains a full row -> parse columns

        # all columns except MovieReleaseName are well-behaved
        # parse columns before MovieReleaseName
        # parse column MovieReleaseName
        # parse columns after MovieReleaseName

        # strip: remove "\n" at end of string = last column = URL
        raw_cols = "".join(buf).strip().split("\t")

        if debug:
            print("raw_cols", repr(raw_cols))

        if len(raw_cols) < expected_num_cols:
            # add next line to buf
            continue

        # no. field values can contain unescaped "\t"
        # so len(raw_cols) is larger than the actual number of columns
        #if len(raw_cols) > expected_num_cols:
        #    raise ValueError(f"too many columns. actual {len(raw_cols)}. expected {expected_num_cols}. raw_cols {raw_cols}")

        if raw_cols[0] == "7587300" and raw_cols[1] == "":
            # fix one wrong line. remove raw_cols[1]
            print(f"sub {raw_cols[0]}: removing idx 1 of raw_cols {raw_cols}")
            raw_cols = raw_cols[0:1] + raw_cols[2:]

        parsed_cols = []
        parse_failed = False

        def parse_column(idx, raw_col):
            global col_names, col_exprs, col_types, raw_cols, parsed_cols, parse_failed
            col_name = col_names[idx]
            col_expr = col_exprs_list[idx]
            #col_type = col_types[idx]
            col_type = col_types[col_name]
            # re.match: match from start of string
            # re.fullmatch: match from start to end of string
            if re.fullmatch(col_expr, raw_col):
                try:
                    parsed_cols.append(col_type(raw_col))
                except ValueError:
                    if col_type == int and raw_col == "":
                        parsed_cols.append(0)
                    else:
                        raise
            else:
                parse_failed = True

        # parse columns before MovieReleaseName
        for idx in range(0, idx_MovieReleaseName):
            try:
                raw_col = raw_cols[idx]
            except IndexError as exc:
                print(f"FIXME failed to parse line {line!r} at file_offset {file_offset} with error: {exc}")
                t2 = time.time()
                print(f"done {num_done} rows in {t2 - t1:.2f} seconds")
                raise
            parse_column(idx, raw_col)

        if parse_failed:
            errf.write(f"failed to parse columns {parsed_cols} from raw_cols {raw_cols}\n")
            continue

        raw_cols[idx_MovieName] = raw_cols[idx_MovieName].strip()

        len_raw_cols = len(raw_cols)
        num_extra_cols = len_raw_cols - len_col_names

        # parse column MovieReleaseName
        parsed_cols.append("\t".join(raw_cols[idx_MovieReleaseName:(idx_MovieReleaseName + 1 + num_extra_cols)]).strip())

        # parse columns after MovieReleaseName
        for idx in range(idx_MovieReleaseName + 1, len_col_names):
            raw_col = raw_cols[idx + num_extra_cols]
            parse_column(idx, raw_col)

        if parse_failed:
            errf.write(f"failed to parse columns {parsed_cols} from raw_cols {raw_cols}\n")
            continue

        # parse ok -> store in db
        if use_col_ids:
            sqlite_cursor.execute(insert_query, filter_cols(parsed_cols, use_col_ids))
        else:
            # dont filter
            sqlite_cursor.execute(insert_query, parsed_cols)

        #print(parsed_cols[idx_IDSubtitle], repr(parsed_cols[idx_MovieReleaseName]))
        #print("parsed_cols", parsed_cols)
        num_done += 1
        #if num_done >= 10: break # debug

        file_offset += len(line.encode("utf8"))

        # clear buffer for next line
        buf = []

        # show progress
        # TODO show ETA
        if num_done % 100000 == 0:
            done_percent = num_done / estimate_num_subs * 100
            print(f"done {num_done} = {done_percent:.1f}%")

# ^ this takes long, so commit the result
sqlite_connection.commit()

t2 = time.time()
print(f"done {num_done} rows in {t2 - t1:.2f} seconds")
print("output files:")
print(metadata_db_path)
print(errfile)

print("creating indexes ...")

# surprise: with this index "select by movie name" queries stay slow
# so we need both fts-table and index for MovieName
# CREATE INDEX idx_{table_name}_movie_year_lang
#   ON {table_name_tmp} (MovieYear, ISO639);

# make "select by movie name" queries 5x faster
sql_query = f"""
CREATE INDEX idx_{table_name_tmp}_movie_name_year_lang
  ON {table_name_tmp} (MovieName, MovieYear, ISO639)
"""
print(sql_query)
sqlite_cursor.execute(sql_query)

sqlite_connection.commit()

# needed in repack.py to group subs by imdb id and language
sql_query = f"""
CREATE INDEX idx_{table_name}_imdb_lang
  ON {table_name_tmp} (ImdbID, ISO639);
"""
print(sql_query)
sqlite_cursor.execute(sql_query)

sqlite_connection.commit()

if create_tmp_table:
    sqlite_cursor.execute(f"ALTER TABLE {table_name_tmp} RENAME TO {table_name}")
    sqlite_connection.commit()

def create_fts_index_for_column(column_name):
    sql_query = (
        f"CREATE VIRTUAL TABLE {table_name}_fts_{column_name} " +
        f"USING fts5 ({column_name}, content='{table_name}')"
    )
    print(sql_query)
    sqlite_cursor.execute(sql_query)
    # actually populate the index
    # this takes 10 minutes for a 2GB database
    # this makes the db 10% larger (when using all columns)
    sql_query = (
        f"INSERT INTO {table_name}_fts_{column_name} ({table_name}_fts_{column_name}) VALUES ('rebuild')"
    )
    print(sql_query)
    sqlite_cursor.execute(sql_query)
    # to delete the fts index:
    # DROP TABLE subz_metadata_fts_MovieName
    sqlite_connection.commit()

for col_name in fts_col_names:
    create_fts_index_for_column(col_name)

# BEGIN TRANSACTION -> ... -> COMMIT
#sqlite_cursor.execute("COMMIT")

sqlite_connection.commit()
sqlite_connection.close()
