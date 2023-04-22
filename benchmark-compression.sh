#! /usr/bin/env bash

# https://peazip.github.io/peazip-compression-benchmark.html
# interesting candidates with fast extraction:
# rar: fast + small
# 7z: smaller than rar, slower compress
# zstd
# brotli
# zip

# todo:
# gzip
# bzip2
# xz

in=unpacked-zips
tempdir=/run/user/$(id -u)/benchmark-compression
mkdir -p $tempdir

set -e
for cmd in zip 7z rar tar gzip bzip2 xz brotli zstd; do
  if ! command -v $cmd >/dev/null 2>&1; then
    echo error: not found command $cmd
    exit
  fi
done

set -x
du -sh $in
set +x

# zip. default level 6
#for level in {1..9}; do
for level in {5..7}; do
out=$tempdir/$in.$level.zip
if ! [ -e $out ]; then
echo zip $level
set -x
time zip -r -q -$level $out $in
set +x
fi
done

# rar

