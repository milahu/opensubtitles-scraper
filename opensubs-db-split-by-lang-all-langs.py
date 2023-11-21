#!/usr/bin/env python3

# FIXME get lang from subtitles_all.db == opensubs-metadata.db

raise NotImplementedError("FIXME get lang from subtitles_all.db == opensubs-metadata.db")

import sys
import os
import re
import sqlite3
import csv

if len(sys.argv) != 3:
  print("usage:")
  print("  python3 opensubs-db-split-by-lang.py opensubs.db opensubs-by-lang")
  print("  (this takes some hours)")
  sys.exit(1)

src_db_path = sys.argv[1]
dst_db_dir = sys.argv[2]

assert os.path.exists(src_db_path) == True, f"error: missing input file: {src_db_path}"

assert os.path.exists(dst_db_dir) == False, f"error: output dir exists: {dst_db_dir}"

# simple integrity check of the input file
assert os.path.getsize(src_db_path) == 136812494848, f"error: wrong size of input file: {src_db_path}"

# takes about 1 hour to get a hash of opensubs.db
print("note: not checking integrity of the input file")
print("  expected file hashes:")
print("    sha256: ca0a2becfbdf5a2e914d18559fe4c1eb84dd21a70ddc474ad180a71d2444bd31")
print("    bt2rh:  406e5bb482777d3ae9ad1c9fd3569132d39eda525726ea5da637fba393bd2f34")
print("    tiger:  0eb2d696dfed60665f170b5c4864367d25e8fe8db7994b03")
print("    sha1:   f3339885d25ce480528efb5c01d2785f7dd12972")
print("    md5:    6e9c09573bbda0a178f420c57014ca2b")

src_con = sqlite3.connect(src_db_path)

os.makedirs(dst_db_dir, exist_ok=True)

# three letter language codes
# https://en.wikipedia.org/wiki/ISO_639
# https://en.wikipedia.org/wiki/List_of_ISO_639-2_codes
# https://github.com/noumar/iso639
# see also subtitles_all.txt.gz-parse.py -> ISO639

# https://github.com/noumar/iso639/raw/main/iso639/iso639-2.tsv
iso639_2_tsv_path = "iso639-2.tsv"

with open(iso639_2_tsv_path) as f:
    valid_iso639_2_codes = set(map(lambda x: x[0], list(csv.reader(f, delimiter='\t'))[1:]))

valid_iso639_2_codes.add("und") # undefined

class Dst():
    db_path = None
    cur = None
    con = None
    def __init__(self, dst_db_dir, lang):
        self.db_path = f"{dst_db_dir}/{lang}.db"
        print(f"creating {self.db_path}")
        self.con = sqlite3.connect(self.db_path)
        self.cur = self.con.cursor()
        """
        # same schema as the source datbase
        self.con.execute(
            "CREATE TABLE subz (\n"
            "  num INTEGER PRIMARY KEY,\n"
            "  name TEXT,\n"
            "  file BLOB\n"
            ")\n"
        )
        """
        # different schema than the source datbase
        # same as in new-subs-archive.py
        # different name:
        #   a: 1|attachment; filename="alien.3.(1992).eng.2cd.(1).zip"|PK
        #   b: 1|alien.3.(1992).eng.2cd|PK
        table_name = "zipfiles"
        sqlite_page_size = 4096 # default value, but make it explicit
        self.cur.executescript(f"PRAGMA page_size = {sqlite_page_size}; VACUUM;")
        self.cur.execute("PRAGMA count_changes=OFF") # better performance
        self.cur.execute(
            f"CREATE TABLE {table_name} (\n"
            f"  num INTEGER PRIMARY KEY,\n"
            f"  name TEXT,\n" # name is mostly useless. correct metadata of num is stored separately
            f"  content BLOB\n"
            f")"
        )
        self.insert_query = f"INSERT INTO {table_name} VALUES (?, ?, ?)"

dst_by_lang = dict()

# 94998|attachment; filename="ongbak.the.thai.warrior.(2003).1cd.(94998).zip"|PK
# this subtitle also has no language in metadata
#   $ sqlite3 subtitles_all.db "select ISO639, LanguageName from metadata where IdSubtitle = 94998"
#   |
# lets check the zipfile
#   $ ./extract.py -s 94998 -p test-zipfile; cd test-zipfile; unzip *.zip
#   $ chardetect *.srt
#   Ong-Bak.2003.Kh.srt: Windows-1252 with confidence 0.6378745823003126
#   $ iconv -f Windows-1252 -t utf8 Ong-Bak.2003.Kh.srt >Ong-Bak.2003.Kh.utf8.srt 
#   $ grep -E '^[^0-9]{2,}' Ong-Bak.2003.Kh.utf8.srt | tail -n +20 | head -n5
#   eyIgRbeKns,g;CIBreTARBHsgÇ nig Gug)ak;
#   CaGnkkarBarbdimakr edIm,IsuxmalPaBkúngPUmirbs;eyIg
#   kúngBiFIenH…
#   KWrMlwkeyIgfa…
#   enA7éf¶eTót eyIgnwg…
# okay, the file is trash... or i used a wrong encoding
# TODO what is "Kh"? a language? km-KH = Khmer = Cambodia = km = khm
#   hello world -> សួស្តី​ពិភពលោក។ = suostei piphoplok
#   $ file -i Ong-Bak.2003.Kh.srt
#   Ong-Bak.2003.Kh.srt: application/x-subrip; charset=unknown-8bit
#   $ python -c 'import magic; p = "Ong-Bak.2003.Kh.srt"; f = open(p, "rb"); s = f.read(1000); f.close(); print(magic.detect_from_content(s))'
#   FileMagic(mime_type='application/x-subrip', encoding='iso-8859-1', name='SubRip, ISO-8859 text, with CRLF, NEL line terminators')
#   $ iconv -f iso-8859-1 -t utf8 Ong-Bak.2003.Kh.srt >Ong-Bak.2003.Kh.utf8.srt
# https://stackoverflow.com/questions/436220/how-to-determine-the-encoding-of-text
# https://gist.github.com/FilipDominec/912b18147842ed5de7adbf3fab1413c9#file-wrong_charset_detection-py
# decode-file-with-all-encodings.py
# no. i really tried, but i have no idea what encoding this is
# how many subtitles with no language?
#   $ sqlite3 subtitles_all.db "select count(1) from metadata where ISO639 = '' and IDSubtitle < 9180519"
#   20

nums_with_undefined_language = set([
    # sqlite3 subtitles_all.db "select IDSubtitle from metadata where ISO639 = ''" | sort -n | xargs printf '%s,\n'
    277,
    278,
    280,
    1276,
    18386,
    62140,
    64270,
    94998,
    113659,
    115769,
    138768,
    142000,
    3254371,
    3254741,
    3254743,
    3803069,
    4275094,
    4275095,
    4275096,
    6253398,
    9211278,
    9211279,
])

# FIXME invalid lang '()' in num=3336993 name='attachment; filename=".().0cd.(3336993).zip"'
# $ sqlite3 opensubs-metadata.db "select * from subz_metadata where IDSubtitle = 3336993 limit 1;" 
# 3336993|Journey to the Center of the Earth|2008|Brazilian|pb|2008-09-25 19:45:52|1231575|srt|1|jttocte.SCREENER.XviD-COALiTiON|23.98|0|0|0|movie|http://www.opensubtitles.org/subtitles/3336993/journey-to-the-center-of-the-earth-pb
# pb = por = Portuguese/Brazilian

# FIXME invalid lang '()' in num=3338296 name='attachment; filename=".().0cd.(3338296).zip"'
# $ sqlite3 opensubs-metadata.db "select * from subz_metadata where IDSubtitle = 3338296 limit 1;" 
# 3338296|Lakeview Terrace|2008|Spanish|es|2008-09-28 07:03:43|947802|srt|1||29.97|0|0|0|movie|http://www.opensubtitles.org/subtitles/3338296/lakeview-terrace-es
# es = spa = Spanish

# FIXME invalid lang 'spn' in num=TODO name='attachment; filename="TODO"'
# what is lang "spn"? spanish?
#   $ sqlite3 subtitles_all.db "select * from metadata where ISO639 = 'spn' LIMIT 1" | wc -l
#   0
# anyway, filenames are not reliable
# so we must use subtitles_all.db == opensubs-metadata.db

# no, this takes too long
#num_total = src_con.execute(f"SELECT count(1) FROM subz")[0]
# note: IDSubtitle is not steady. 2837807 sub ids are missing between 242445 and 3080253
# see also opensubtitles_dump_client/outliers.md
# TODO get total number of subs
#num_total = 1234
#print("num_total", type(num_total), repr(num_total))

for num, name, file in src_con.execute(f"SELECT num, name, file FROM subz ORDER BY num ASC"):
    name_lang = name.split(".")[-4]
    # FIXME get lang from subtitles_all.db == opensubs-metadata.db
    lang = name_lang
    if num in nums_with_undefined_language:
        # verify name. now name_lang must be the movie year like "(2000)" or "(0)" or "()"
        if re.match(r"\([0-9]*\)", name_lang) == None:
            print(f"FIXME invalid name_lang {repr(name_lang)} in num={num} name={repr(name)}")
        # undetermined language = undefined language
        # https://stackoverflow.com/questions/9952667/there-is-a-code-for-language-english-spanish-etc-not-defined
        lang = "und"
    if not lang in valid_iso639_2_codes:
        print(f"FIXME invalid lang {repr(lang)} in num={num} name={repr(name)}")
    if not lang in dst_by_lang:
        dst_by_lang[lang] = Dst(dst_db_dir, lang)
    dst = dst_by_lang[lang]

    # cut name:
    #   a: 1|attachment; filename="alien.3.(1992).eng.2cd.(1).zip"|PK
    #   b: 1|alien.3.(1992).eng.2cd|PK
    name_suffix = f'.({num}).zip"'
    if name[0:22] == 'attachment; filename="' and name.endswith(name_suffix):
        name = name[22:(-1 * len(name_suffix))]
    else:
        print(f"FIXME invalid name {repr(name)} in num={num}")

    # insert
    dst.cur.execute(dst.insert_query, (num, name, file))

    if num % 100000 == 0:
        #progress_percent = num / num_total * 100
        #print(f"done {num} of {num_total} = {progress_percent:.2f}%")
        print(f"done {num}")
        if False:
            # todo?
            for lang in dst_by_lang:
                dst = dst_by_lang[lang]
                print(f"writing {dst.db_path}")
                dst.con.commit()

src_con.close()

for lang in dst_by_lang:
    dst = dst_by_lang[lang]
    dst.con.commit()
    dst.con.close()
    # make it read-only
    os.chmod(dst.db_path, 0o444)
    print(f"done {dst.db_path}")
