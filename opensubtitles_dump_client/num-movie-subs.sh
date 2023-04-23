#! /bin/sh

time sqlite3 ../subtitles_all/opensubs-metadata.db 'select count() from subz_metadata where MovieKind = "movie"'

# 2088788 = 2_088_788
