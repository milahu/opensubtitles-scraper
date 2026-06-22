#! /usr/bin/env python3



# get subtitles for a video file
# from local subtitle providers

# to expose this over an http server, see
# docs/wsgi/lighttpd.conf
# docs/cgi/lighttpd.conf
# WSGI = many requests, low latency
# CGI = few requests, high latency

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
import string
import traceback
import urllib.parse

# requirements
# pip install guessit langcodes charset_normalizer stream_zip platformdirs
import guessit
import langcodes
import charset_normalizer
import stream_zip
import platformdirs



default_lang = "en"

# default values if args.movie is empty
default_title = "movie"
default_container = "mkv"

# with recode, this is 2x slower
# ideally recode once and cache the result
recode_sub_content_to_utf8 = False

# if is_cgi: unpack_zipfiles = False
unpack_zipfiles = True

# put language code before extension like ".eng.srt" so mpv can parse it
default_path_format = "$video_base.$num0.$lang.$ext"

path_format_vars = {
    "video_path": "path/to/Some.Movie.mp4",
    "video_base": "path/to/Some.Movie",
    "path": "subtitle filename: Some.Movie.srt",
    "base": "subtitle basename: Some.Movie",
    "ext": "subtitle file extension: srt",
    "num": "subtitle number: 12345",
    "num0": "zero-padded subtitle number: 00012345",
    "lang": "subtitle language as 3-letter code: eng",
}



# global state
is_debug = False
data_dir = None
is_cgi = False
is_wsgi = False
# runtime = "cli"
is_cli = False
config = None



def get_env(keys, default=None, environ=os.environ):
    if isinstance(keys, str):
        keys = [keys]
    for key in keys:
        val = environ.get(key)
        if not val is None:
            return val
    return default

def get_request_scheme(environ=os.environ):
    keys = (
        "HTTP_X_FORWARDED_PROTO",
        "REQUEST_SCHEME",
    )
    return get_env(keys, "http", environ)

def get_request_host(environ=os.environ):
    keys = (
        "HTTP_X_HOST",
        "HTTP_HOST",
    )
    return get_env(keys, "localhost", environ)
    # FIXME also get port
    # port 9592

def get_request_path(environ=os.environ):
    keys = (
        #"", # FIXME get original path
        "REQUEST_URI",
    )
    val = get_env(keys, "/bin/get-subtitles", environ)
    # workaround: nginx does not pass $request_uri as request header
    if get_request_host(environ).endswith(".feralhosting.com"):
        return "/" + os.environ["USER"] + val
    return val


def start_response_cgi(status, headers):
    print(f"Status: {status}")
    for key, val in headers:
        print(f"{key}: {val}")
    print()


def show_help_cgi():
    environ = dict(os.environ)
    for chunk in get_help_wsgi(os.environ, start_response_cgi):
        sys.stdout.buffer.write(chunk)
    sys.exit()


def get_help_wsgi(environ, start_response):
    headers = [
        ("Content-Type", "text/plain"),
    ]
    start_response("200 OK", headers)
    request_host = get_request_host(environ)
    # fix: nginx wrongly passes HTTP_X_FORWARDED_PROTO=http
    # request_scheme = get_request_scheme(environ)
    request_scheme = "http" if request_host == "localhost" else "https"
    request_url = (
        request_scheme + "://" +
        request_host +
        get_request_path(environ)
    )
    request_url = request_url.encode("utf8")

    curl = b"curl"
    if environ.get("SERVER_NAME", "").endswith(".onion"):
        curl += b" --proxy socks5h://127.0.0.1:9050"

    yield b"get-subtitles\n"
    yield b"\n"
    yield b"returns a zip archive with subtitles for a movie\n"
    yield b"\n"
    yield b"\n"
    yield b"\n"
    yield b"usage\n"
    yield b"\n"
    yield curl + b' -G --fail-with-body -O -J --data-urlencode "movie=Scary.Movie.2000.720p.mp4" ' + request_url + b' && unzip Scary.Movie.2000.720p.subs.zip\n'
    yield b"\n"
    yield curl + b' -G --fail-with-body -o - --data-urlencode "movie=Scary.Movie.2000.720p.mp4" ' + request_url + b' | bsdtar -xvf -\n'
    yield b"\n"
    yield b"\n"
    yield b"\n"
    yield b"source\n"
    yield b"\n"
    yield b"https://github.com/milahu/opensubtitles-scraper/raw/main/get-subs.py\n"
    yield b"\n"
    yield b"\n"
    yield b"\n"
    yield b"client\n"
    yield b"\n"
    # TODO store a fully functional get-subs.sh script in git
    yield b'#!/usr/bin/env bash\n'
    yield b'# get-subs.sh - get subtitles from subtitles server\n'
    yield b'#set -x # xtrace\n'
    yield b'server_url="' + request_url + b'"\n'
    if os.environ.get("SERVER_NAME", "").endswith(".onion"):
        yield b"# note: this requires a running tor proxy on 127.0.0.1:9050 - hint: sudo systemctl start tor\n"
    yield b'curl=(' + curl + b')\n'
    yield b'command -v curl >/dev/null || { echo "error: curl was not found"; exit 1; }\n'
    yield b'command -v unzip >/dev/null || { echo "error: unzip was not found"; exit 1; }\n'
    yield b'[ -n "$1" ] || { echo "usage: $0 [--lang en,es,de,ru,cn] path/to/Scary.Movie.2000.720p.mp4"; exit 1; }\n'
    yield b'lang=\n'
    yield b'path_format=\n'
    yield b'while (( $# > 0 )); do\n'
    yield b'case "$1" in\n'
    yield b'  --lang|-l) lang="$2"; shift 2; continue;;\n'
    yield b'  --path-format) path_format="$2"; shift 2; continue;;\n'
    yield b'  *) :;;\n'
    yield b'esac\n'
    yield b'dir="$(dirname "$1")"\n'
    yield b'[ -e "$dir" ] || { echo "error: no such directory: ${dir@Q}"; exit 1; }\n'
    yield b'pushd "$dir" >/dev/null\n'
    yield b'movie="$(basename "$1")"\n'
    # TODO escape request_url for bash string
    yield b'curl_data=(\n'
    yield b'  --data-urlencode "movie=$movie"\n'
    yield b'  --data-urlencode "lang=$lang"\n'
    yield b'  --data-urlencode "path_format=$path_format"\n'
    yield b')\n'
    yield b'if command -v bsdtar >/dev/null; then\n'
    yield b'  # https://superuser.com/a/1834410/951886 # write error body to stderr\n'
    yield b'  "${curl[@]}" -G --fail-with-body -D - -o - "${curl_data[@]}" "$server_url" | {\n'
    yield b'    s=; while read -r h; do h="${h:0: -1}"; if [ -z "$s" ]; then s=${h#* }; s=${s%% *}; fi; [ -z "$h" ] && break; done\n'
    yield b'    if [ "${s:0:1}" = 2 ]; then cat; else cat >&2; fi' # write error body to stderr
    yield b'  } | bsdtar -xvf -\n'
    yield b'else\n'
    yield b'  zip="${movie%.*}.subs.zip"\n'
    yield b'  ! [ -e "$zip" ] || { echo "error: tempfile exists: ${zip@Q}"; exit 1; }\n'
    yield b'  if ! "${curl[@]}" -G --fail-with-body -o "$zip" "${curl_data[@]}" "$server_url"; then\n'
    yield b'    cat "$zip" && rm "$zip" # zip contains the error message\n'
    yield b'  else\n'
    yield b'    unzip "$zip" && rm "$zip"\n'
    yield b'  fi\n'
    yield b'fi\n'
    yield b'popd >/dev/null\n'
    yield b'shift\n'
    yield b'done\n'
    yield b"\n"
    yield b"\n"
    yield b"\n"
    yield b"filenames\n"
    yield b"\n"
    yield b"when you pass a movie filename like movie=Scary.Movie.2000.720p.mp4\n"
    yield b"then the subtitle files will be named Scary.Movie.2000.720p.12345.srt etc\n"
    yield b"so when you extract them to the folder of the movie file\n"
    yield b"then your video player should find the subtitles\n"
    yield b"\n"
    yield b"you can change the filenames format with the path_format parameter\n"
    yield b"default: " + default_path_format.encode("utf8") + b"\n"
    yield b"variables:\n"
    for key, val in path_format_vars.items():
        yield f"${{{key}}}: {val}\n".encode("utf8")
    yield b"\n"
    yield b"\n"
    yield b"\n"
    yield b"language\n"
    yield b"\n"
    yield b"you can pass one or more languages as 2 letter codes per ISO 639-1\n"
    yield b"or as 3 letter codes per ISO 639-2\n"
    yield b"https://en.wikipedia.org/wiki/List_of_ISO_639_language_codes\n"
    yield b"\n"
    yield b'the output filenames have the format "Some.Movie.2000.{num}.{lang}.srt"\n'
    yield b"where lang is a 3 letter code compatible with video players\n"
    yield b"\n"
    yield b"?movie=Futurama.S06E07.The.Late.Philip.J.Fry.mp4&lang=es\n"
    yield b"\n"
    yield b"?movie=Futurama.S06E07.The.Late.Philip.J.Fry.mp4&lang=en,es,fr,de,cz,cn\n"
    yield b"\n"
    yield b"?movie=Futurama.S06E07.The.Late.Philip.J.Fry.mp4&lang=eng,spa,fre,ger,cze,chi\n"
    # TODO

    yield b"\n"
    yield b"?imdb=tt2580382\n"
    yield b"\n"
    yield b"?imdb=tt0705920\n"

    yield b"\n"
    yield b"\n"
    yield b"\n"
    yield b"movie title\n"
    yield b"\n"
    yield b"in rare cases, the guessit library (https://github.com/guessit-io/guessit) fails to parse movie filenames\n"
    yield b"examples: xXx.2002.mp4 22.July.2018.mp4\n"
    yield b"\n"
    yield b"in these cases, you can override the guessit result with the video-parsed-json parameter\n"
    yield b"examples:\n"
    yield curl + b""" -G -O --fail-with-body -J --data-urlencode 'video-parsed-json={"type":"movie","title":"22 July","year":2018}' """ + request_url + b"\n"
    yield curl + b""" -G -O --fail-with-body -J --data-urlencode 'video-parsed-json={"type":"episode","title":"The Simpsons","season":1,"episode":1}' """ + request_url + b"\n"
    yield b"\n"
    yield b"\n"
    yield b"\n"
    yield b"encoding\n"
    yield b"\n"
    yield b"the subtitles are not recoded to utf8\n"
    yield b"because im too lazy to finish this postprocessing\n"
    yield b"most subtitles should have utf8 encoding\n"
    yield b"but some subtitles can have single-byte encodings like latin1\n"
    yield b"see also\n"
    yield b"https://github.com/milahu/opensubtitles-scraper/raw/main/repack.py\n"
    yield b"\n"
    yield b"\n"
    yield b"\n"
    yield b"adblocker\n"
    yield b"\n"
    yield b"this is not done on the server side to save cpu time\n"
    yield b"\n"
    yield b"to remove ads, see\n"
    yield b"https://github.com/milahu/opensubtitles-scraper/raw/main/opensubtitles_adblocker.py\n"
    yield b"\n"
    yield b"to add more ads to the blocklist, see\n"
    yield b"https://github.com/milahu/opensubtitles-scraper/raw/main/opensubtitles_adblocker_add.py\n"



def expand_path(path):
    global data_dir
    if path == None:
        return path
    # TODO use os.path.expanduser
    if path.startswith("~/"):
        path = os.environ["HOME"] + path[1:]
    # TODO use os.path.expandvars
    elif path.startswith("$HOME/"):
        path = os.environ["HOME"] + path[5:]
    elif path.startswith("$CAS/"):
        # TODO try to find path in CAS dirs from ~/.config/cas.json
        # {
        #   "dirs": [
        #     "/path/to/cas"
        #   ]
        # }
        path = os.environ["CAS"] + path[4:]
    return os.path.join(data_dir, path)



# map country codes (ISO 3166) to language codes (ISO 639)
# https://github.com/georgkrause/langcodes/issues/16

map_lang4country = {
    "ad": "ca", "ag": "en", "ai": "en", "al": "sq", "ao": "pt", "at": "de",
    "au": "en", "aw": "nl", "ax": "sv", "bb": "en", "bd": "bn", "bf": "fr",
    "bj": "fr", "bl": "fr", "bq": "nl", "bt": "dz", "bw": "en", "by": "be",
    "bz": "en", "cc": "ms", "cd": "fr", "cf": "fr", "cg": "fr", "ci": "fr",
    "ck": "en", "cl": "es", "cm": "en", "cn": "zh", "cw": "nl", "cx": "en",
    "cz": "cs", "dj": "fr", "dk": "da", "dm": "en", "do": "es", "ec": "es",
    "eg": "ar", "eh": "ar", "er": "aa", "fk": "en", "fm": "en", "gb": "en",
    "ge": "ka", "gf": "fr", "gg": "en", "gh": "en", "gi": "en", "gm": "en",
    "gp": "fr", "gq": "es", "gr": "el", "gs": "en", "gt": "es", "gw": "pt",
    "gy": "en", "hk": "zh", "hn": "es", "il": "he", "im": "en", "iq": "ar",
    "ir": "fa", "je": "en", "jm": "en", "jo": "ar", "jp": "ja", "ke": "en",
    "kh": "km", "kp": "ko", "kz": "kk", "lc": "en", "lk": "si", "lr": "en",
    "ls": "en", "ly": "ar", "ma": "ar", "mc": "fr", "md": "ro", "me": "sr",
    "mf": "fr", "mm": "my", "mp": "fil", "mq": "fr", "mu": "en", "mv": "dv",
    "mw": "ny", "mx": "es", "mz": "pt", "nc": "fr", "nf": "en", "ni": "es",
    "np": "ne", "nu": "niu", "nz": "en", "pe": "es", "pf": "fr", "pg": "en",
    "ph": "tl", "pk": "ur", "pm": "fr", "pn": "en", "pr": "en", "pw": "pau",
    "py": "es", "qa": "ar", "re": "fr", "rs": "sr", "sb": "en", "sj": "no",
    "sx": "nl", "sy": "ar", "sz": "en", "tc": "en", "td": "fr", "tf": "fr",
    "tj": "tg", "tm": "tk", "tv": "tvl", "tz": "sw", "ua": "uk", "um": "en",
    "us": "en", "uy": "es", "va": "la", "vc": "en", "vg": "en", "vn": "vi",
    "vu": "bi", "wf": "wls", "ws": "sm", "xk": "sq", "ye": "ar", "yt": "fr",
    "zm": "en", "zw": "en"
}

def lang4country(country):
    try:
        return map_lang4country[country]
    except KeyError:
        return country

def lang2letter(lang):
    "convert to 2 letter language code"
    try:
        return langcodes.Language.get(lang).language
    except langcodes.tag_parser.LanguageTagError:
        return lang

def lang3letter(lang):
    "convert to 3 letter language code"
    try:
        return langcodes.Language.get(lang).to_alpha3(variant='B')
    except langcodes.tag_parser.LanguageTagError:
        return lang



def error(msg):
    raise Exception(msg)



def error_cgi(msg, status=400):
    print(f"Status: {status}")
    print("Content-Type: text/plain")
    print()
    print("error: " + msg)
    sys.exit()



def parse_args():
    import argparse
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("-l", "--lang", dest="lang_list")
    parser.add_argument(
        "--path-format", # args.path_format
        default=default_path_format,
        type=str,
        metavar="FORMAT",
        help=(
            f"path format for subtitle files\n"
            f"default: {default_path_format!r}\n"
            f"variables:\n"
            +
            "".join(map(lambda kv: f"${{{kv[0]}}}: {kv[1]}\n", path_format_vars.items()))
        ),
    )
    parser.add_argument("--imdb")
    parser.add_argument("--video-parsed-json") # args.video_parsed_json
    parser.add_argument("movie")
    args = parser.parse_args()
    if args.lang_list != None:
        args.lang_list = re.findall(r"\b[a-z]{2,3}\b", args.lang_list) or [default_lang]
    else:
        args.lang_list = [default_lang]
    if not args.path_format:
        args.path_format = default_path_format
    #error(repr(args)) # debug
    return args



def parse_args_cgi(environ=None):

    environ = environ or os.environ

    query_string = environ.get("QUERY_STRING")

    if not query_string:
        return None
        # show_help_cgi()

    #query_list = urllib.parse.parse_qsl(query_string, keep_blank_values=True)
    query_dict = urllib.parse.parse_qs(query_string, keep_blank_values=True)

    movie = query_dict.get("movie", [None])[0]
    imdb = query_dict.get("imdb", [None])[0] # TODO
    video_parsed_json = query_dict.get("video-parsed-json", [None])[0]

    # check required arguments
    """
    if movie == None and imdb == None:
        error_cgi("missing argument: movie or imdb")
    """
    if movie == None and video_parsed_json == None:
        error_cgi("missing argument: movie")
    elif movie != None:
        movie = os.path.basename(movie)

    lang_str = query_dict.get("lang", [""])[0].lower()
    # parse list of 2 or 3 letter language codes
    lang_list = re.findall(r"\b[a-z]{2,3}\b", lang_str) or [default_lang]

    path_format = query_dict.get("path_format", [None])[0]
    if not path_format:
        path_format = default_path_format

    #error_cgi("lang_list: " + repr(lang_list)) # debug

    args = types.SimpleNamespace(
        movie = movie,
        imdb = imdb,
        lang_list = lang_list,
        path_format = path_format,
        video_parsed_json = video_parsed_json,
    )
    #error_cgi(repr(args)) # debug
    return args



def send_zipfile_cgi(args, member_files):

    if args.movie:
        basename, _extension = os.path.splitext(args.movie)
    else:
        basename = args.video_parsed.get("title", default_title).replace(" ", ".")

    headers = []

    headers.append("Status: 200")

    headers.append("Content-Type: application/zip")

    # Content-Dispositon
    # by default, curl and wget will ignore the filename. fix:
    #   curl -OJ
    #   wget --content-disposition
    # https://stackoverflow.com/questions/1361604/how-to-encode-utf8-filename-for-http-headers-python-django
    filename = basename + ".subs.zip"
    quote = urllib.parse.quote
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

    # from stream_zip import stream_zip

    zip_header = None

    empty_zip_header = b"PK\x05\x06\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"

    is_first_chunk = True

    for zipped_chunk in stream_zip.stream_zip(member_files):

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
            # single-file provider
            providers.append(provider)
            continue
        # multi-file provider: expand to multiple providers
        # subtitles are grouped by shard or language
        shard_size = provider.get("shard_size")
        db_path_base = expand_path(provider.get("db_path_base"))
        db_path_format = provider.get("db_path_format")
        # TODO? use regex to parse shard_id
        #db_path_glob = provider.get("db_path_glob")
        #db_path_shard_id_regex = provider.get("db_path_shard_id_regex")
        get_shard_id = None
        get_lang = None
        if db_path_base and db_path_format:
            db_path_end = db_path_format
            db_path_end = db_path_end.replace("{shard_id}", "*")
            db_path_end = db_path_end.replace("{lang}", "*")
            db_path_glob = db_path_base + db_path_end
            if db_path_format.endswith("/{shard_id}xxx.db"):
                get_shard_id = lambda db_path: int(os.path.basename(db_path)[:-6])
            elif db_path_format.endswith("/{lang}.db"):
                # legacy. split-by-language releases are not stable
                # so this was used only once in opensubtitles.org.dump.9180519.to.9521948.by.lang.2023.04.26
                # with 3 letter language codes: eng, ger, cze, rus, chi, ...
                get_lang = lambda db_path: os.path.basename(db_path)[:-3]
            else:
                error("not implemented")
        else:
            error("not implemented")
        for db_path in glob.glob(db_path_glob):
            provider_2 = dict(provider)
            provider_2["db_path"] = db_path
            if get_shard_id:
                shard_id = get_shard_id(db_path)
                num_range_from = shard_id * shard_size
                provider_2["id"] = provider["id"] + f"/shard-{shard_id}"
                provider_2["num_range_from"] = num_range_from
                provider_2["num_range_to"] = num_range_from + shard_size - 1
            if get_lang:
                lang = get_lang(db_path)
                provider_2["id"] = provider["id"] + f"/lang-{lang}"
                provider_2["lang"] = lang
            providers.append(provider_2)
    config["providers"] = providers



def db_path_regex_of_pattern(pattern: str) -> re.Pattern:
    token_re = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}|\*")
    parts = []
    pos = 0
    for m in token_re.finditer(pattern):
        # Escape literal text before the token
        parts.append(re.escape(pattern[pos:m.start()]))
        if m.group(1):  # {name}
            name = m.group(1)
            if name == "lang":
                # {lang} -> [a-z]{2,3}
                # provider_lang = provider.get("lang", "*")
                parts.append(f"(?P<{name}>[a-z]{{2,3}})")
            elif name == "shard_id":
                # {shard_id} -> [0-9]+
                # num_range_from = provider.get("num_range_from", 0)
                # num_range_to = provider.get("num_range_to", 0)
                parts.append(f"(?P<{name}>[0-9]+)")
            else:
                parts.append(f"(?P<{name}>.*?)")
        else:  # *
            parts.append(".*?")
        pos = m.end()
    # Escape remaining literal text
    parts.append(re.escape(pattern[pos:]))
    regex = "^" + "".join(parts) + "$"
    return re.compile(regex)



def resolve_providers(providers):

    global is_cli
    global is_debug

    # resolve database files from glob patterns in provider["db_path_format"]
    new_providers = []
    for provider in providers:
        if provider.get("enabled") == False:
            continue
        if "db_path" in provider:
            # nothing to resolve here
            new_providers.append(provider)
            continue
        if "db_path_base" in provider and "db_path_format" in provider:
            # resolve db files
            # NOTE we expand variables only in db_path_base
            # NOTE db_path_format is a glob pattern for .db files
            # which can contain placeholders
            # {lang} -> [a-z]{2,3}
            # {shard_id} -> [0-9]+
            # NOTE db_path_format must start with "/"
            db_path_base = provider["db_path_base"]
            db_path_base = expand_path(db_path_base)
            db_path_format = provider["db_path_format"]
            db_path_regex = db_path_regex_of_pattern(db_path_format)
            db_path_base_len = len(db_path_base)
            new_provider_base = dict(provider) # shallow copy
            del new_provider_base["db_path_base"]
            del new_provider_base["db_path_format"]
            for root, dirs, files in os.walk(db_path_base):
                # if '__pycache__' in dirs:
                #     dirs.remove('__pycache__')  # don't visit __pycache__ directories
                for name in sorted(files):
                    db_path = os.path.join(root, name)
                    # NOTE db_subpath starts with "/"
                    db_subpath = db_path[db_path_base_len:]
                    # print(f"db_subpath: {db_subpath!r}")
                    match = db_path_regex.fullmatch(db_subpath)
                    if not match:
                        continue
                    # print(f"db_path: {db_path!r}")
                    # these values are used later to filter databases
                    # num_range_from = provider.get("num_range_from", 0)
                    # num_range_to = provider.get("num_range_to", 0)
                    # provider_lang = provider.get("lang", "*")
                    match_dict = match.groupdict()
                    if "shard_id" in match_dict:
                        shard_id = match_dict["shard_id"] = int(match_dict["shard_id"])
                        if "shard_size" in provider and type(provider["shard_size"]) == int:
                            shard_size = provider["shard_size"]
                            match_dict["num_range_from"] = shard_id * shard_size
                            match_dict["num_range_to"] = (shard_id + 1) * shard_size - 1
                    # print(f"db_subpath={db_subpath!r} match_dict={match_dict}")
                    new_provider = dict(new_provider_base) # shallow copy
                    new_provider["db_path"] = db_path
                    new_provider.update(match_dict)
                    new_providers.append(new_provider)
        else:
            # FIXME load all databases
            if is_cli or is_debug:
                print(f"not loading database: provider={json.dumps(provider, indent=2)}")

    return new_providers



def init():

    # init global state for WSGI app

    global data_dir
    global is_cgi
    global is_cli
    global is_debug
    global is_wsgi
    global error
    global unpack_zipfiles
    global config

    if os.environ.get("GATEWAY_INTERFACE") == "CGI/1.1":
        is_cgi = True
        error = error_cgi
    elif "_" in os.environ:
        # os.environ["_"] == sys.argv[0] == "./get-subs.py"
        is_cli = True
    elif any(arg.endswith(":wsgi_request_handler") for arg in sys.argv):
        # gunicorn --preload get-subs:wsgi_request_handler
        is_wsgi = True

    if 0:
        # compare env between CLI and WSGI
        # ./get-subs.py >get-subs.py.out.cli
        # ./docs/wsgi/gunicorn.sh >get-subs.py.out.wsgi
        # diff -u get-subs.py.out.cli get-subs.py.out.wsgi
        print("os.environ:", json.dumps(dict(os.environ), indent=2))
        print("sys.argv:", json.dumps(sys.argv, indent=2))

    if is_debug:
        print(f"init: is_cgi={is_cgi} is_cli={is_cli}")

    # see also https://github.com/technetium/cgli/blob/main/cgli/cgli.py

    if os.environ.get("GATEWAY_INTERFACE") == "CGI/1.1":
        # print("init: GATEWAY_INTERFACE = CGI/1.1", file=sys.stderr)
        is_cgi = True
        error = error_cgi
        if os.environ.get("REQUEST_METHOD") != "GET":
            error("only GET requests are supported")

    # relative paths are relative to data_dir
    # on linux: $HOME/.config/subtitles
    # data_dir = str(pathlib.Path(sys.argv[0]).parent.parent.parent / "subtitles")
    data_dir = (
        os.environ.get("SUBTITLES_DATA_DIR") or
        platformdirs.user_config_dir("subtitles")
    )
    if not os.path.exists(data_dir):
        error(f"missing data_dir: {repr(data_dir)}")

    config_path = f"{data_dir}/local-subtitle-providers.json"
    if not os.path.exists(config_path):
        error(f"missing config_path: {repr(config_path)}")

    with open(config_path) as f:
        config = json.load(f)

    metadata_db_path = expand_path(config["subtitles_metadata_db_path"])
    if not os.path.exists(metadata_db_path):
        error(f"no such file: {metadata_db_path}")

    #print(f"opening database {metadata_db_path}")
    # metadata_con = sqlite3.connect(metadata_db_path)
    metadata_con = sqlite3.connect(f"file:{metadata_db_path}?mode=ro", uri=True)
    metadata_cur = metadata_con.cursor()
    config["subtitles_metadata_db_con"] = metadata_con
    config["subtitles_metadata_db_cur"] = metadata_cur

    if 1:
        # load all databases now to fail early
        config["providers"] = resolve_providers(config["providers"])
        num_loaded_dbs = 0
        for provider in config["providers"]:
            if provider.get("enabled") == False:
                continue
            if not "db_path" in provider:
                # FIXME load all databases
                if is_cli or is_debug:
                    print(f"not loading database: provider={json.dumps(provider, indent=2)}")
                continue
            db_path = provider.get("db_path")
            # print(f"loading database: db_path={db_path!r}")
            db_path = expand_path(db_path)
            if not os.path.exists(db_path):
                error(f"no such file: {db_path}")
            # provider["db_con"] = sqlite3.connect(db_path)
            provider["db_con"] = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            # cache the cursor for faster lookup of similar nums
            provider["db_cur"] = provider["db_con"].cursor()
            num_loaded_dbs += 1
        assert num_loaded_dbs > 0, "no databases were loaded"
        if is_cli or is_debug:
            print(f"loaded {num_loaded_dbs} databases")



def main():

    global data_dir
    global is_cgi
    global error
    global unpack_zipfiles

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

    if args.video_parsed_json:
        video_parsed = json.loads(args.video_parsed_json)

    else:
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

    args.video_parsed = video_parsed

    #print("video_parsed", video_parsed)

    config_get_providers(config)

    if is_cgi:
        # from stream_zip import ZIP_32
        # set the zip_fn here so the non-cgi code works without stream_zip
        def fix_args(args):
            #yield (sub_path, modified_at, mode, stream_zip.ZIP_32, (sub_content,))
            (a, b, c, _, e) = args
            return (a, b, c, stream_zip.ZIP_32, e)
        try:
            # send_zipfile_cgi(args, map(fix_args, get_movie_subs(config, args, video_parsed)))
            send_zipfile_cgi(args, get_movie_subs(config, args, video_parsed))
        except Exception as exc:
            tb_str = "".join(traceback.format_exception(exc))
            error(f"{type(exc).__name__}: {exc}\n\n{tb_str}\n\nvideo_parsed={video_parsed}")
    else:
        #return get_movie_subs(video_path, video_parsed, lang, config)
        for item in get_movie_subs(config, args, video_parsed):
            (sub_path, modified_at, mode, zip_fn, (sub_content,)) = item
            sub_filename = os.path.basename(sub_path)
            print(f"writing {repr(sub_filename)}") # from {repr(filename)} ({encoding})")
            with open(sub_path, "wb") as sub_file:
                sub_file.write(sub_content)


def wsgi_request_handler(environ, start_response):

    # WSGI request handler

    global config

    if is_debug:
        print("wsgi_request_handler")

    # for key, val in environ.items():
    #     print(f"environ: {key} = {val}")

    try:
        args = parse_args_cgi(environ)

        if not args:
            # show_help_cgi()
            yield from get_help_wsgi(environ, start_response)
            return

        if is_debug:
            print(f"args: {args}")

        if args.video_parsed_json:
            video_parsed = json.loads(args.video_parsed_json)

        else:
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

        args.video_parsed = video_parsed

        # # set the zip_fn here so the non-cgi code works without stream_zip
        # def fix_args(args):
        #     #yield (sub_path, modified_at, mode, stream_zip.ZIP_32, (sub_content,))
        #     (a, b, c, _, e) = args
        #     return (a, b, c, stream_zip.ZIP_32, e)
        # member_files = map(fix_args, get_movie_subs(config, args, video_parsed))

        member_files = get_movie_subs(config, args, video_parsed)

        headers = [
            ("Content-Type", "application/zip"),
            # ("Content-Disposition", 'attachment; filename="subs.zip"'),
            # ("Transfer-Encoding", "chunked"), # stream response?
        ]

        if args.movie:
            basename, _extension = os.path.splitext(args.movie)
        else:
            basename = args.video_parsed.get("title", default_title).replace(" ", ".")

        filename = basename + ".subs.zip"
        quote = urllib.parse.quote
        disposition = 'attachment'
        try:
            filename.encode('ascii')
            # TODO better? escape filename
            #file_expr = 'filename="{}"'.format(filename)
            file_expr = 'filename="{}"'.format(quote(filename))
        except UnicodeEncodeError:
            file_expr = "filename*=utf-8''{}".format(quote(filename))
        headers.append(('Content-Disposition', f'{disposition}; {file_expr}'))

        sent_headers = False
        zip_header = None
        # empty_zip_header = b"PK\x05\x06\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        # len(empty_zip_header) == 22
        is_first_chunk = True
        for zipped_chunk in stream_zip.stream_zip(member_files):
            # if is_first_chunk and zipped_chunk == empty_zip_header:
            if is_first_chunk and len(zipped_chunk) == 22:
                # print(f"chunk 1: {zipped_chunk!r}")
                # buffer headers and this chunk
                # https://github.com/uktrade/stream-zip/issues/116
                # return nothing on empty input
                zip_header = zipped_chunk
                is_first_chunk = False
                continue
            if not sent_headers:
                # stream_zip returned the second chunk
                # print(f"chunk 2: {zipped_chunk[:50]!r}")
                start_response("200 OK", headers)
                sent_headers = True
            if zip_header:
                # zip_header was set in the previous iteration
                yield zip_header
                zip_header = None
            # print(f"chunk N: {zipped_chunk[:50]!r}")
            yield zipped_chunk
            is_first_chunk = False

        if not sent_headers:
            # stream_zip(member_files) did not return any data
            headers = tuple()
            start_response("404 Not Found", headers)

    except Exception as exc:
        tb = "".join(traceback.format_exception(exc))
        print(tb)
        start_response(
            "500 Internal Server Error",
            [("Content-Type", "text/plain")]
        )
        # return [tb.encode()]
        return tb.encode()


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
    if args.movie:
        video_path_base, video_path_extension = os.path.splitext(args.movie)
    else:
        video_path_base = video_parsed.get("title", default_title).replace(" ", ".")
        if video_parsed.get("type") == "episode":
            season = video_parsed.get("season")
            episode = video_parsed.get("episode")
            if season != None and episode != None:
                video_path_base += f".S{season:02d}E{episode:02d}"
        video_path_extension = video_parsed.get("container", default_container)
    # one database for metadata: 1.6GB
    #print(f"""metadata: getting connection""")
    # FIXME opensubs-metadata.db is slow
    # add index for (MovieName, MovieYear)
    # add full-text-search index for MovieName
    # add index for MovieYear
    r'''
    metadata_db_path = expand_path(config["subtitles_metadata_db_path"])
    if not os.path.exists(metadata_db_path):
        error(f"no such file: {metadata_db_path}")
    #print(f"opening database {metadata_db_path}")
    metadata_con = sqlite3.connect(metadata_db_path)
    metadata_cur = metadata_con.cursor()
    '''
    metadata_cur = config["subtitles_metadata_db_cur"]

    # multiple databases for zipfiles: 24GB for english subs
    sql_query = None
    sql_args = None

    # map from country codes (ISO 3166) to language codes (ISO 639)
    # cz -> cs, jp -> ja, ...
    args.lang_list = map(lang4country, args.lang_list)

    # convert to 2 letter language codes for the database query
    # ger -> de, eng -> en, ...
    args.lang_list = map(lang2letter, args.lang_list)

    args.lang_list = list(args.lang_list)

    if is_cli or is_debug:
        print("video_parsed", video_parsed)

    if video_parsed.get("type") == "movie":
        movie_title = video_parsed.get("title")
        movie_year = video_parsed.get("year")

        if not movie_title and not movie_year:
            error(f"failed to parse movie_title and movie_year from filename {repr(args.movie)}\n\nvideo_parsed={video_parsed}")

        def basename(path):
            # os.path.basename does not split on both / and \
            return re.split(r"[/\\]", path)[-1]

        if not movie_title:
            # workaround for xXx.2002.mp4
            # https://github.com/guessit-io/guessit/issues/773
            # xxx should be parsed as movie title
            movie_title = basename(args.movie).split(str(movie_year))[0][:-1]

        if not movie_title:
            error(f"failed to parse movie_title from filename {repr(args.movie)}")

        sql_query = (
            #"SELECT IDSubtitle "
            #"SELECT subz_metadata.IDSubtitle "
            "SELECT subz_metadata.rowid, subz_metadata.ISO639 "
            #"FROM subz_metadata "
            "FROM subz_metadata, subz_metadata_fts_MovieName "
            #"WHERE MovieName LIKE ? "
            "WHERE "
            "subz_metadata.rowid = subz_metadata_fts_MovieName.rowid "
            "AND "
            "subz_metadata_fts_MovieName.MovieName MATCH ? " +
            ("AND subz_metadata.MovieYear = ? " if movie_year else "") +
            "AND "
            f"subz_metadata.ISO639 IN ({','.join('?' * len(args.lang_list))}) "
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
        sql_args.extend(args.lang_list)
    elif video_parsed.get("type") == "episode":
        sql_query = (
            "SELECT subz_metadata.rowid, subz_metadata.ISO639 "
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
            f"subz_metadata.ISO639 IN ({','.join('?' * len(args.lang_list))}) "
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
            *args.lang_list,
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

    if is_cli or is_debug:
        print(f"""metadata: getting results for query:""", format_query(sql_query, sql_args))

    num_lang_list = metadata_cur.execute(sql_query, sql_args).fetchall()

    #if is_cli or is_debug:
    #    print("metadata: num_lang_list:", num_lang_list)

    args_lang3letter_list = list(map(lang3letter, args.lang_list))

    for provider in config["providers"]:
        #if provider.get("enabled") == False:
        #    continue
        provider_lang = provider.get("lang", "*")
        if provider_lang != "*":
            # TODO allow multiple languages for one provider
            if not provider_lang in args_lang3letter_list:
                continue

        def filter_num(num):
            num_range_from = provider.get("num_range_from", 0)
            if num_range_from == 0:
                return True
            num_range_to = provider.get("num_range_to", 0)
            if num_range_to == 0:
                return True
            return num_range_from <= num and num <= num_range_to

        provider_num_lang_list = []
        rest_num_lang_list = []
        for num_lang in num_lang_list:
            num = num_lang[0]
            if filter_num(num):
                provider_num_lang_list.append(num_lang)
            else:
                rest_num_lang_list.append(num_lang)
        num_lang_list = rest_num_lang_list
        if not provider_num_lang_list:
            #print(f"""local provider {provider["id"]}: num is out of range""")
            continue
        #print(f"""local provider {provider["id"]}: getting {len(provider_num_lang_list)} nums""")

        if not "db_con" in provider:
            continue

        r'''
        if not "db_con" in provider:
            db_path = expand_path(provider.get("db_path"))

            # use sqlite ATTACH? - no. number is limited to 10 files
            # https://stackoverflow.com/questions/30292367/sqlite-append-two-tables-from-two-databases-that-have-the-exact-same-schema
            # https://sqlite.org/cgi/src/doc/reuse-schema/doc/shared_schema.md

            if not os.path.exists(db_path):
                error(f"no such file: {db_path}")

            # provider["db_con"] = sqlite3.connect(db_path)
            provider["db_con"] = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)

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
        '''

        provider_num_list = list(map(lambda x: x[0], provider_num_lang_list))

        lang_by_num = None
        if unpack_zipfiles:
            lang_by_num = {num: lang for num, lang in provider_num_lang_list}

        sql_query = (
            f"""SELECT {provider["zipfiles_num_column"]}, """
            f"""{provider["zipfiles_zipfile_column"]} """
            f"""FROM {provider["zipfiles_table"]} """
            f"""WHERE {provider["zipfiles_num_column"]} IN """
            f"""({", ".join(map(str, provider_num_list))})"""
        )
        if is_cli or is_debug:
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
                lang = lang_by_num[num]
                # return subtitle files with 3 letter codes: eng, ger, cze, ...
                lang = lang3letter(lang)
                (sub_path, sub_content) = extract_sub(zip_content, video_path_base, num, lang, args)
            else:
                (sub_path, sub_content) = (f"{num}.zip", zip_content)
            # no. dont require stream_zip here
            #from stream_zip import ZIP_32
            #yield (sub_path, modified_at, mode, ZIP_32, (sub_content,))
            # zip_fn = None
            zip_fn = stream_zip.ZIP_32
            yield (sub_path, modified_at, mode, zip_fn, (sub_content,))
            # found zipfile -> dont search other providers
        #print(f"""local provider {provider["id"]}: done""")


def extract_sub(zip_content, video_path_base, num, lang, args):
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
            file_base, ext = os.path.splitext(filename)
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
            sub_path = string.Template(args.path_format).safe_substitute(dict(
                # TODO keep in sync with path_format_vars
                video_path = args.movie,
                video_base = video_path_base,
                path = filename,
                base = file_base,
                ext = ext.removeprefix("."),
                # num = str(num),
                num = num,
                num0 = num_padded,
                lang = lang,
            ))
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



init()



if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        tb_str = "".join(traceback.format_exception(exc))
        error(f"{type(exc).__name__}: {exc}\n\n{tb_str}")
    sys.exit()
