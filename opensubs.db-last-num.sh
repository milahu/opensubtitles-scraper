#! /bin/sh
sqlite3 opensubs.db "select num from subz order by num desc limit 1;"
#9180517
