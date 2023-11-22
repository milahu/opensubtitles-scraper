#! /usr/bin/env bash

num_downloads=10
num_downloads=2

./fetch-subs.py --proxy-provider chromium --num-downloads $num_downloads --first-num 9756545 --debug --start-vnc-client

add_files=./new-subs-repo/add-files.sh
if [ -x "$add_files" ]; then
  "$add_files" /run/user/$(id -u)/fetch-subs-*/home/Downloads/*.zip
  "$add_files" /run/user/$(id -u)/fetch-subs-*/home/Downloads/*.not-found
  "$add_files" /run/user/$(id -u)/fetch-subs-*/home/done_downloads/req*/*.zip
  "$add_files" /run/user/$(id -u)/fetch-subs-*/home/done_downloads/req*/*.not-found
  "$add_files" new-subs/*.zip
  "$add_files" new-subs/*.not-found
fi
