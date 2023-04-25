#!/bin/sh

num_done=$(ls new-subs | wc -l)

num_total=1000000

progress=$(echo $num_done $num_total | awk '{ print $1/$2*100 }')

echo $(date +"%F %T") $progress%
