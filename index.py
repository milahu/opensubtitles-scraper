# find zip files in sqlite database
# zip file header in hex: 504b0304140000000800
# TODO verify. maybe shorter?
# find zip-files/ -type f | head -n100 | while read f; do cat "$f" | head -c16 | xxd -p; done
# verify:
# find zip-files/ -type f | head -n100 | while read f; do cat "$f" | head -c16 | xxd -p; done | grep -v ^504b0304140000000800

import sys

def hexdump(bytes):
  line = ""
  for i, b in enumerate(bytes):
    if i % 16 != 0:
      line += " "
      if i % 8 == 0:
        line += "   "
    if i % 16 == 0 and i > 0:
      print(line)
      line = ""
    line += f"{b:02x}"
  if line != "":
    print(line)

import struct
import math

import sqlite3_types

with open("opensubs.db", "rb") as f:
    pos = 0
    f.seek(0)
    file_header = sqlite3_types.FileHeader()
    f.readinto(file_header)
    #print(file_header.header_string)
    #print(file_header.page_size)

    # page_size: Must be a power of two between 512 and 32768 inclusive,
    # or the value 1 representing a page size of 65536.
    if file_header.page_size == 1:
        file_header.page_size = 65536
    else:
        page_size_base = math.log(file_header.page_size, 2)
        if int(page_size_base) != page_size_base:
            raise Exception(f"page size must be a power of 2: {file_header.page_size}")
        if file_header.page_size < 512 or 32768 < file_header.page_size:
            raise Exception(f"page size must be in range (512, 32768): {file_header.page_size}")

sys.exit()


# brute force: search zip files by zip file header
with open("opensubs.db", "rb") as f:
    pos = 0
    while True:
        f.seek(pos)
        chunk = f.read(10)
        if chunk == b"\x50\x4b\x03\x04\x14\x00\x00\x00\x08\x00":
            # found start of zip archive
            start = pos
            print(f"start: {start}")
            # TODO get size
            before_len = 128
            f.seek(pos - before_len)
            chunk = f.read(before_len)
            print("bytes before zip:")
            hexdump(chunk)
            break
        pos += 1

sys.exit()

# sqlite get raw offset of row in database file

# https://www.sqlite.org/fileformat.html
# 2.1. Record Format
# The record format makes extensive use of the variable-length integer or varint representation of 64-bit signed integers defined above.
# A record contains a header and a body, in that order. The header begins with a single varint which determines the total number of bytes in the header. The varint value is the size of the header in bytes including the size varint itself. Following the size varint are one or more additional varints, one per column. These additional varints are called "serial type" numbers and determine the datatype of each column.
# 
# BLOB:
# Serial Type: N≥12 and even
# Content Size: (N-12)/2
# Meaning: Value is a BLOB that is (N-12)/2 bytes in length.

# https://stackoverflow.com/questions/32903465/reading-raw-data-from-an-sqlite-table-in-python
# https://github.com/ck123pm/sqliteRepair

#import sqlite3

# see brute-force solution in
# /home/user/src/opensubtitles-dump/index.sh
# /home/user/src/opensubtitles-dump/index.txt

# todo: ideally trace sqlite read operations
# to get the byte offset of a selected blob file
# this is much faster than index.sh (binary-grep.sh using xdelta3)

# index size is 48707 bytes for 1000 entries
# extrapolated index size for 6.5M entries: 300 MBytes
# todo: group the index by language
# example:
# 1229 27934724 19807 into.the.sun.(2005).fin.1cd.(1229).zip
# -> language: fin

# index size is 569243 bytes for 9999 entries
# extrapolated index size for 6.5M entries: 300 MBytes
# 569243 / 9999 * 6.5E6 / 1E6 = 370 MBytes

# compress index by grouping?
# group by movie name and sub language

import sys
import re
import json
import pickle

def print_usage():
    print(f"usage:", file=sys.stderr)
    print(f"python {sys.argv[0]} group index.txt index.txt.out", file=sys.stderr)
    sys.exit(1)

def fatal_error(msg):
    print(f"fatal error: {msg}", file=sys.stderr)
    sys.exit(1)

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
    with open(infile) as f:
        i = 1
        langs = dict()
        for line in f.readlines():
            #print(f"line {i}: {repr(line)}")
            i += 1
            #if i > 10: break # debug
            line_chunks = line.strip().split(" ")
            assert len(line_chunks) == 4
            sub_id, sub_offset, sub_size, filename = line_chunks
            filename_chunks = filename.split(".")

            # death.to.smoochy.(2002).slv.1cd.(10).zip
            movie_name_parts = filename_chunks[0:-5] # death.to.smoochy
            movie_year_parens = filename_chunks[-5] # (2002)
            sub_lang = filename_chunks[-4] # slv
            sub_numparts = filename_chunks[-3] # 1cd
            sub_relid_parens = filename_chunks[-2] # (10)
            sub_extension = filename_chunks[-1] # zip

            # antitrust.(2001).slv.1cd.(6).zip

            assert sub_extension == "zip"
            assert re.fullmatch(r"\(\d+\)", sub_relid_parens) # (10)
            assert re.fullmatch(r"[a-z]{3}", sub_lang) # slv
            assert re.fullmatch(r"\(\d{4}\)", movie_year_parens) # (2002)

            movie_name = " ".join(movie_name_parts)
            movie_year = movie_year_parens[1:-2]
            movie_name_year = movie_name + " " + movie_year_parens
            sub_relid = sub_relid_parens[1:-1]

            assert sub_relid == sub_id
            assert movie_name != ""

            sub_id = int(sub_id)
            sub_offset = int(sub_offset)
            sub_size = int(sub_size)

            if re.fullmatch(r"\d+cd", sub_numparts): # 1cd
                sub_numparts = int(sub_numparts[0:-2])

            if True:
                # compact
                lang_movie_entry = [
                    sub_id,
                    #sub_lang, # debug
                    sub_numparts,
                    #sub_relid,
                    sub_offset,
                    sub_size,
                    #filename, # debug
                ]
                for value in lang_movie_entry:
                    assert value != ""
            else:
                # verbose, debug
                lang_movie_entry = dict(
                    id=sub_id,
                    #lang=sub_lang, # debug
                    parts=sub_numparts,
                    #relid=sub_relid,
                    offset=sub_offset,
                    size=sub_size,
                    #name=filename, # debug
                )

            if not sub_lang in langs:
                langs[sub_lang] = dict()

            if not movie_name_year in langs[sub_lang]:
                langs[sub_lang][movie_name_year] = list()

            langs[sub_lang][movie_name_year].append(lang_movie_entry)

        def dump(data, filename, format):
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

        if split_by_lang:
            for lang in langs:
                outfile_lang = f"{outfile}.{lang}"
                dump(langs[lang], outfile_lang, format)
                print(f"done: {outfile_lang}")
        else:
            dump(langs, outfile, format)
            print(f"done: {outfile}")

if __name__ == "__main__":
    result = main()
    sys.exit(result or 0)
