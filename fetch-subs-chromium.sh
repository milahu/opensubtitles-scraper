#! /usr/bin/env bash

./fetch-subs.py --proxy-provider chromium --num-downloads 10 --first-num 9756545 --debug --start-vnc-client

add_files=./new-subs-repo/add-files.sh
if [ -x "$add_files" ]; then
  "$add_files" /run/user/$(id -u)/*-fetch-subs*home/Downloads/*.zip
fi
