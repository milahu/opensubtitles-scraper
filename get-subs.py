#! /usr/bin/env python3

# get subtitles for a video file
# from local subtitle providers


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
data_dir = os.path.dirname(__file__)


def main():
    config_path = f"{data_dir}/local-subtitle-providers.json"
    with open(config_path) as f:
        config = json.load(f)
    lang_ISO639 = "en"
    video_path = sys.argv[1]
    print("video_path", video_path)
    video_filename = os.path.basename(video_path)
    print("video_filename", video_filename)
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


def get_movie_subs(video_path, video_parsed, lang_ISO639, config):
    video_path_base, video_path_extension = os.path.splitext(video_path)
    # one database for metadata: 1.6GB
    meta_con = sqlite3.connect(f"{data_dir}/subtitles_all.db")
    meta_cur = meta_con.cursor()
    # multiple databases for zipfiles: 24GB for english subs
    sql_query = "SELECT IDSubtitle FROM metadata WHERE MovieName LIKE ? AND MovieYear = ? AND ISO639 = ? AND SubSumCD = 1"
    sql_args = (video_parsed.get("title"), video_parsed.get("year"), lang_ISO639)
    for num, in meta_cur.execute(sql_query, sql_args):
        for provider in config["providers"]:
            # check range of num
            if num < provider["num_range_from"] or provider["num_range_to"] < num:
                # num is out of range
                #print(f"""local provider {provider["id"]}: num is out of range""")
                continue
            #print(f"""local provider {provider["id"]}: num is in range""")
            if not "db_con" in provider:
                db_path = provider["db_path"]
                if db_path.startswith("~/"):
                    db_path = os.environ["HOME"] + db_path[1:]
                elif db_path.startswith("$HOME/"):
                    db_path = os.environ["HOME"] + db_path[5:]
                provider["db_con"] = sqlite3.connect(db_path)
            if not "db_cur" in provider:
                # cache the cursor for faster lookup of similar nums
                provider["db_cur"] = provider["db_con"].cursor()
            sql_query = (
                f"""SELECT {provider["zipfiles_zipfile_column"]} """
                f"""FROM {provider["zipfiles_table"]} """
                f"""WHERE {provider["zipfiles_num_column"]} = {num}"""
            )
            #print("sql_query", sql_query)
            row = provider["db_cur"].execute(sql_query).fetchone()
            if not row:
                #print(f"""local provider {provider["id"]}: num not found""")
                continue
            # found
            #print(f"""found sub {num} in local provider {provider["id"]}""")
            zip_content, = row
            extract_sub(zip_content, video_path_base, num, lang_ISO639)
            # found zipfile -> dont search other providers
            break


def extract_sub(zip_content, video_path_base, num, lang_ISO639):
    with zipfile.ZipFile(io.BytesIO(zip_content)) as zip_file:
        for zipinfo in zip_file.infolist():
            if zipinfo.filename.endswith("/"):
                continue
            filename = zipinfo.filename
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
                # note: chardet can return wrong encodings
                # https://github.com/chardet/chardet/issues/279
                chardet_result = chardet.detect(sub_content)
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
