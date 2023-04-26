#! /usr/bin/env python3

# based on index.py and index-compress.py

import sys
import re
import json
import pickle
import zlib
import sqlite3
import os
import collections
import math

#zipfiles_db_path = "opensubs-zipfiles.db"
#zipfiles_parsed_db_path = "opensubs-zipfiles-parsed.db"

metadata_db_path = sys.argv[1]
zipfile_names_table_name = sys.argv[2]
zipfile_names_parsed_table_name = sys.argv[3]

table_name = zipfile_names_parsed_table_name
table_name_tmp = f"{table_name}_tmp"

#min_sub_number = None
#min_sub_number = 6562515 # resume

# adding checksums for zipfiles does not make sense
# because the zipfiles are dynamic
# inside the zipfiles, the nfo files contain 2 variables:
# - download count
# - nfo file creation time
# the only constants are the subtitle files inside the zip files
# the nfo files have MD5 hashes of the subtitle files
# these MD5 hashes are valid only for the original file encoding
# and change when recoding file contents to utf8
#add_crc = True


def main():

    assert has_table(metadata_db_path, zipfile_names_table_name), f"error: missing input table: {zipfile_names_table_name}"

    assert has_table(metadata_db_path, zipfile_names_parsed_table_name) == False, f"error: output table exists: {zipfile_names_parsed_table_name}"

    con = sqlite3.connect(metadata_db_path)
    # default: rows are tuples
    #con.row_factory = sqlite3.Row # rows are dicts
    cur = con.cursor()

    print(f"creating table {table_name_tmp}")
    cur.execute(f"""
        CREATE TABLE {table_name_tmp} (
            num INTEGER PRIMARY KEY,
            name TEXT,
            year INTEGER,
            lang TEXT,
            parts INTEGER,
            errors TEXT
        )
    """)

    num_done = 0
    sql_query = f"SELECT num, zipfile_name FROM {zipfile_names_table_name}"
    #if min_sub_number:
    #        sql_query += f" WHERE num >= {min_sub_number}"

    #print(f"looping {zipfile_names_table_name}")
    for sub_number, zipfile_name in cur.execute(sql_query):
        #print("sub_number, zipfile_name", sub_number, zipfile_name)
        filename_chunks = zipfile_name.split(".")
        #print("filename_chunks", filename_chunks)

        # death.to.smoochy.(2002).slv.1cd.(10).zip
        movie_name_parts = filename_chunks[0:-5] # death.to.smoochy
        movie_year_parens = filename_chunks[-5] # (2002)
        sub_lang = filename_chunks[-4] # slv
        sub_numparts = filename_chunks[-3] # 1cd
        sub_number_parens = filename_chunks[-2] # (10)
        sub_extension = filename_chunks[-1] # zip

        parse_errors = []

        if (
            movie_year_parens == "()" and
            re.fullmatch(r"\((?:\d{4}|0|)\)", filename_chunks[-6])
        ):
            parse_errors.append("extra empty parens after year")
            # extra empty parens after year
            # 1208.east.of.bucharest.(2006).().ita.1cd.(3157715).zip
            # 1208.east.of.bucharest.(2006).().rum.1cd.(3541881).zip
            # note: this movie title is repeated many many times
            # $ grep -F '1208.east.of.bucharest.(2006)' index.txt | wc -l
            # 4535
            movie_year_parens = filename_chunks[-6]
            movie_name_parts = filename_chunks[0:-6]

        # antitrust.(2001).slv.1cd.(6).zip

        assert sub_extension == "zip", f"sub {sub_number}: bad zipfile_name: {zipfile_name}"
        assert re.fullmatch(r"\(\d+\)", sub_number_parens), f"sub {sub_number}: bad zipfile_name: {zipfile_name}" # (10)

        year_regex = r"\((?:\d{0,4})\)"

        if re.fullmatch(year_regex, sub_lang):
            parse_errors.append("missing sub_lang")
            # sub_lang is missing: ongbak.the.thai.warrior.(2003).1cd.(94998).zip
            # sub_lang is missing: the.walt.disney.company.and.mcdonalds.present.the.american.teacher.awards.(1995).1cd.(142000).zip
            # sub_lang is missing, default to english. TODO verify
            movie_year_parens = sub_lang
            sub_lang = "eng"

        assert re.fullmatch(r"[a-z]{3}", sub_lang), f"sub {sub_number}: bad zipfile_name: {zipfile_name}" # slv

        assert re.fullmatch(year_regex, movie_year_parens), f"sub {sub_number}: bad zipfile_name: {zipfile_name}" # (2002)
        if movie_year_parens == "()":
            parse_errors.append("empty year")
            # frostbite.().pob.1cd.(92027).zip
            # FIXME: year is empty: 1208.east.of.bucharest.(2006).().pol.1cd.(3553155).zip
        elif len(movie_year_parens) != 6:
            parse_errors.append("invalid year")
            # no.movie.title.yet.(click.on.correct.subtitles.and.insert.imdb.link).(0).dan.6cd.(79262).zip
            # transgressoes_leves.(1).pob.1cd.(6488168).zip
            # justin.biebers.ultimate.bullshit.collection.(666).eng.1cd.(6567608).zip

        movie_name = " ".join(movie_name_parts)
        movie_year = movie_year_parens[1:-1]
        #movie_name_year = movie_name + " " + movie_year_parens
        sub_number_filename = int(sub_number_parens[1:-1])

        assert sub_number == sub_number_filename, f"sub {sub_number}: bad zipfile_name: {zipfile_name}, sub_number: {sub_number}, sub_number_filename: {sub_number_filename}"

        #assert movie_name != "", f"sub {sub_number}: bad zipfile_name: {zipfile_name}"
        # movie name can be empty
        if movie_name == "":
            parse_errors.append("empty movie name")
            # empty movie name: .(1971).pol.1cd.(3193794).zip

        #assert movie_name != "", f"sub {sub_number}: bad zipfile_name: {zipfile_name}"
        # movie name can be empty
        if movie_name != movie_name.strip():
            parse_errors.append("spaced movie name")
            movie_name = movie_name.strip()

        #sub_offset = int(sub_offset)
        #sub_size = int(sub_size)

        if re.fullmatch(r"\d+cd", sub_numparts): # 1cd (str)
            # note: can be "0cd"
            # .().0cd.(3336993).zip
            sub_numparts = int(sub_numparts[0:-2]) # 1 (int)
        else:
            parse_errors.append("no 'cd' prefix in sub_numparts")

        sql_query = f"insert into subz_zipfiles_parsed(num, name, year, lang, parts, errors) values(?, ?, ?, ?, ?, ?)"
        sql_data = (sub_number, movie_name, movie_year, sub_lang, sub_numparts, ", ".join(parse_errors))
        cur.execute(sql_query, sql_data)

        num_done += 1
        if num_done % 100000 == 0:
            print("done", num_done)

    print("creating index subz_zipfiles_parsed.idx_lang")
    cur.execute("""
        CREATE INDEX idx_lang
        ON subz_zipfiles_parsed (lang)
    """)

    print("creating index subz_zipfiles_parsed.idx_name_year_lang")
    cur.execute("""
        CREATE INDEX idx_name_year_lang
        ON subz_zipfiles_parsed (name, year, lang)
    """)

    con.commit()
    con.close()

if __name__ == "__main__":
    sys.exit(main() or 0)
