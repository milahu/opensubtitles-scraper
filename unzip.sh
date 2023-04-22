#! /usr/bin/env bash

set -e
#set -x

# TODO get last id from done-zips folder
# $ ls done-zips/ | tail -n1
# 000001759.the.trouble.with.harry.(1955).cze.1cd.(1759).zip

batch_2_size=100

batch_size=100

for i in $(seq $batch_2_size); do

start=1

echo

if [ -d done-zips ]; then
  last_end=$(ls done-zips/ | sort | tail -n1 | cut -d. -f1 | sed -E 's/^0+//g')
elif [ -e last_end.txt ]; then
  last_end=$(cat last_end.txt)
else
  last_end=0 # first id is 1
fi
echo "last end: $last_end"

start=$((last_end + 1))

echo "start: $start"
echo "batch size: $batch_size"

end=$((start + batch_size))

echo "end: $end"

./extract.py -s $start -e $end -p zips

mkdir -p done-zips
mkdir -p unpacked-zips

while read -d$'\n' zipfile; do

printf .
#echo $zipfile
base="$(basename "$zipfile" .zip)"
if [ -d "unpacked-zips/$base" ]; then
  rm -rf "unpacked-zips/$base"
fi
mkdir "unpacked-zips/$base"
# B: backup = rename duplicate files
unzip -B -q "$zipfile" -d "unpacked-zips/$base"
mv "$zipfile" done-zips/
#break

done < <(find zips -mindepth 1 -maxdepth 1 -name "*.zip")

echo $end >last_end.txt

done
