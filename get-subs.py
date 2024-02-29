#! /usr/bin/env python3

# get subtitles for a video file
# from local subtitle providers

# TODO search for episode
# TODO allow passing name/year/season/episode/imdb-id as extra arguments
# TODO get subs for multiple files, example: 1 season of a tv show
# TODO remove ads from subs. usually first and last frames in sub. see ads.txt
# for ads, reduce frame length to zero, so the ads are still visible in the txt files
# FIXME use fuzzy search. example: Borat 2 Subsequent Moviefilm -> Borat Subsequent Moviefilm
# FIXME chardet.detect is slow - TODO try https://pypi.org/project/faust-cchardet/
# FIXME opensubs-metadata.db is slow
# FIXME escape % in title. example: 97% Owned (2012)
# TODO allow multiple video files per call
# TODO optimize queries for multiple similar video files
# usually: all episodes of a tv show season


import sys
import os
import sqlite3
import zipfile
import io
import json
import glob

# requirements
import platformdirs
import guessit
import charset_normalizer


# global state
data_dir = None


def expand_path(path):
    global data_dir
    if path == None:
        return path
    if path.startswith("~/"):
        path = os.environ["HOME"] + path[1:]
    elif path.startswith("$HOME/"):
        path = os.environ["HOME"] + path[5:]
    return os.path.join(data_dir, path)


def main():
    global data_dir
    # relative paths are relative to data_dir
    # on linux: $HOME/.config/subtitles
    data_dir = platformdirs.user_config_dir("subtitles")
    if not os.path.exists(data_dir):
        raise Exception(f"missing data_dir: {repr(data_dir)}")
    config_path = f"{data_dir}/local-subtitle-providers.json"
    if not os.path.exists(config_path):
        raise Exception(f"missing config_path: {repr(config_path)}")
    with open(config_path) as f:
        config = json.load(f)
    # TODO use default from locale in os.environ["LANG"]
    lang_ISO639 = "en"
    if len(sys.argv) != 2 or not os.path.exists(sys.argv[1]):
        print_usage()
        return
    video_path = sys.argv[1]
    print("video_path", video_path)
    # note: video_path does not need to exist
    os.makedirs(os.path.dirname(video_path), exist_ok=True)
    video_filename = os.path.basename(video_path)
    #print("video_filename", video_filename)
    video_parsed = guessit.guessit(video_filename)
    str_list = []
    print("video_parsed", video_parsed)

    providers = []
    for provider in config["providers"]:
        if provider.get("enabled") == False:
            continue
        if "db_path" in provider:
            providers.append(provider)
            continue
        # expand "shard" provider
        shard_size = provider.get("shard_size")
        db_path_base = expand_path(provider.get("db_path_base"))
        db_path_format = provider.get("db_path_format")
        # TODO? use regex to parse shard_id
        #db_path_glob = provider.get("db_path_glob")
        #db_path_shard_id_regex = provider.get("db_path_shard_id_regex")
        get_shard_id = None
        if db_path_base and db_path_format:
            db_path_glob = db_path_base + db_path_format.replace("{shard_id}", "*")
            if db_path_format.endswith("/{shard_id}xxx.db"):
                get_shard_id = lambda db_path: int(os.path.basename(db_path)[:-6])
            else:
                raise NotImplementedError
        else:
            raise NotImplementedError
        for db_path in glob.glob(db_path_glob):
            shard_id = get_shard_id(db_path)
            num_range_from = shard_id * shard_size
            provider_2 = dict(provider)
            provider_2["id"] = provider["id"] + f"/shard-{shard_id}"
            provider_2["db_path"] = db_path
            provider_2["num_range_from"] = num_range_from
            provider_2["num_range_to"] = num_range_from + shard_size - 1
            providers.append(provider_2)
    config["providers"] = providers

    return get_movie_subs(video_path, video_parsed, lang_ISO639, config)


def print_usage():
    print("usage:", file=sys.stderr)
    #argv0 = "get-subs.py"
    argv0 = os.path.basename(sys.argv[0])
    print(f"{argv0} Some.Movie.2000.720p.mp4", file=sys.stderr)


def get_movie_subs(video_path, video_parsed, lang_ISO639, config):
    global data_dir
    video_path_base, video_path_extension = os.path.splitext(video_path)
    # one database for metadata: 1.6GB
    #print(f"""metadata: getting connection""")
    # FIXME opensubs-metadata.db is slow
    # add index for (MovieName, MovieYear)
    # add full-text-search index for MovieName
    # add index for MovieYear
    metadata_db_path = expand_path(config["subtitles_metadata_db_path"])
    assert os.path.exists(metadata_db_path), f"no such file: {metadata_db_path}"
    print(f"opening database {metadata_db_path}")
    metadata_con = sqlite3.connect(metadata_db_path)
    metadata_cur = metadata_con.cursor()
    # multiple databases for zipfiles: 24GB for english subs
    sql_query = None
    sql_args = None
    if video_parsed.get("type") == "movie":
        sql_query = (
            "SELECT IDSubtitle "
            "FROM subz_metadata "
            "WHERE MovieName LIKE ? "
            "AND MovieYear = ? "
            "AND ISO639 = ? "
            "AND SubSumCD = 1 "
            "AND MovieKind = 'movie' "
            #"AND ImdbID = 12345"
        )
        sql_args = (
            video_parsed.get("title"),
            video_parsed.get("year"),
            lang_ISO639,
        )
    elif video_parsed.get("type") == "episode":
        # TODO lookup via IMDB
        # solve ambiguity: movie covers? plots?
        # covers/plots are not in https://www.kaggle.com/datasets/ashirwadsangwan/imdb-dataset
        # -> online ambiguity soliver? = compare some urls
        # titleType = 'tvSeries'
        # sqlite3 imdb/title.basics.db "select * from imdb_title_basics where primaryTitle like 'Euphoria' and titleType = 'tvSeries' AND genres LIKE '%Drama%';" -line
        # https://www.imdb.com/title/tt23863502/
        # https://www.imdb.com/title/tt8772296/ # this is it: 8772296
        # titleType = 'tvEpisode'
        # sqlite3 imdb/title.episode.db "select * from imdb_title_basics where parentTconst = 8772296 and seasonNumber = 1 and episodeNumber = 1 limit 1;" -line
        # parentTconst = 8772296
        # tconst = 8135530
        # sqlite3 imdb/title.basics.db "select * from imdb_title_basics where tconst = 8135530;" -line
        # TODO
        series_imdb_parent = 8772296
        sql_query = (
            "SELECT IDSubtitle "
            "FROM subz_metadata "
            "WHERE "
            #"MovieName LIKE ? "
            "SeriesIMDBParent = ? "
            "AND "
            "SeriesSeason = ? "
            "AND "
            "SeriesEpisode = ? "
            "AND "
            "ISO639 = ? "
            "AND "
            "SubSumCD = 1 "
            "AND "
            "MovieKind = 'tv' "
            #"AND SeriesIMDBParent = 12345"
            #"AND ImdbID = 12345"
        )
        sql_args = (
            #video_parsed.get("title"),
            series_imdb_parent,
            #video_parsed.get("episode_title"),
            video_parsed.get("season"),
            video_parsed.get("episode"),
            lang_ISO639,
        )
    else:
        raise Exception(f"""unknown video type: {repr(video_parsed.get("type"))}""")

    nums = []
    def format_query(sql_query, sql_args=None):
        if not sql_args:
            return sql_query
        # replace "?" in query with args
        parts = sql_query.split(" ? ")
        result = ""
        for idx, part in enumerate(parts):
            result += part
            if idx < len(sql_args):
                result += f" {repr(sql_args[idx])} "
        return result
    print(f"""metadata: getting results for query:""", format_query(sql_query, sql_args))
    for num, in metadata_cur.execute(sql_query, sql_args):
        nums.append(num)

    for provider in config["providers"]:
        #if provider.get("enabled") == False:
        #    continue
        provider_lang = provider.get("lang", "*")
        if provider_lang != "*":
            # TODO allow multiple languages for one provider
            if provider_lang != lang_ISO639:
                continue
        def filter_num(num):
            num_range_from = provider.get("num_range_from", 0)
            if num_range_from == 0:
                return True
            num_range_to = provider.get("num_range_to", 0)
            if num_range_to == 0:
                return True
            return num_range_from <= num and num <= num_range_to
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
            db_path = expand_path(provider.get("db_path"))

            # use sqlite ATTACH? - no. number is limited to 10 files
            # https://stackoverflow.com/questions/30292367/sqlite-append-two-tables-from-two-databases-that-have-the-exact-same-schema
            # https://sqlite.org/cgi/src/doc/reuse-schema/doc/shared_schema.md

            assert os.path.exists(db_path), f"no such file: {db_path}"

            provider["db_con"] = sqlite3.connect(db_path)

            # TODO? build external index
            # https://sqlite.org/forum/forumpost/0ed07b9626
            # https://stackoverflow.com/questions/19379761/how-to-setup-index-for-virtual-table-in-sqlite
            # pysqlite3.connect is always readonly
            #provider["db_con"] = pysqlite3.connect(db_path)

            print(f"""local provider {provider["id"]}: opening database {db_path}""")

            # no: sqlite3.OperationalError: no such access mode: readonly
            # TODO encode path to URI
            #db_uri = f"file:{db_path}?mode=readonly"
            #provider["db_con"] = sqlite3.connect(db_uri, uri=True)

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
            # TODO guess filename_encoding for each file
            #filename_encoding = charset_normalizer.from_bytes(sub_content).best().encoding
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
            sub_encoding = charset_normalizer.from_bytes(sub_content).best().encoding
            if sub_encoding not in {"ascii", "utf_8"}:
                # recode sub_content to utf8
                try:
                    # bytes -> str -> bytes
                    sub_content = sub_content.decode(sub_encoding).encode("utf8")
                except UnicodeDecodeError as error:
                    print(f"output {repr(sub_path)} warning: failed to convert to utf8 from {sub_encoding}: {error}")
            sub_filename = os.path.basename(sub_path)
            print(f"output {repr(sub_filename)} from {repr(filename)} ({encoding})")
            with open(sub_path, "wb") as sub_file:
                sub_file.write(sub_content)
            break # stop after first file
            # TODO write multiple files


main()
