#! /usr/bin/env python3

# FIXME hole between progress 3% and 34%
# done: index.txt.grouped_003.ukr
# progress: 34%
# done: index.txt.grouped_034.eng
# -> bug in pysqlite3?
# see also: index.txt.plot-0-1.hole.png
# gnuplot> set terminal png; set output "index.txt.plot-0-1.hole.png"; plot "index.txt" using 0:1
# $ head -n $((220964 + 3)) index.txt | tail -n6
# 242443 scrubs.s03.e19.my.choosiest.choice.of.all.(2004).hun.1cd.(242443).zip 1542837,303,3784+1542835-
# 242444 lucky.louie.s01.e02.kims.o.(2006).hun.1cd.(242444).zip 1542840,433,3654+1542838-
# 242445 prison.break.s02.e02.otis.(2006).cze.1cd.(242445).zip 1542845,3680,406+1542841-
# 3080253 deiji.(2006).fre.2cd.(3080253).zip 1542845,856,2730+1542846-1542849
# 3080254 lady.in.the.water.(2006).spa.1cd.(3080254).zip 1542856,1938,2147+1542850-
# 3080255 agent.cody.banks.(2003).ara.1cd.(3080255).zip 1542863,482,3603+1542857-
# hole: 3080253 - 242445 = 2837808
# $ sqlite3 -readonly opensubs.db "select num from subz where num between 242443 and 3080255"
# 242443
# 242444
# 242445
# 3080253
# 3080254
# 3080255
# -> hole is also in opensubs.db

# memory usage: 2.3GB at 90% progress
# projected memory usage: 2.6GB at 100% progress

import sys
import re
import json
import pickle
import zlib
import sqlite3
import os
import collections
import math

# TODO check available RAM
# this needs about 1GB of memory (TODO better number)

database = "opensubs.db"


min_sub_number = None
#min_sub_number = 6562515 # resume

# old result in index.txt.outliers
debug_outliers = False

#add_crc = False # fast: TODO time
add_crc = True # slow: TODO time


if add_crc:
    # check if file is readable
    assert os.path.exists(database), f"failed to read file: {database}"


#store_result = False # Maximum RSS: 920MB
store_result = True # Maximum RSS: xxx
# takes lots of RAM. TODO store in sqlite?


def dump_data(data, filename, format):
    if format == "json":
        with open(filename, "w") as f:
            json.dump(data, f)
    elif format == "pickle":
        with open(filename, "wb") as f:
            pickle.dump(data, f)
    else:
        raise Exception(f"unknown format: {format}")

# output options
split_by_lang = True # multiple small files
format = "json" # 75% of index.txt
#format = "pickle" # 60% of index.txt


con = None
if add_crc:
    # extract.py
    con = sqlite3.connect(database)
    con.row_factory = sqlite3.Row
def get_single(num):
    with con:
        cur = con.cursor()
        cur.execute("select * from subz where num = (?)", (num,))
        row = cur.fetchone()
    return row
def get_file(num):
    row = get_single(num)
    File = collections.namedtuple("File", "num name data")
    return File(row["num"], row["name"][22:-1], row["file"])

def print_usage():
    print(f"usage:", file=sys.stderr)
    print(f"python {sys.argv[0]} group index.txt index.txt.out", file=sys.stderr)
    sys.exit(1)

def fatal_error(msg):
    print(f"fatal error: {msg}", file=sys.stderr)
    sys.exit(1)

# https://docs.python.org/3/library/binascii.html
# https://stackoverflow.com/questions/35205702/calculating-crc16-in-python
import binascii
def crc16_xmodem(data: bytes, init_value=0):
  return binascii.crc_hqx(data, init_value)


# https://stackoverflow.com/questions/46258499/how-to-read-the-last-line-of-a-file-in-python
def read_n_to_last_line(filename, n = 1):
    """Returns the nth before last line of a file (n=1 gives last line)"""
    num_newlines = 0
    with open(filename, 'rb') as f:
        try:
            f.seek(-2, os.SEEK_END)    
            while num_newlines < n:
                f.seek(-2, os.SEEK_CUR)
                if f.read(1) == b'\n':
                    num_newlines += 1
        except OSError:
            f.seek(0)
        last_line = f.readline().decode()
    return last_line


def compress_positions(positions):
    """
    compress absolute to relative positions

    in most cases, the second range starts at the first position,
    but in theory, all ranges can start at the first position

    store the first position as prefix
    """
    first_pos = math.inf
    ranges = []
    for pos_range in positions.split("+"):
        m = re.fullmatch(r"(\d+)(?:(,\d+,\d+)|(-)(\d*))?", pos_range)
        assert m, f"no match in pos_range: {pos_range}"
        range_start = int(m.group(1))
        range_rest = m.group(2) or m.group(3) # (,\d+,\d+) or (-)
        range_end = m.group(4)
        first_pos = min(first_pos, range_start)
        ranges.append((range_start, range_rest, range_end))
    result = []
    for range_start, range_rest, range_end in ranges:
        if range_end:
            result.append(f"{range_start-first_pos}{range_rest}{int(range_end)-first_pos}")
        else:
            # first range is done here
            # range_rest = f",{start_ofs},{end_ofs}"
            result.append(f"{range_start-first_pos}{range_rest}")
    return f"{first_pos}:" + "+".join(result)


def parse_positions(string, page_size, reserved_space):
    # TODO test
    # these values are stored in the database header
    #page_size, reserved_space = 4096, 0
    """
    positions = parse_positions(sub_positions, page_size, reserved_space)
    print("positions", positions)
    zip_file_content = b""
    with open(datbase_file, "rb") as f:
        for start, end in positions:
            f.seek(start)
            zip_file_content += f.read(end - start)
    """
    lowest_page_idx, rest = string.split(":", 2)
    lowest_page_idx = int(lowest_page_idx)
    ranges = rest.split("+")
    first_range = ranges.pop(0) # 12,422,3666
    first_page_idx_rel, start_ofs_rel, end_ofs_rel = first_range.split(",")
    first_page_idx = lowest_page_idx + int(first_page_idx_rel)
    page_ofs = first_page_idx * page_size
    start_ofs = page_ofs + int(start_ofs_rel)
    end_ofs = page_ofs + int(end_ofs_rel)
    assert start_ofs < end_ofs
    result = [(start_ofs, end_ofs)] # first page
    for range_str in ranges:
        start_page_idx_rel, end_page_idx_rel = range_str.split("-")
        start_page_idx_rel = int(start_page_idx_rel)
        start_page_idx = lowest_page_idx + start_page_idx_rel
        if end_page_idx_rel == "":
            end_page_idx = first_page_idx - 1
        else:
            end_page_idx = lowest_page_idx + int(end_page_idx_rel)
        for page_idx in range(start_page_idx, end_page_idx + 1):
            start_ofs = page_idx * page_size
            # 4 = 4 bytes at end of page for "next page pointer"
            end_ofs = start_ofs + page_size - 4 - reserved_space
            result.append((start_ofs, end_ofs))
    return result


def main():
    if len(sys.argv) != 4:
        print_usage()
    action = sys.argv[1]
    infile = sys.argv[2]
    outfile = sys.argv[3]
    if action != "group":
        print_usage()
    if infile == outfile:
        fatal_error("infile and outfile must be different")

    #crc_file_path = f"{outfile}.crc-cache"
    crc_file_path = f"{database}.crc-cache"

    crc_cache = dict()
    with open(crc_file_path, "r") as f:
        for line in f.readlines():
            num, crc = line.strip().split(" ")
            crc_cache[int(num)] = int(crc)

    crc_file = open(crc_file_path, "a")

    print(f"crc_file_path: {crc_file_path}")

    # last line
    line = read_n_to_last_line(infile)
    print("last line:", line.strip())
    line_chunks = line.strip().split(" ")
    last_sub_number = int(line_chunks[0])
    print("last sub_number:", last_sub_number)

    with open(infile) as f:
        i = 1
        langs = dict()
        progress_percent_last = 0
        for line in f.readlines():
            #print(f"line {i}: {repr(line)}")
            #sys.stdout.write("."); sys.stdout.flush()
            i += 1
            #if i > 1000: break # debug
            line_chunks = line.strip().split(" ")
            #assert len(line_chunks) == 4
            #sub_number, sub_offset, sub_size, filename = line_chunks
            assert len(line_chunks) == 3
            sub_number, filename, sub_positions = line_chunks

            sub_number_int = int(sub_number)

            if min_sub_number and sub_number_int < min_sub_number:
                continue

            progress_percent = round(sub_number_int / last_sub_number * 100)
            if progress_percent != progress_percent_last:
                print(f"progress: {progress_percent}%")
                # write partial result
                if store_result and progress_percent % 10 == 0:
                    outfile_part = f"{outfile}_{progress_percent:03d}"
                    if split_by_lang:
                        for lang in langs:
                            outfile_lang = f"{outfile_part}.{lang}"
                            dump_data(langs[lang], outfile_lang, format)
                            print(f"done: {outfile_lang}")
                    else:
                        dump_data(langs, outfile_part, format)
                        print(f"done: {outfile_part}")

            filename_chunks = filename.split(".")

            # death.to.smoochy.(2002).slv.1cd.(10).zip
            movie_name_parts = filename_chunks[0:-5] # death.to.smoochy
            movie_year_parens = filename_chunks[-5] # (2002)
            sub_lang = filename_chunks[-4] # slv
            sub_numparts = filename_chunks[-3] # 1cd
            sub_number_parens = filename_chunks[-2] # (10)
            sub_extension = filename_chunks[-1] # zip

            if (
                movie_year_parens == "()" and
                re.fullmatch(r"\((?:\d{4}|0|)\)", filename_chunks[-6])
            ):
                if debug_outliers:
                    print(f"sub {sub_number} @ {progress_percent}%: extra empty parens after year: {filename}")
                # extra empty parens after year
                # 1208.east.of.bucharest.(2006).().ita.1cd.(3157715).zip
                # 1208.east.of.bucharest.(2006).().rum.1cd.(3541881).zip
                # note: this movie title is repeated many many times
                # $ grep -F '1208.east.of.bucharest.(2006)' index.txt | wc -l
                # 4535
                movie_year_parens = filename_chunks[-6]
                movie_name_parts = filename_chunks[0:-6]

            # antitrust.(2001).slv.1cd.(6).zip

            assert sub_extension == "zip", f"sub {sub_number}: bad filename: {filename}"
            assert re.fullmatch(r"\(\d+\)", sub_number_parens), f"sub {sub_number}: bad filename: {filename}" # (10)

            year_regex = r"\((?:\d{0,4})\)"

            if re.fullmatch(year_regex, sub_lang):
                if debug_outliers:
                    print(f"sub {sub_number} @ {progress_percent}%: sub_lang is missing: {filename}")
                # sub_lang is missing: ongbak.the.thai.warrior.(2003).1cd.(94998).zip
                # sub_lang is missing: the.walt.disney.company.and.mcdonalds.present.the.american.teacher.awards.(1995).1cd.(142000).zip
                # sub_lang is missing, default to english. TODO verify
                movie_year_parens = sub_lang
                sub_lang = "eng"

            assert re.fullmatch(r"[a-z]{3}", sub_lang), f"sub {sub_number}: bad filename: {filename}" # slv

            assert re.fullmatch(year_regex, movie_year_parens), f"sub {sub_number}: bad filename: {filename}" # (2002)
            if debug_outliers:
                if movie_year_parens == "()":
                    print(f"sub {sub_number} @ {progress_percent}%: year is empty: {filename}")
                    # frostbite.().pob.1cd.(92027).zip
                    # FIXME: year is empty: 1208.east.of.bucharest.(2006).().pol.1cd.(3553155).zip
                elif len(movie_year_parens) != 6:
                    print(f"sub {sub_number} @ {progress_percent}%: year is invalid: {filename}")
                    # no.movie.title.yet.(click.on.correct.subtitles.and.insert.imdb.link).(0).dan.6cd.(79262).zip
                    # transgressoes_leves.(1).pob.1cd.(6488168).zip
                    # justin.biebers.ultimate.bullshit.collection.(666).eng.1cd.(6567608).zip

            movie_name = " ".join(movie_name_parts)
            movie_year = movie_year_parens[1:-2]
            movie_name_year = movie_name + " " + movie_year_parens
            sub_number_filename = sub_number_parens[1:-1]

            assert sub_number == sub_number_filename, f"sub {sub_number}: bad filename: {filename}, sub_number: {sub_number}, sub_number_filename: {sub_number_filename}"

            #assert movie_name != "", f"sub {sub_number}: bad filename: {filename}"
            # movie name can be empty
            if debug_outliers:
                if movie_name == "":
                    print(f"sub {sub_number} @ {progress_percent}%: empty movie name: {filename}")
                    # empty movie name: .(1971).pol.1cd.(3193794).zip

            #sub_offset = int(sub_offset)
            #sub_size = int(sub_size)

            if re.fullmatch(r"\d+cd", sub_numparts): # 1cd (str)
                # note: can be "0cd"
                # .().0cd.(3336993).zip
                sub_numparts = int(sub_numparts[0:-2]) # 1 (int)
            else:
                if debug_outliers:
                    print(f"sub {sub_number} @ {progress_percent}%: no 'cd' prefix in sub_numparts: {filename}")

            zipfile_crc = None
            if add_crc:
                if sub_number_int in crc_cache:
                    # cache hit
                    zipfile_crc = crc_cache[sub_number_int]
                else:
                    # cache miss
                    zipfile = get_file(sub_number_int)
                    zipfile_crc = crc16_xmodem(zipfile.data)
                    crc_file.write(f"{sub_number} {zipfile_crc}\n")

            compact_format = True

            sub_positions = compress_positions(sub_positions)

            if store_result:

                if compact_format:
                    lang_movie_entry = [
                        sub_number_int,
                        #sub_lang, # debug
                        sub_numparts,
                        #sub_number,
                        #sub_offset,
                        #sub_size,
                        sub_positions,
                        #filename, # debug
                        #zipfile_crc,
                    ]
                    if add_crc:
                        lang_movie_entry.append(zipfile_crc)
                    for value in lang_movie_entry:
                        assert value != ""
                else:
                    # verbose format for debugging
                    lang_movie_entry = dict(
                        id=sub_number_int,
                        #lang=sub_lang, # debug
                        parts=sub_numparts,
                        #relid=sub_number,
                        offset=sub_offset,
                        size=sub_size,
                        sub_positions=sub_positions,
                        #name=filename, # debug
                        #zipfile_crc=zipfile_crc,
                    )
                    if add_crc:
                        lang_movie_entry["zipfile_crc"] = zipfile_crc

                if not sub_lang in langs:
                    langs[sub_lang] = dict()

                if not movie_name_year in langs[sub_lang]:
                    langs[sub_lang][movie_name_year] = list()

                langs[sub_lang][movie_name_year].append(lang_movie_entry)

            progress_percent_last = progress_percent

        print()

        if store_result:

            if split_by_lang:
                for lang in langs:
                    outfile_lang = f"{outfile}.{lang}"
                    dump_data(langs[lang], outfile_lang, format)
                    print(f"done: {outfile_lang}")
            else:
                dump_data(langs, outfile, format)
                print(f"done: {outfile}")

if __name__ == "__main__":
    result = main()
    sys.exit(result or 0)
