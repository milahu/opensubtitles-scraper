#!/usr/bin/env bash

# fetch + commit + push subtitles

# usage:
# while true; do timeout -k 60 3600 ./main.sh; sleep 6h; done

# note: timeout is needed because fetch-subs.py can hang forever

set -x

min_release_id=103 # ignore old files in opensubtitles-scraper-new-subs/shards/

fetch_subs_timeout=3600 # 1 hour
fetch_subs_kill_timeout=60 # 1 minute

# fetch-subs.py
#   tempdir = f"/run/user/{os.getuid()}"
#   tempdir = tempdir + f"/fetch-subs-{datetime_str()}"
tempdir_prefix=/run/user/$UID/fetch-subs-

cd "$(dirname "$0")"

grep $'^\tpath = ' .gitmodules | cut -c9- | while read path; do
  if [ "$(stat -c%F "$path")" != "directory" ]; then
    echo "error: missing gitmodule $path. hint: git submodule update --init"
    exit 1
  fi
done

if [ -x ./opensubtitles-scraper-new-subs/mount-branches.sh ]; then
  # mount all "shard" branches in opensubtitles-scraper-new-subs/shards/
  ./opensubtitles-scraper-new-subs/mount-branches.sh
fi

# infinite loop: run the scraper every 6 hours
# while true; do

  # write missing_numbers.txt for fetch-subs.py
  # so we can finish nearly-complete shards
  ./new-subs-list-missing-files.sh

  # download subtitles_all.txt.gz and initialize subtitles_all.db
  #   fetch new subs to new-subs/
  #   the scraper can hang (fixme) so we kill it after $fetch_subs_timeout seconds
  # headless mode is blocked by cloudflare -> http 403
  # https://github.com/kaliiiiiiiiii/Selenium-Driverless/issues/343
  # ./fetch-subs.py "$@"
  # FIXME chrome window can stay open
  timeout --kill-after="$fetch_subs_kill_timeout" "$fetch_subs_timeout" \
  ./fetch-subs.py --headful-chromium "$@"
  # TODO if the scraper always hangs, debug it with
  #   ./fetch-subs.py --headful-chromium

  # workaround: kill leftover chromium processes
  # FIXME all chromium processes should be killed in cleanup of aiohttp_chromium
  echo "killing leftover chromium processes"
  ps -AF | grep "user-data-dir=$tempdir_prefix" | grep chromium | awk '{ print $2 }' | xargs -r kill

  # workaround: remove leftover tempdirs
  # FIXME all tempdirs should be removed in cleanup of aiohttp_chromium
  echo "removing leftover tempdirs"
  rm -rf "$tempdir_prefix"*

  # move new-subs/* to opensubtitles-scraper-new-subs/shards/*xxxxx/*xxx.db
  ./new-subs-repo-git2sqlite.py
  # create release

  # create release db and torrent files
  ./shards2release.py --min-release-id "$min_release_id"

  # add new torrents to git
  # "new" torrent files are untracked by git
  git ls-files --others --exclude-standard |
  grep -E -x 'release/opensubtitles.org.dump.[a-z0-9.]+.torrent' |
  while read -r torrent_path; do
    ./release_add_to_git.py $torrent_path
  done

  # publish new torrents to reddit
  if ! [ -e release/reddit-posts.json ]; then
    echo "FIXME missing release/reddit-posts.json"
  else
    done_torrent_files="$(
      cat release/reddit-posts.json |
      jq -r '
        .[] | select(. != null) |
        if .torrent_path then .torrent_path else (.torrent_paths | .[]) end
      ' |
      LANG=C sort
    )"
    all_torrent_files="$(ls release/*.torrent | LANG=C sort)"
    new_torrent_files="$(
      diff <(echo "$done_torrent_files") <(echo "$all_torrent_files") |
      grep '^> ' | cut -c3-
    )"
    if [ -n "$new_torrent_files" ]; then
      for torrent_path in $new_torrent_files; do
        ./reddit_add_torrent.py $torrent_path
      done
    fi
  fi

  # publish temporary files
  ./opensubtitles-scraper-new-subs/add-shards.sh
  ./opensubtitles-scraper-new-subs/git-push.sh

  # print download progress for each release
  shards_path=opensubtitles-scraper-new-subs/shards
  ls "$shards_path" | grep -xE '[0-9]+xxxxx' | sort -n | while read shard_name; do
    shard_progress=$(ls "$shards_path/$shard_name" | wc -l)
    echo "$shards_path/$shard_name: done $shard_progress of 100 shards"
  done
  new_subs_path=new-subs
  if [ -d "$new_subs_path" ]; then
    n=$(ls "$new_subs_path" | wc -l)
    echo "$new_subs_path: done $n zipfiles = $((n / 1000)) shards"
  fi

  # done loop step
  exit

  date
  echo "sleeping 6 hours ..."
  sleep 6h
# done
