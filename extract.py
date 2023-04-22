#! /usr/bin/env python3

import sqlite3
import os
import argparse

con = sqlite3.connect("opensubs.db")
con.row_factory = sqlite3.Row


def save(name, file, path):
    with open("{}/{}".format(path, name), "wb") as w:
        w.write(file)


def get_range(start, end):
    with con:
        cur = con.cursor()
        cur.execute(
            "select * from subz where num >= (?) and num <= (?)",
            (
                start,
                end,
            ),
        )
        rows = cur.fetchall()
    return rows


def get_single(num):
    with con:
        cur = con.cursor()
        cur.execute("select * from subz where num = (?)", (num,))
        row = cur.fetchone()
    return row


##save all
##tmp_start=9200000
##while tmp_start >=0:
##    rows = get_range(tmp_start-1000, tmp_start)
##    tmp_start-=1000
##    for row in rows:
##        save(row['name'], row['file'])

# examples
##ten = get_range (0, 10)
##one = get_single(1    )
##print(one['name'])
##print('-')
##for row in ten:
##    print(row['name'])
####    save(row['name'], row['file'])

if __name__ == "__main__":
    print("main")
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--start", help="extract start", required=True)
    parser.add_argument(
        "-e", "--end", help="extract end (omit to extract one)", required=False
    )
    parser.add_argument("-p", "--path", help="path", required=False)
    args = vars(parser.parse_args())
    path = args.get("path") if args.get("path") else "./tmp"

    if not os.path.isdir(path):
        os.mkdir(path)
    if args.get("end"):
        rows = get_range(args.get("start"), args.get("end"))
        for row in rows:
            #print("row.name = " + repr(row["name"]))
            # row.name = 'attachment; filename="ghost.in.the.shell.2.innocence.(2004).eng.1cd.(3).zip"'
            name = row["name"][22:-1]
            num = row["num"]
            # 6 million subtitles = 6 000 000
            name = f'{num:09d}.{name}'
            #print("name = " + repr(name))
            save(name, row["file"], path)
    else:
        row = get_single(args.get("start"))
        #save(row["name"], row["file"], path)
        # TODO refactor
        if True:
            #print("row.name = " + repr(row["name"]))
            # row.name = 'attachment; filename="ghost.in.the.shell.2.innocence.(2004).eng.1cd.(3).zip"'
            name = row["name"][22:-1]
            num = row["num"]
            # 6 million subtitles = 6 000 000
            name = f'{num:09d}.{name}'
            #print("name = " + repr(name))
            save(name, row["file"], path)
