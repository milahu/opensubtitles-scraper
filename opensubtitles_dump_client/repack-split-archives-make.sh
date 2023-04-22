#! /bin/sh

find . -mindepth 1 -maxdepth 1 -type d -not -name split-archives | while read d
do

mkdir -p split-archives/zip
cd "$d"
zip "../split-archives/zip/$d.zip" *
cd ..

mkdir -p split-archives/7z
cd "$d"
7z a "../split-archives/7z/$d.7z" *
cd ..

mkdir -p split-archives/tar
cd "$d"
tar cf "../split-archives/tar/$d.tar" *
cd ..

mkdir -p split-archives/bz2
bzip2 -k -c "split-archives/tar/$d.tar" >"split-archives/bz2/$d.tar.bz2"

mkdir -p split-archives/bz3
bzip3 -k -c "split-archives/tar/$d.tar" >"split-archives/bz3/$d.tar.bz3"

mkdir -p split-archives/gz
gzip -k -c "split-archives/tar/$d.tar" >"split-archives/gz/$d.tar.gz"

mkdir -p split-archives/xz
gzip -k -c "split-archives/tar/$d.tar" >"split-archives/xz/$d.tar.xz"

done
