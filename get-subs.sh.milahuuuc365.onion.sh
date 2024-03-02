#!/usr/bin/env bash
# get-subs.sh - get subtitles from subtitles server
server_url="http://milahuuuc3656fettsi3jjepqhhvnuml5hug3k7djtzlfe4dw6trivqd.onion/bin/get-subtitles"
curl=(curl --proxy socks5h://127.0.0.1:9050)
command -v curl >/dev/null || { echo "error: curl was not found"; exit 1; }
command -v unzip >/dev/null || { echo "error: unzip was not found"; exit 1; }
[ -n "$1" ] || { echo "usage: $0 path/to/Scary.Movie.2000.720p.mp4"; exit 1; }
dir="$(dirname "$1")"
[ -e "$dir" ] || { echo "error: no such directory: ${dir@Q}"; exit 1; }
cd "$dir"
movie="$(basename "$1")"
if command -v bsdtar >/dev/null; then
  "${curl[@]}" -G -o - -d "movie=$movie" "$server_url" | bsdtar -xvf -
else
  zip="${movie%.*}.subs.zip"
  ! [ -e "$zip" ] || { echo "error: tempfile exists: ${zip@Q}"; exit 1; }
  "${curl[@]}" -G -o "$zip" -d "movie=$movie" "$server_url" && unzip "$zip" && rm "$zip"
fi
