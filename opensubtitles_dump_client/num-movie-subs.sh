#! /bin/sh

time sqlite3 ../subtitles_all/subtitles_all.txt.gz-parse-result.db 'select count() from subz_metadata where MovieKind = "movie"'

# 2088788 = 2_088_788
