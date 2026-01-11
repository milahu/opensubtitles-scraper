#!/usr/bin/env bash

set -x

if [ -e fetch_subs_secrets.usernames.txt ]; then
  while true; do
    # no. sending too many requests gets our IP address blocked
    # retry loop to maximize downloads per day
    # for ((i=0; i<3; i++)); do
      for username in $(cat fetch_subs_secrets.usernames.txt); do
        # FIXME i cannot kill this process with control+C
        ./main.sh --username "$username"
        sleep 1m
      done
    # done
    date
    # fix:
    # If you will continue trying to download, <b>your IP will be blocked</b> by our firewall.
    # For more information read our <a href="/faq#antileech">FAQ</a> or contact us, if you think you should not see this error.
    # This deny will be removed after around 24 hours, so be patient.</div>
    sleep 24h
    # add some extra delay so our IP address is not blocked
    # opensubtitles.org is rather strict about their rate limits
    # waiting only 24 hours can get our IP address blocked
    # and we have to contact support to unblock it
    # see also: docs/dont-copy-our-website.md
    sleep 6h
  done
  exit # not reachable
fi

while true; do
  ./main.sh
  date
  sleep 6h
done
