#! /usr/bin/env python3

# get subtitles for a video file
# from local subtitle providers

# FIXME chardet.detect is slow
# FIXME subtitles_all.db is slow


import sys
import os
import sqlite3
import zipfile
import io
import json

# requirements
import guessit
import magic
import chardet


# TODO better
#data_dir = os.path.dirname(__file__)
data_dir = os.environ["HOME"] + "/.config/subtitles"


def main():
    config_path = f"{data_dir}/local-subtitle-providers.json"
    with open(config_path) as f:
        config = json.load(f)
    lang_ISO639 = "en"
    if len(sys.argv) != 2 or not os.path.exists(sys.argv[1]):
        print_usage()
        return
    video_path = sys.argv[1]
    print("video_path", video_path)
    video_filename = os.path.basename(video_path)
    #print("video_filename", video_filename)
    video_parsed = guessit.guessit(video_filename)
    str_list = []
    print("video_parsed", video_parsed)
    if video_parsed.get("type") == "movie":
        return get_movie_subs(video_path, video_parsed, lang_ISO639, config)
        # note: if we put year in parens, year is ignored
        str_list += [f"""{video_parsed.get("title")} {video_parsed.get("year")}"""]
    raise NotImplementedError
    #elif video_parsed.get("type") == "episode":
    #    str_list += [f"""{video_parsed.get("title")} S{video_parsed.get("season"):02d}E{video_parsed.get("episode"):02d}"""]
    #    str_list += [f"""{video_parsed.get("title")} {video_parsed.get("season")}x{video_parsed.get("episode")}"""]
    #for s in str_list:
    #    print(s)


def print_usage():
    print("usage:", file=sys.stderr)
    #argv0 = "get-subs.py"
    argv0 = os.path.basename(sys.argv[0])
    print(f"{argv0} Some.Movie.2000.720p.mp4", file=sys.stderr)


def get_movie_subs(video_path, video_parsed, lang_ISO639, config):
    video_path_base, video_path_extension = os.path.splitext(video_path)
    # one database for metadata: 1.6GB
    #print(f"""metadata: getting connection""")
    # FIXME subtitles_all.db is slow
    # add index for (MovieName, MovieYear)
    # add full-text-search index for MovieName
    # add index for MovieYear
    meta_con = sqlite3.connect(f"{data_dir}/subtitles_all.db")
    meta_cur = meta_con.cursor()
    # multiple databases for zipfiles: 24GB for english subs
    sql_query = "SELECT IDSubtitle FROM metadata WHERE MovieName LIKE ? AND MovieYear = ? AND ISO639 = ? AND SubSumCD = 1"
    sql_args = (video_parsed.get("title"), video_parsed.get("year"), lang_ISO639)
    nums = []
    #print(f"""metadata: getting results for query:""", sql_query)
    for num, in meta_cur.execute(sql_query, sql_args):
        nums.append(num)
    for provider in config["providers"]:
        def filter_num(num):
            return provider["num_range_from"] <= num and num <= provider["num_range_to"]
        provider_nums = []
        rest_nums = []
        for num in nums:
            if filter_num(num):
                provider_nums.append(num)
            else:
                rest_nums.append(num)
        nums = rest_nums
        if not provider_nums:
            #print(f"""local provider {provider["id"]}: num is out of range""")
            continue
        #print(f"""local provider {provider["id"]}: getting {len(provider_nums)} nums""")
        if not "db_con" in provider:
            db_path = provider["db_path"]
            if db_path.startswith("~/"):
                db_path = os.environ["HOME"] + db_path[1:]
            elif db_path.startswith("$HOME/"):
                db_path = os.environ["HOME"] + db_path[5:]
            #print(f"""local provider {provider["id"]}: getting connection""")
            provider["db_con"] = sqlite3.connect(db_path)
        if not "db_cur" in provider:
            # cache the cursor for faster lookup of similar nums
            provider["db_cur"] = provider["db_con"].cursor()
        sql_query = (
            f"""SELECT {provider["zipfiles_num_column"]}, """
            f"""{provider["zipfiles_zipfile_column"]} """
            f"""FROM {provider["zipfiles_table"]} """
            f"""WHERE {provider["zipfiles_num_column"]} IN """
            f"""({", ".join(map(str, provider_nums))})"""
        )
        #print("sql_query", sql_query)
        #print(f"""local provider {provider["id"]}: getting results for query:""", sql_query)
        for num, zip_content in provider["db_cur"].execute(sql_query):
            # found
            #print(f"""found sub {num} in local provider {provider["id"]}""")
            extract_sub(zip_content, video_path_base, num, lang_ISO639)
            # found zipfile -> dont search other providers
        #print(f"""local provider {provider["id"]}: done""")


def extract_sub(zip_content, video_path_base, num, lang_ISO639):
    #print(f"extracting sub {num}")
    with zipfile.ZipFile(io.BytesIO(zip_content)) as zip_file:
        #print(f"extracting sub {num}: done opening zip file")
        for zipinfo in zip_file.infolist():
            if zipinfo.filename.endswith("/"):
                continue
            filename = zipinfo.filename
            #print(f"extracting sub {num}: filename: {repr(filename)}")
            # zip metadata is often encoded with cp437
            for encoding in ["cp437", "iso-8859-1"]:
                try:
                    # '├⌐'.encode("cp437").decode("utf8") == 'é'
                    filename = filename.encode(encoding).decode("utf8")
                except UnicodeEncodeError:
                    continue
                break
            if filename == "":
                filename = "empty_filename.srt"
            _, ext = os.path.splitext(filename)
            if ext == ".nfo":
                continue
            if ext == ".dlsubc":
                # num = 4062524
                ext = ".srt"
            if ext == ".txt":
                # mpv ignores subs with .txt extension
                # https://github.com/mpv-player/mpv/issues/4144
                ext = ".sub"
            # simply return the first subtitle file
            # TODO handle multiple files
            # 2% of all subs are multipart: 2cd/3cd/4cd/...
            # some subs have extra hearing-impaired subs
            # zero-pad num to fix sort order
            # currently, the last num has 7 digits (9521948)
            # 1000 new subs every day -> 8 digits will last for 250 years
            # (99999999 - 9521948) / 1000 / 365 = 250
            num_width = 8
            num_padded = str(num).rjust(num_width, "0")
            sub_path = f"{video_path_base}.{lang_ISO639}.{num_padded}{ext}"
            sub_content = zip_file.read(zipinfo)
            # recode sub_content to utf8
            #print(f"extracting sub {num}: magic.detect_from_content")
            magic_result = magic.detect_from_content(sub_content)
            encoding = magic_result.encoding
            def recode_content(sub_content, encoding):
                try:
                    # bytes -> str -> bytes
                    sub_content = sub_content.decode(encoding).encode("utf8")
                except UnicodeDecodeError as error:
                    print(f"output {repr(sub_path)} warning: failed to convert to utf8 from {encoding}: {error}")
                return sub_content
            if encoding not in {"us-ascii", "utf-8", "unknown-8bit", "binary"}:
                #print(f"output {repr(sub_path)} encoding {encoding} from libmagic")
                sub_content = recode_content(sub_content, encoding)
            elif encoding == "unknown-8bit":
                # libmagic failed to find encoding -> try chardet
                # bug? 0000445: file/libmagic fails to detect cp1252 encoding
                # https://bugs.astron.com/view.php?id=445
                # note: chardet can return wrong encodings
                # https://github.com/chardet/chardet/issues/279
                # FIXME chardet.detect is slow
                # example subs: 4248010 4590955
                # result: cp1252 == Windows-1252
                #print(f"extracting sub {num}: chardet.detect ...")
                chardet_result = chardet.detect(sub_content)
                #print(f"extracting sub {num}: chardet.detect done")
                encoding = chardet_result["encoding"]
                if not encoding in {"ascii", "utf-8"}:
                    #print(f"output {repr(sub_path)} encoding {encoding} from chardet")
                    sub_content = recode_content(sub_content, encoding)
            print(f"output {repr(sub_path)} from {repr(filename)} ({encoding})")
            with open(sub_path, "wb") as sub_file:
                sub_file.write(sub_content)
            break # stop after first file
            # TODO write multiple files


main()
