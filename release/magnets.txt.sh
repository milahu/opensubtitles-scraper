#!/usr/bin/env bash

set -e

cd "$(dirname "$0")"/..

output_path="release/magnets.txt"

echo "writing $output_path"
{

while read torrent_path; do

#magnetURI=$(torrenttools magnet "$torrent_path")
# short magnet link without trackers
magnetURI=$(torrenttools magnet "$torrent_path" | tr '&' $'\n' | grep -v ^tr= | tr $'\n' '&' | sed 's/&$//')

echo "$magnetURI"

done < <(
  # sort by torrent creation date, descending
  git ls-tree HEAD release/ |
  cut -d$'\t' -f2 |
  grep '\.torrent$' |
  while read torrent_path; do
    #timestamp=$(git log -n1 --format=format:%at -- "$torrent_path")
    timestamp=$(torrenttools show creation-date "$torrent_path")
    printf "%012d %s\n" "$timestamp" "$torrent_path"
  done |
  sort -n -r |
  cut -c14-
)

} >"$output_path"
