#!/usr/bin/env bash

sqlite3 opensubs-metadata.db "select substr(SubAddDate, 0, 5) as year, count(1) from subz_metadata group by year" >docs/subs-added-by-year.txt
sqlite3 opensubs-metadata.db "select substr(SubAddDate, 0, 8) as month, count(1) from subz_metadata group by month" >docs/subs-added-by-month.txt
sqlite3 opensubs-metadata.db "select substr(SubAddDate, 0, 11) as day, count(1) from subz_metadata group by day" >docs/subs-added-by-day.txt
