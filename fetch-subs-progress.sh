#!/bin/sh

num_done=$(ls new-subs | wc -l)

num_total=1000000

progress=$(echo $num_done $num_total | awk '{ print $1/$2*100 }')

size=$(du -sm new-subs 2>/dev/null | cut -d$'\t' -f1)

projected_size=$(echo $size $progress | awk '{ print int($1/($2/100)) }')

echo $(date +"%F %T") $progress% = ${size}MB of ${projected_size}MB
