#! /bin/sh

mkdir -p original-zips
last_codec=rar # repack.sh: last codec in $codecs string
last_sub_id=$(ls -N "repack/rar" | sort | tail -n1 | sed -E 's/^0*([1-9][0-9]*)\..*$/\1/')
for (( sub_id=1; sub_id<=$last_sub_id; sub_id++ )); do
  sub_id_str=$(printf "%09d\n" "$sub_id")
  [ -e original-zips/$sub_id_str.* ] && continue
  ! [ -e zip-files/$sub_id_str.* ] && continue
  ln -sr zip-files/$sub_id_str.* original-zips/
done

du -sbL original-zips $(find repack/ -mindepth 1 -maxdepth 1 -type d) | sort -n
