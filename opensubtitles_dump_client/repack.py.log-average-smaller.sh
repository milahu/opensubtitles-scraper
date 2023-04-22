#!/usr/bin/env bash

prefix="^done tar "

sum=$((cat repack.py.log | grep "$prefix" | grep -E -o ' [0-9.]+% smaller$' | cut -d. -f1 | cut -d% -f1 | xargs printf "%s + "; echo 0; ) | bc)
num=$(cat repack.py.log | grep "$prefix" | wc -l)

echo $sum $num | awk '{ print($1 / $2) }'
