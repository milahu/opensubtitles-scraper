#!/usr/bin/env python3

import os
import sys
import time
import gzip
import json
import re
import math
import sqlite3

debug_sub_number = 0 # invalid
# corner cases:
#debug_sub_number = 6
#debug_sub_number = 277
#debug_sub_number = 4473142
#debug_sub_number = 4531264
#debug_sub_number = 8724405 # empty MovieName
debug_sub_number = 85844 # MovieReleaseName is "\tAppurush" # FIXME
#debug_sub_number = 226696 # MovieReleaseName has "\r" (old mac line format)
#debug_sub_number = 5899534 # SubFormat = "oth"
#debug_sub_number = 7587300 # MovieName has "\t" (only for this sub)


deadloop_counter = 0

# TODO auto-detect deadloops
# = when buf_cols.get("IDSubtitle") is constant over many iterations

lines_limit = math.inf
#lines_limit = 10 * 1000 # debug

# TODO write result to sqlite database
# compact json file has 1.4GB which is not practical to hold in memory

#infile = "subtitles_all.txt.gz" # slow
infile = "subtitles_all.txt"
#outfile = "subtitles_all.txt.gz-parse-result.txt"
metadata_db_path = "opensubs-metadata.db"
if len(sys.argv) == 2:
    metadata_db_path = sys.argv[1]
    print("metadata_db_path:", repr(metadata_db_path))
dbgfile = "subtitles_all.txt.gz-parse-debug.txt"
errfile = "subtitles_all.txt.gz-parse-errors.txt"

# TODO raise error if metadata_db_path exists

assert os.path.exists(metadata_db_path) == False, "error: output file exists"

sqlite_connection = sqlite3.connect(metadata_db_path)
# default: rows are tuples
sqlite_connection.row_factory = sqlite3.Row # rows are dicts
sqlite_cursor = sqlite_connection.cursor()

col_names = [
    # head -n1 subtitles_all.txt | tr '\t' '\n' | grep -n . | sed -E 's/^([0-9]+):(.*)$/"\2", # \1/'
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

idx_IDSubtitle = col_names.index("IDSubtitle")
idx_MovieName = col_names.index("MovieName")
idx_MovieReleaseName = col_names.index("MovieReleaseName")

col_exprs = [
    r"\d{1,7}", # 1 = IDSubtitle. between 1 and 9180517
    r".*", # 2 = MovieName
    r"\d{0,4}", # 3 = MovieYear. can be empty or 0 or 1 or 666 or ...
    r".*", # 4 = LanguageName
    r"([a-z]{2})?", # 5 = ISO639 = LanguageCode
    r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", # 6 = SubAddDate. example: 2006-11-19 04:26:07
    r"\d*", # 7 = ImdbID
    r"(srt|sub|txt|mpl|smi|ssa|tmp|vtt|oth)", # 8 = SubFormat # TODO more
    r"\d+", # 9 = SubSumCD
    None, # r".*", # 10 = MovieReleaseName. can contain "\t" -> parse until next valid field
    r"\d{1,3}\.\d{3}", # 11 = MovieFPS. values: 0.000 15.000 23.000 23.976 23.977 23.980 24.000 25.000 29.970 30.000
    r"\d*", # 12 = SeriesSeason
    r"\d*", # 13 = SeriesEpisode
    r"\d*", # 14 = SeriesIMDBParent
    r"(movie|tv)", # 15 = MovieKind # TODO more
    r"http://www.opensubtitles.org/subtitles/\d+/.*", # 16 = URL
]

# expected count:
# $ ./opensubs.db-count.sh 
# 5719123 opensubtitles_dump_client/index.txt
# actual count with col_exprs[0:6]: ID, name, year, languageName, languageCode, date
# $ grep -P '^\d{1,7}\t.+\t\d{4}\t.+\t[a-z]{2}\t\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}' subtitles_all.txt | wc -l
# 5706193
# actual count with col_exprs[0:5]: ID, name, year, languageName, languageCode
# $ grep -P '^\d{1,7}\t.+\t\d{4}\t.+\t[a-z]{2}' subtitles_all.txt | wc -l
# 5706223 # max?
# actual count with col_exprs[0:4]: ID, name, year, languageName
# $ grep -P '^\d{1,7}\t.+\t\d{4}\t.+' subtitles_all.txt | wc -l
# 5706223 # max?
# actual count with col_exprs[0:3]: ID, name, year
# $ grep -P '^\d{1,7}\t.+\t\d{4}' subtitles_all.txt | wc -l
# 5729486 # too much? more than 5719123
# $ diff -u <(grep -P '^\d{1,7}\t.+\t\d{4}\t.+' subtitles_all.txt) <(grep -P '^\d{1,7}\t.+\t\d{4}' subtitles_all.txt) >count.diff
#line_start_expr = r"\t".join(col_exprs[0:6])
line_start_expr = r"^" + r"\t".join(col_exprs[0:5]) + r"\t"
#print("line_start_expr", line_start_expr); sys.exit()

# we assume that the input file is well-formed
# so that ALL lines end with "\n", also the last line
# $ tail -c1 subtitles_all.txt | xxd -ps
# 0a
# $ printf "\n" | xxd -ps
# 0a
line_end_expr = r"\t" + r"\t".join(col_exprs[-1:]) + r"\n$"

# get all language names
# $ grep -P '^\d{1,7}\t.+\t\d{4}\t.+\t[a-z]{2}' subtitles_all.txt | cut -d$'\t' -f4 | grep . | sort | uniq >subtitles_all.txt-language-names.txt

col_types = [
    int, # 1 = IDSubtitle
    str, # 2 = MovieName
    int, # 3 = MovieYear
    str, # 4 = LanguageName
    str, # 5 = ISO639 = LanguageCode
    str, # 6 = SubAddDate. example: 2006-11-19 04:26:07
    int, # 7 = ImdbID
    str, # 8 = SubFormat # TODO more
    int, # 9 = SubSumCD
    str, # 10 = MovieReleaseName
    float, # 11 = MovieFPS. default: 0.000. other values: 23.976
    int, # 12 = SeriesSeason
    int, # 13 = SeriesEpisode
    int, # 14 = SeriesIMDBParent
    str, # 15 = MovieKind # TODO more
    str, # 16 = URL
]

col_names_types = []
for idx, col_name in enumerate(col_names):
    col_type = col_types[idx]
    sql_type = ""
    if col_type == int:
        sql_type = "INTEGER"
    elif col_type == float:
        sql_type = "FLOAT"
    elif col_type == str:
        sql_type = "TEXT"
    sql_extra = ""
    if idx == 0:
        sql_extra = "PRIMARY KEY"
    col_names_types.append(f"{col_name} {sql_type} {sql_extra}")


create_query = f"""create table if not exists subz_metadata({",".join(col_names_types)})"""
#print(create_query)
sqlite_cursor.execute(create_query)


if not os.path.exists(infile):
    print(f"error: no such file: {infile}")
    print(f"hint:\ngzip -d -k -f {infile}.gz")
    sys.exit(1)

t1 = time.time()
num_lines = 0

def escape_line(line):
    assert line[-1] == "\n", f"line must end with newline. line = {repr(line)}"
    return line[0:-1].replace("\n", "\\n") + "\n"

print(f"parsing {infile} ...")

with (
    #gzip.open(infile, "r") as inf, # slow
    open(infile, "r") as inf,
    #open(outfile, "w") as outf,
    open(dbgfile, "w") as dbgf,
    open(errfile, "w") as errf
):
    # first line is not wrapped
    first_line = inf.readline()
    #print("first_line", repr(first_line))
    #outf.write(first_line + "\n")
    expected_cols = len(first_line.split("\t"))
    expected_first_line = "\t".join(col_names) + "\n"
    assert (
        first_line == expected_first_line
    ), (
        f"unexpected first line.\nactual  : {repr(first_line)}\nexpected: {repr(expected_first_line)}"
    )
    buf = []
    #buf_cols = {}
    insert_query = f"""replace into subz_metadata({",".join(col_names)}) values({",".join(["?"] * len_col_names)})"""
    deadloop_counter_max = 20
    deadloop_counter_raise = 30
    deadloop_counter = 0
    last_sub_number = 0
    num_done = 0

    #print("inf.readlines")
    #for line in inf.readlines(): # slow
    for line in inf:

        #print("line", repr(line))

        # replace("\r\n", "\n"): convert from windows line format to unix line format
        # replace("\r", "\n"): convert from old mac line format to unix line format
        line = line.replace("\r\n", "\n").replace("\r", "\n")

        if False:
            if last_sub_number == buf_cols.get("IDSubtitle"):
                deadloop_counter += 1
            else:
                deadloop_counter = 0
            last_sub_number = buf_cols.get("IDSubtitle")
            is_debug = deadloop_counter > deadloop_counter_max
            if deadloop_counter > deadloop_counter_raise:
                raise Exception("deadloop")

        #len_buf_cols = len(buf_cols)

        is_line_start = re.search(line_start_expr, line)
        #print("is_line_start", is_line_start)
        #print("buf", buf)
        #print("buf_cols", buf_cols)

        is_line_end = re.search(line_end_expr, line)

        if is_line_start:
            buf = []
            # error: buffer was not cleared
            #errf.write("non-empty buffer: " + repr(buf) + "\n")

        buf += [line] # note: keep "\n"

        if not is_line_end:
            continue

        # buf contains a full row -> parse columns

        # all columns except MovieReleaseName are well-behaved
        # parse columns before MovieReleaseName
        # parse column MovieReleaseName
        # parse columns after MovieReleaseName

        # strip: remove "\n" at end of string. not part of column URL
        raw_cols = "".join(buf).strip().split("\t")

        if raw_cols[0] == "7587300" and raw_cols[1] == "":
            # fix one wrong line. remove raw_cols[1]
            print(f"sub {raw_cols[0]}: removing idx 1 of raw_cols {raw_cols}")
            raw_cols = raw_cols[0:1] + raw_cols[2:]

        #parsed_cols = {}
        parsed_cols = []
        parse_failed = False

        def parse_column(idx, raw_col):
            global col_names, col_exprs, col_types, raw_cols, parsed_cols, parse_failed
            col_name = col_names[idx]
            col_expr = col_exprs[idx]
            col_type = col_types[idx]
            # re.match: match from start of string
            # re.fullmatch: match from start to end of string
            if re.fullmatch(col_expr, raw_col):
                try:
                    #parsed_cols[col_name] = col_type(raw_col)
                    parsed_cols.append(col_type(raw_col))
                except ValueError:
                    if col_type == int and raw_col == "":
                        #parsed_cols[col_name] = 0
                        parsed_cols.append(0)
                    else:
                        raise
            else:
                parse_failed = True
                #parsed_cols[col_name] = ""
                #parsed_cols[f"_col{idx}"] = raw_col

        # parse columns before MovieReleaseName
        for idx in range(0, idx_MovieReleaseName):
            raw_col = raw_cols[idx]
            parse_column(idx, raw_col)

        if parse_failed:
            errf.write(f"failed to parse columns {parsed_cols} from raw_cols {raw_cols}\n")
            continue

        raw_cols[idx_MovieName] = raw_cols[idx_MovieName].strip()

        len_raw_cols = len(raw_cols)
        num_extra_cols = len_raw_cols - len_col_names

        # parse column MovieReleaseName
        col_name = "MovieReleaseName"
        #parsed_cols[col_name] = "\t".join(raw_cols[idx_MovieReleaseName:(idx_MovieReleaseName + 1 + num_extra_cols)])
        parsed_cols.append("\t".join(raw_cols[idx_MovieReleaseName:(idx_MovieReleaseName + 1 + num_extra_cols)]).strip())

        # parse columns after MovieReleaseName
        for idx in range(idx_MovieReleaseName + 1, len_col_names):
            raw_col = raw_cols[idx + num_extra_cols]
            parse_column(idx, raw_col)

        if parse_failed:
            errf.write(f"failed to parse columns {parsed_cols} from raw_cols {raw_cols}\n")
            continue

        # parse ok -> store in db
        sqlite_cursor.execute(insert_query, parsed_cols)

        #print(parsed_cols[idx_IDSubtitle], repr(parsed_cols[idx_MovieReleaseName]))
        #print("parsed_cols", parsed_cols)
        num_done += 1
        #if num_done >= 10: break # debug

        # show progress
        if num_done % 100000 == 0:
            print(f"done {num_done}")

# DROP INDEX idx_movie_name_year;

sqlite_cursor.execute("""
    CREATE INDEX idx_movie_name_year_lang
    ON subz_metadata (MovieName, MovieYear, ISO639)
""")

sqlite_connection.commit()
sqlite_connection.close()

t2 = time.time()
print(f"done {num_done} lines in {t2 - t1:.2f} seconds")
print("output files:")
#print(outfile)
print(metadata_db_path)
print(errfile)
