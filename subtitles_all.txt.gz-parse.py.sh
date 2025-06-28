#!/bin/sh

set -x # debug

subtitles_all_txt_gz_path="$subtitles_all_txt_gz_path"
if [ -n "$1" ]; then subtitles_all_txt_gz_path="$(realpath "$1")"; fi

# example: 20250628T17061751125070Z+0200
t=$(date -d "$(stat -c%x "$subtitles_all_txt_gz_path")" +%Y%m%dT%H%m%sZ%z)

metadata_db_path="opensubs-metadata.$t.db"
errfile="opensubs-metadata.$t.db.error.log"
dbgfile="opensubs-metadata.$t.db.debug.log"

subtitles_all_txt_subtitles_all_txt_gz_url="https://dl.opensubtitles.org/addons/export/subtitles_all.txt.gz"
table_name="subz_metadata"

if ! [ -e "$subtitles_all_txt_gz_path" ]; then
  echo "error: missing file: $subtitles_all_txt_gz_path"
  echo "please get it from $subtitles_all_txt_subtitles_all_txt_gz_url"
  exit 1
fi

# metadata_db_path = sys.argv[1]
# table_name = sys.argv[2]
# subtitles_all_txt_gz_path = sys.argv[3]
# errfile = sys.argv[4]
# dbgfile = sys.argv[5]

exec ./subtitles_all.txt.gz-parse.py "$metadata_db_path" "$table_name" "$subtitles_all_txt_gz_path" "$errfile" "$dbgfile"
