#!/usr/bin/env bash

add_files=./new-subs-repo/add-files.sh
if [ -x "$add_files" ]; then
  "$add_files" /run/user/$(id -u)/fetch-subs-*/home/Downloads/*.zip
  "$add_files" /run/user/$(id -u)/fetch-subs-*/home/Downloads/*.not-found
  "$add_files" /run/user/$(id -u)/fetch-subs-*/home/done_downloads/req*/*.zip
  "$add_files" /run/user/$(id -u)/fetch-subs-*/home/done_downloads/req*/*.not-found
  "$add_files" new-subs/*.zip
  "$add_files" new-subs/*.not-found
fi
