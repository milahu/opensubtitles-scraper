#! /bin/sh

set -u

start=$1
end=$2

for ((sub_id=$start; sub_id<=$end; sub_id++)); do

sub_id_str=$(printf "%09d\n" "$sub_id")

rm -rfv repack/*/$sub_id_str.*
rm -rfv unpacked-zips/$sub_id_str.*

done
