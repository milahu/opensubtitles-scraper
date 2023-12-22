#! /usr/bin/env bash

# daily quota for non-vip accounts
# can be bypassed by changing the IP address
num_downloads=200

./fetch-subs.py --proxy-provider chromium --num-downloads $num_downloads --first-num 9756545 --debug --start-vnc-client

./fetch-subs-add-zipfiles.sh
