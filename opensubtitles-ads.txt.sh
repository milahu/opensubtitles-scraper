#! /usr/bin/env bash

set -e

# some ads have a length of 6 seconds or more
# but some ads are shorter

# also these textparts are ads:
# subtitles made by X
# translated by X
# someidiot@someprovider.com
# someidiot
# COPYRIGHT BY X
# [ENGLISH]

echo adding data to opensubs-find-ads.db
python -u find_ads.py | tee -a find_ads.py.log

echo getting textparts from opensubs-find-ads.db
last_idx=$(sqlite3 opensubs-find-ads.db "select max(idx) from subs_textparts")
offset=$((last_idx - 1000))
sqlite3 opensubs-find-ads.db "select idx, sub, pos, len, txt from subs_textparts limit 1000 offset $offset"

echo hit enter to start copying the clipboard
read
echo background: adding clipboard contents to $tempfile every second
tempfile=/run/user/$(id -u)/opensubs-ads.txt
l="$(xclip -o)"
while true; do
  sleep 1
  c="$(xclip -o)"
  if [ "$l" = "$c" ]; then
    # no change
    continue
  fi
  # TODO Better? still seems to allow garbage input
  if ! echo "$c" | grep -qE '^([0-9]+)\|([0-9]+)\|(-?[0-9]+)\|([0-9]+)\|'; then
    # no subtitle
    continue
  fi
  l="$c"
  echo "$c" | sed -E 's/^([0-9]+)\|([0-9]+)\|(-?[0-9]+)\|([0-9]+)\|(.*)$/\5|\4|\3|\2/' >>$tempfile
done &
pid=$!

echo "use triple-click to select lines with ads (and wait 1 second)"
echo hit enter to stop copying the clipboard
read

echo killing the clipboard copier
kill $pid

echo merging $tempfile with ads.txt
cat ads.txt $tempfile | LC_ALL=C sort -u | sponge ads.txt

rm $tempfile
