#!/bin/sh

min_count=1000

set -e

cd done-zips

for zip in *.zip; do

base=${zip%.*}

[ -e "../unpacked-zips/$base" ] && continue

echo $base
unzip -q -B "$zip" -d "../unpacked-zips/$base"

count=$(ls ../unpacked-zips/ | wc -l)
((count >= min_count)) && break

done
