#!/bin/sh

sqlite3 opensubs-metadata.db "select IDSubtitle, SubAddDate from subz_metadata order by IDSubtitle desc limit 1" >last-sub-add-date.txt
