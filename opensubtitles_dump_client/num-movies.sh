#! /bin/sh

# https://stackoverflow.com/questions/30248600/sql-count-number-of-groups

time sqlite3 ../subtitles_all/subtitles_all.txt.gz-parse-result.db 'select count(distinct MovieName) from subz_metadata where MovieKind = "movie"'

# 125269 = 125_269 # movie only

# 301457 = 301_457 # movie and tv
