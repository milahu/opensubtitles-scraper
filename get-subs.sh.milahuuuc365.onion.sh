#!/usr/bin/env bash
# get-subs.sh - get subtitles from subtitles server
server_url="http://milahuuuc3656fettsi3jjepqhhvnuml5hug3k7djtzlfe4dw6trivqd.onion/bin/get-subtitles"
# note: this requires a running tor proxy on 127.0.0.1:9050 - hint: sudo systemctl start tor
curl=(curl --proxy socks5h://127.0.0.1:9050)
command -v curl >/dev/null || { echo "error: curl was not found"; exit 1; }
command -v unzip >/dev/null || { echo "error: unzip was not found"; exit 1; }
[ -n "$1" ] || { echo "usage: $0 path/to/Scary.Movie.2000.720p.mp4"; exit 1; }
dir="$(dirname "$1")"
[ -e "$dir" ] || { echo "error: no such directory: ${dir@Q}"; exit 1; }
cd "$dir"
movie="$(basename "$1")"
if command -v bsdtar >/dev/null; then
  # https://superuser.com/a/1834410/951886 # write error body to stderr
  "${curl[@]}" -G --fail-with-body -D - -o - --data-urlencode "movie=$movie" "$server_url" | {
    s=; while read -r h; do h="${h:0: -1}"; if [ -z "$s" ]; then s=${h#* }; s=${s%% *}; fi; [ -z "$h" ] && break; done
    if [ "${s:0:1}" = 2 ]; then cat; else cat >&2; fi
  } | bsdtar -xvf -
else
  zip="${movie%.*}.subs.zip"
  ! [ -e "$zip" ] || { echo "error: tempfile exists: ${zip@Q}"; exit 1; }
  if ! "${curl[@]}" -G --fail-with-body -o "$zip" --data-urlencode "movie=$movie" "$server_url"; then
    cat "$zip" && rm "$zip" # zip contains the error message
  else
    unzip "$zip" && rm "$zip"
  fi
fi
