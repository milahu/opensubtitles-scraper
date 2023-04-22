#!/bin/sh
cd new-subs
for f in *.zip; do unzip -l "$f" >/dev/null 2>&1 || mv "$f" "$f.broken"; done
