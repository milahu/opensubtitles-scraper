#!/bin/sh
cd new-subs
for f in *.zip; do s=$(stat -c%s "$f"); [ $s = 0 ] && { mv -v "$f" "${f%.*}.not-found"; }; done
