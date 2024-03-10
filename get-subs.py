#! /usr/bin/env python3



# get subtitles for a video file
# from local subtitle providers

# to expose this over an http server, see docs/lighttpd.conf

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
import pathlib
import types
import re

# requirements
import guessit
import charset_normalizer



# with recode, this is 2x slower
# ideally recode once and cache the result
recode_sub_content_to_utf8 = False

# if is_cgi: unpack_zipfiles = False
unpack_zipfiles = True



# global state
data_dir = None
is_cgi = False



def show_help_cgi():
    request_url = (
        os.environ.get("REQUEST_SCHEME") + "://" +
        os.environ.get("HTTP_HOST") +
        os.environ.get("REQUEST_URI")
    )
    print("Status: 200")
    print("Content-Type: text/plain")
    print()

    curl = "curl"
    if os.environ.get("SERVER_NAME", "").endswith(".onion"):
        curl += " --proxy socks5h://127.0.0.1:9050"

    print("get-subtitles")
    print()
    print("returns a zip archive with subtitles for a movie")
    print()
    print()
    print()
    print("usage")
    print()
    print(f'{curl} -G --fail-with-body -O -J --data-urlencode "movie=Scary.Movie.2000.720p.mp4" {request_url} && unzip Scary.Movie.2000.720p.subs.zip')
    print()
    print(f'{curl} -G --fail-with-body -o - --data-urlencode "movie=Scary.Movie.2000.720p.mp4" {request_url} | bsdtar -xvf -')
    print()
    print()
    print()
    print("source")
    print()
    print("https://github.com/milahu/opensubtitles-scraper/raw/main/get-subs.py")
    print()
    print()
    print()
    print("client")
    print()
    print('#!/usr/bin/env bash')
    print('# get-subs.sh - get subtitles from subtitles server')
    print(f'server_url="{request_url}"')
    if os.environ.get("SERVER_NAME", "").endswith(".onion"):
        print("# note: this requires a running tor proxy on 127.0.0.1:9050 - hint: sudo systemctl start tor")
    print(f'curl=({curl})')
    print('command -v curl >/dev/null || { echo "error: curl was not found"; exit 1; }')
    print('command -v unzip >/dev/null || { echo "error: unzip was not found"; exit 1; }')
    print('[ -n "$1" ] || { echo "usage: $0 path/to/Scary.Movie.2000.720p.mp4"; exit 1; }')
    print('dir="$(dirname "$1")"')
    print('[ -e "$dir" ] || { echo "error: no such directory: ${dir@Q}"; exit 1; }')
    print('cd "$dir"')
    print('movie="$(basename "$1")"')
    # TODO escape request_url for bash string
    print('if command -v bsdtar >/dev/null; then')
    print('  # https://superuser.com/a/1834410/951886 # write error body to stderr')
    print('  "${curl[@]}" -G --fail-with-body -D - -o - --data-urlencode "movie=$movie" "$server_url" | {')
    print('    s=; while read -r h; do h="${h:0: -1}"; if [ -z "$s" ]; then s=${h#* }; s=${s%% *}; fi; [ -z "$h" ] && break; done')
    print('    if [ "${s:0:1}" = 2 ]; then cat; else cat >&2; fi') # write error body to stderr
    print('  } | bsdtar -xvf -')
    print('else')
    print('  zip="${movie%.*}.subs.zip"')
    print('  ! [ -e "$zip" ] || { echo "error: tempfile exists: ${zip@Q}"; exit 1; }')
    print('  if ! "${curl[@]}" -G --fail-with-body -o "$zip" --data-urlencode "movie=$movie" "$server_url"; then')
    print('    cat "$zip" && rm "$zip" # zip contains the error message')
    print('  else')
    print('    unzip "$zip" && rm "$zip"')
    print('  fi')
    print('fi')
    # TODO
    """
    print()
    print(f"{request_url}?movie=Futurama.S06E07.The.Late.Philip.J.Fry.mp4&lang=es")
    print()
    print(f"{request_url}?imdb=tt2580382")
    print()
    print(f"{request_url}?imdb=tt0705920")
    """
    print()
    print()
    print()
    print("filenames")
    print()
    print("when you pass a movie filename like movie=Scary.Movie.2000.720p.mp4")
    print("then the subtitle files will be named Scary.Movie.2000.720p.12345.srt etc")
    print("so when you extract them to the folder of the movie file")
    print("then your video player should find the subtitles")
    print()
    print()
    print()
    print("encoding")
    print()
    print("the subtitles are not recoded to utf8")
    print("because im too lazy to finish this postprocessing")
    print("most subtitles should have utf8 encoding")
    print("but some subtitles can have single-byte encodings like latin1")
    print("see also")
    print("https://github.com/milahu/opensubtitles-scraper/raw/main/repack.py")

    sys.exit()



def expand_path(path):
    global data_dir
    if path == None:
        return path
    if path.startswith("~/"):
        path = os.environ["HOME"] + path[1:]
    elif path.startswith("$HOME/"):
        path = os.environ["HOME"] + path[5:]
    return os.path.join(data_dir, path)



def error(msg):
    raise Exception(msg)



def error_cgi(msg, status=400):
    print(f"Status: {status}")
    print("Content-Type: text/plain")
    print()
    print("error: " + msg)
    sys.exit()



def parse_args():
    #if len(sys.argv) != 2 or not os.path.exists(sys.argv[1]):
    if len(sys.argv) != 2:
        print_usage()
        sys.exit(1)
    args = types.SimpleNamespace(
        movie = sys.argv[1],
        #imdb = imdb,
        # lang_ISO639
        lang = "en",
    )
    #error(repr(args)) # debug
    return args



def parse_args_cgi():

    import urllib.parse

    query_string = os.environ.get("QUERY_STRING")
    #assert query_string != None
    if query_string == None:
        error("no query string")

    if query_string == "":
        show_help_cgi()

    #query_list = urllib.parse.parse_qsl(query_string, keep_blank_values=True)
    query_dict = urllib.parse.parse_qs(query_string, keep_blank_values=True)

    movie = query_dict.get("movie", [None])[0]
    imdb = query_dict.get("imdb", [None])[0]

    # check required arguments
    """
    if movie == None and imdb == None:
        error_cgi("missing argument: movie or imdb")
    """
    if movie == None:
        error_cgi("missing argument: movie")
    else:
        movie = os.path.basename(movie)

    lang = query_dict.get("lang", ["en"])[0]

    args = types.SimpleNamespace(
        movie = movie,
        imdb = imdb,
        lang = lang,
    )
    #error_cgi(repr(args)) # debug
    return args



def send_zipfile_cgi(args, member_files):

    basename, _extension = os.path.splitext(args.movie)

    headers = []

    headers.append("Status: 200")

    headers.append("Content-Type: application/zip")

    # Content-Dispositon
    # by default, curl and wget will ignore the filename. fix:
    #   curl -OJ
    #   wget --content-disposition
    # https://stackoverflow.com/questions/1361604/how-to-encode-utf8-filename-for-http-headers-python-django
    filename = basename + ".subs.zip"
    from urllib.parse import quote
    disposition = 'attachment'
    try:
        filename.encode('ascii')
        # TODO better? escape filename
        #file_expr = 'filename="{}"'.format(filename)
        file_expr = 'filename="{}"'.format(quote(filename))
    except UnicodeEncodeError:
        file_expr = "filename*=utf-8''{}".format(quote(filename))
    headers.append('Content-Disposition: {}; {}'.format(disposition, file_expr))

    sent_headers = False

    from stream_zip import stream_zip

    zip_header = None

    empty_zip_header = b"PK\x05\x06\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"

    is_first_chunk = True

    for zipped_chunk in stream_zip(member_files):

        if is_first_chunk and zipped_chunk == empty_zip_header:
            # buffer headers and this chunk
            # https://github.com/uktrade/stream-zip/issues/116
            # return nothing on empty input
            zip_header = zipped_chunk
            is_first_chunk = False
            continue

        if not sent_headers:
            # note: print adds a "\n"
            print("\n".join(headers) + "\n")
            sent_headers = True
            # fix: lighttpd error: response headers too large
            # if we dont flush sys.stdout here, then sys.stdout.buffer is written first
            sys.stdout.flush()

        if zip_header:
            # zip_header was set in the previous iteration
            sys.stdout.buffer.write(zip_header)
            zip_header = None

        sys.stdout.buffer.write(zipped_chunk)

        is_first_chunk = False

    if not sent_headers:
        # stream_zip(member_files) did not return any data
        error("not found", 404)

    sys.stdout.buffer.flush()

    sys.exit()



def config_get_providers(config):
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
                error("not implemented")
        else:
            error("not implemented")
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



def main():

    global data_dir
    global is_cgi
    global error
    global unpack_zipfiles

    # see also https://github.com/technetium/cgli/blob/main/cgli/cgli.py

    if os.environ.get("GATEWAY_INTERFACE") == "CGI/1.1":
        if os.environ.get("REQUEST_METHOD") != "GET":
            error("only GET requests are supported")
        is_cgi = True
        error = error_cgi
        # no. this has almost no effect on speed
        # the slowest part is "search by movie name" in database
        # -> use sqlite fts (full text search) -> 5x faster
        #unpack_zipfiles = False

    # relative paths are relative to data_dir
    # on linux: $HOME/.config/subtitles
    if is_cgi:
        data_dir = str(pathlib.Path(sys.argv[0]).parent.parent.parent / "subtitles")
    else:
        import platformdirs
        data_dir = platformdirs.user_config_dir("subtitles")
    if not os.path.exists(data_dir):
        error(f"missing data_dir: {repr(data_dir)}")

    config_path = f"{data_dir}/local-subtitle-providers.json"
    if not os.path.exists(config_path):
        error(f"missing config_path: {repr(config_path)}")
    with open(config_path) as f:
        config = json.load(f)

    # TODO use default from locale in os.environ["LANG"]
    # lang_ISO639
    lang = "en"

    # parse arguments
    if is_cgi:
        args = parse_args_cgi()
    else:
        args = parse_args()

    """
    video_path = sys.argv[1]
    print("video_path", video_path)
    # note: video_path does not need to exist
    os.makedirs(os.path.dirname(video_path), exist_ok=True)
    """

    video_filename = os.path.basename(args.movie)
    #print("video_filename", video_filename)

    # TODO allow to set title and year
    # guessit can fail in rare cases

    # len("abc 2000.mp4") == 12
    if len(video_filename) < 12:
        error("video_filename is too short")

    if len(video_filename) > 255:
        error("video_filename is too long")

    video_parsed = guessit.guessit(video_filename)
    #print("video_parsed", video_parsed)

    config_get_providers(config)

    if is_cgi:
        from stream_zip import ZIP_32
        # set the zip_fn here so the non-cgi code works without stream_zip
        def fix_args(args):
            #yield (sub_path, modified_at, mode, ZIP_32, (sub_content,))
            (a, b, c, _, e) = args
            return (a, b, c, ZIP_32, e)
        try:
            send_zipfile_cgi(args, map(fix_args, get_movie_subs(config, args, video_parsed)))
        except Exception as e:
            error(f"Exception {type(e)} {e}")
    else:
        #return get_movie_subs(video_path, video_parsed, lang, config)
        for item in get_movie_subs(config, args, video_parsed):
            (sub_path, modified_at, mode, zip_fn, (sub_content,)) = item
            sub_filename = os.path.basename(sub_path)
            print(f"writing {repr(sub_filename)}") # from {repr(filename)} ({encoding})")
            with open(sub_path, "wb") as sub_file:
                sub_file.write(sub_content)



def print_usage():
    print("usage:", file=sys.stderr)
    #argv0 = "get-subs.py"
    argv0 = os.path.basename(sys.argv[0])
    print(f"{argv0} Scary.Movie.2000.720p.mp4", file=sys.stderr)



def fts_string(str):
    # escape string for SQLite FTS query
    # note: this enforces the order of words
    return '"' + str.replace('"', ' ') + '"'



def fts_words(str):
    # escape words for SQLite FTS query
    # fix: sqlite3.OperationalError: fts5: syntax error near ","
    # https://github.com/hideaki-t/sqlite-fts-python
    # https://stackoverflow.com/a/78135123/10440128
    pat = re.compile(r'\w+', re.UNICODE)
    return " ".join(map(lambda word: word.lower(), pat.findall(str)))



def get_movie_subs(config, args, video_parsed):
    global data_dir
    global is_cgi
    video_path_base, video_path_extension = os.path.splitext(args.movie)
    # one database for metadata: 1.6GB
    #print(f"""metadata: getting connection""")
    # FIXME opensubs-metadata.db is slow
    # add index for (MovieName, MovieYear)
    # add full-text-search index for MovieName
    # add index for MovieYear
    metadata_db_path = expand_path(config["subtitles_metadata_db_path"])
    if not os.path.exists(metadata_db_path):
        error(f"no such file: {metadata_db_path}")
    #print(f"opening database {metadata_db_path}")
    metadata_con = sqlite3.connect(metadata_db_path)
    metadata_cur = metadata_con.cursor()
    # multiple databases for zipfiles: 24GB for english subs
    sql_query = None
    sql_args = None

    if not is_cgi:
        print("video_parsed", video_parsed)

    if video_parsed.get("type") == "movie":
        movie_title = video_parsed.get("title")
        movie_year = video_parsed.get("year")
        sql_query = (
            #"SELECT IDSubtitle "
            #"SELECT subz_metadata.IDSubtitle "
            "SELECT subz_metadata.rowid "
            #"FROM subz_metadata "
            "FROM subz_metadata, subz_metadata_fts_MovieName "
            #"WHERE MovieName LIKE ? "
            "WHERE "
            "subz_metadata.rowid = subz_metadata_fts_MovieName.rowid "
            "AND "
            "subz_metadata_fts_MovieName.MovieName MATCH ? " +
            ("AND subz_metadata.MovieYear = ? " if movie_year else "") +
            "AND "
            "subz_metadata.ISO639 = ? "
            "AND "
            "subz_metadata.SubSumCD = 1 "
            "AND "
            "subz_metadata.MovieKind = 'movie' "
            #"AND ImdbID = 12345"
            # rate-limiting for abuse-queries like movie=the.mp4
            "LIMIT 500 "
        )
        sql_args = []
        sql_args.append(fts_words(movie_title))
        if movie_year:
            sql_args.append(movie_year)
        sql_args.append(args.lang)
    elif video_parsed.get("type") == "episode":
        sql_query = (
            "SELECT subz_metadata.rowid "
            "FROM subz_metadata, subz_metadata_fts_MovieName "
            "WHERE "
            "subz_metadata.rowid = subz_metadata_fts_MovieName.rowid "
            "AND "
            "subz_metadata_fts_MovieName.MovieName MATCH ? "
            "AND "
            "SeriesSeason = ? "
            "AND "
            "SeriesEpisode = ? "
            "AND "
            "subz_metadata.ISO639 = ? "
            "AND "
            "subz_metadata.SubSumCD = 1 "
            "AND "
            "subz_metadata.MovieKind = 'tv' "
            # rate-limiting for abuse-queries like movie=the.mp4
            "LIMIT 500 "
        )
        title = video_parsed.get("title")
        episode_title = video_parsed.get("episode_title")
        if episode_title:
            title += " " + episode_title
        sql_args = (
            fts_words(title),
            video_parsed.get("season"),
            video_parsed.get("episode"),
            args.lang,
        )
    else:
        error(f"""unknown video type: {repr(video_parsed.get("type"))}""")

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

    if not is_cgi:
        print(f"""metadata: getting results for query:""", format_query(sql_query, sql_args))

    nums = list(map(lambda row: row[0], metadata_cur.execute(sql_query, sql_args).fetchall()))

    #if not is_cgi:
    #    print("metadata: nums:", nums)

    for provider in config["providers"]:
        #if provider.get("enabled") == False:
        #    continue
        provider_lang = provider.get("lang", "*")
        if provider_lang != "*":
            # TODO allow multiple languages for one provider
            if provider_lang != args.lang:
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

            if not os.path.exists(db_path):
                error(f"no such file: {db_path}")

            provider["db_con"] = sqlite3.connect(db_path)

            # TODO? build external index
            # https://sqlite.org/forum/forumpost/0ed07b9626
            # https://stackoverflow.com/questions/19379761/how-to-setup-index-for-virtual-table-in-sqlite
            # pysqlite3.connect is always readonly
            #provider["db_con"] = pysqlite3.connect(db_path)

            #print(f"""local provider {provider["id"]}: opening database {db_path}""")

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
        if not is_cgi:
            #print("sql_query", sql_query)
            print(f"""local provider {provider["id"]}: getting results for query:""", sql_query)

        #modified_at = 0
        #modified_at = datetime.fromtimestamp(0)
        # zip epoch is 1980-01-01?
        from datetime import datetime
        modified_at = datetime(1980, 1, 1)
        #mode = S_IFREG | 0o600
        mode = 0o100600

        for num, zip_content in provider["db_cur"].execute(sql_query):
            # found
            #print(f"""found sub {num} in local provider {provider["id"]}""")
            if unpack_zipfiles:
                (sub_path, sub_content) = extract_sub(zip_content, video_path_base, num, args.lang)
            else:
                (sub_path, sub_content) = (f"{num}.zip", zip_content)
            # no. dont require stream_zip here
            #from stream_zip import ZIP_32
            #yield (sub_path, modified_at, mode, ZIP_32, (sub_content,))
            zip_fn = None
            yield (sub_path, modified_at, mode, zip_fn, (sub_content,))
            # found zipfile -> dont search other providers
        #print(f"""local provider {provider["id"]}: done""")



def extract_sub(zip_content, video_path_base, num, lang):
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
            sub_path = f"{video_path_base}.{lang}.{num_padded}{ext}"
            sub_content = zip_file.read(zipinfo)
            if recode_sub_content_to_utf8:
                sub_encoding = charset_normalizer.from_bytes(sub_content).best().encoding
                if sub_encoding not in {"ascii", "utf_8"}:
                    # recode sub_content to utf8
                    try:
                        # bytes -> str -> bytes
                        sub_content = sub_content.decode(sub_encoding).encode("utf8")
                    except UnicodeDecodeError as error:
                        pass
                        #print(f"output {repr(sub_path)} warning: failed to convert to utf8 from {sub_encoding}: {error}")
            """
            sub_filename = os.path.basename(sub_path)
            #print(f"output {repr(sub_filename)} from {repr(filename)} ({encoding})")
            with open(sub_path, "wb") as sub_file:
                sub_file.write(sub_content)
            """
            #yield (sub_path, sub_content)
            return (sub_path, sub_content)
            break # stop after first file
            # TODO write multiple files


if __name__ == "__main__":
    main()
    sys.exit()
