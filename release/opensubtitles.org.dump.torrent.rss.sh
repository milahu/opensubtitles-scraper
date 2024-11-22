#!/usr/bin/env bash

# Torrent RSS feeds
# https://www.bittorrent.org/beps/bep_0036.html
# https://forum.qbittorrent.org/viewtopic.php?t=2531
# https://eztvx.to/ezrss.xml

# RSS
# https://www.rssboard.org/rss-specification
# https://validator.w3.org/feed/

set -e

cd "$(dirname "$0")"/..

rss_path="release/opensubtitles.org.dump.torrent.rss"

function escape_html() {
  echo "$1" | sed 's/&/\&amp;/g'
}

echo "writing $rss_path"
{

# ttl: number of minutes that indicates how long a channel can be cached before refreshing from the source
ttl=$((60 * 24 * 5)) # 5 days

done_first=false

cat <<EOF
<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0">
  <channel>
    <title>opensubtitles.org dump</title>
    <description>subtitles from opensubtitles.org</description>
    <link>https://github.com/milahu/opensubtitles-scraper</link>
    <copyright>public domain</copyright>
    <category>subtitles</category>
    <ttl>$ttl</ttl>
EOF

while read torrent_path; do

#torrent_filename="$(basename "$torrent_path")"

#torrent_filesize="$(stat -c%s "$torrent_path")"

#title="$torrent_filename"
# date in RFC2822 format
#pubDate=$(git log -n1 --format=format:%aD -- "$torrent_path")
timestamp=$(torrenttools show creation-date "$torrent_path")
pubDate=$(LC_ALL=C date --utc +"%a, %d %b %Y %H:%M:%S %z" -d"1970-01-01 00:00:00 +0000 + $timestamp seconds")

if ! $done_first; then
# The last time the content of the channel changed.
# torrents are sorted by author date, descending
# so the first torrent has the latest date
lastBuildDate="$pubDate"
cat <<EOF
    <lastBuildDate>$lastBuildDate</lastBuildDate>
EOF
fi

# If practical, the guid SHOULD be the info-hash of the torrent
# head -n1: "torrenttools show infohash" returns v1 and v2 hash
# for the most part, clients expect the GUID to simply be a unique identifier for this piece of content
guid=$(torrenttools show infohash "$torrent_path" | head -n1)

#contentLength=$(torrenttools show size "$torrent_path")

#magnetURI=$(torrenttools magnet "$torrent_path")
# short magnet link without trackers
magnetURI=$(torrenttools magnet "$torrent_path" | tr '&' $'\n' | grep -v ^tr= | tr $'\n' '&' | sed 's/&$//')

title=$(torrenttools show name "$torrent_path")

cat <<EOF
    <item>
      <title>$title</title>
      <pubDate>$pubDate</pubDate>
      <guid isPermaLink="false">$guid</guid>
      <enclosure type="application/x-bittorrent" url="$(escape_html "$magnetURI")"/>
    </item>
EOF

done_first=true

done < <(
  # sort by torrent creation date, descending
  {
    git ls-tree HEAD release/ |
    cut -d$'\t' -f2 |
    grep '\.torrent$'

    # also process not-yet committed torrent files
    for path in "$@"; do
      echo "$path"
    done
  } |
  while read torrent_path; do
    #timestamp=$(git log -n1 --format=format:%at -- "$torrent_path")
    timestamp=$(torrenttools show creation-date "$torrent_path")
    printf "%012d %s\n" "$timestamp" "$torrent_path"
  done |
  sort -n -r |
  cut -c14-
)

cat <<EOF
  </channel>
</rss>
EOF

} >"$rss_path"
