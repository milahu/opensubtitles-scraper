#! /bin/sh

set -u
set -e # debug

start=$1
last_sub_id=$2

codec=bzip3
repack_dir=repack/$codec
t1=$(date +%s)
for ((sub_id=$start; sub_id<=$last_sub_id; sub_id++)); do
sub_id_str=$(printf "%09d\n" "$sub_id")
compressed_file="$(ls -N $repack_dir/$sub_id_str.* 2>/dev/null || :)"
[ -z "$compressed_file" ] && continue
$codec -d -c -k "$compressed_file" >/dev/null
done
t2=$(date +%s)
dt=$((t2 - t1))
echo "$dt $repack_dir"

codec=bzip2
repack_dir=repack/$codec
t1=$(date +%s)
for ((sub_id=$start; sub_id<=$last_sub_id; sub_id++)); do
sub_id_str=$(printf "%09d\n" "$sub_id")
compressed_file="$(ls -N $repack_dir/$sub_id_str.* 2>/dev/null || :)"
[ -z "$compressed_file" ] && continue
$codec -d -c -k "$compressed_file" >/dev/null
done
t2=$(date +%s)
dt=$((t2 - t1))
echo "$dt $repack_dir"

codec=7z
repack_dir=repack/$codec
t1=$(date +%s)
for ((sub_id=$start; sub_id<=$last_sub_id; sub_id++)); do
sub_id_str=$(printf "%09d\n" "$sub_id")
compressed_file="$(ls -N $repack_dir/$sub_id_str.* 2>/dev/null || :)"
[ -z "$compressed_file" ] && continue
$codec x "$compressed_file" -so >/dev/null
done
t2=$(date +%s)
dt=$((t2 - t1))
echo "$dt $repack_dir"

codec=zip
#repack_dir=repack/$codec
repack_dir=original-zips
t1=$(date +%s)
for ((sub_id=$start; sub_id<=$last_sub_id; sub_id++)); do
sub_id_str=$(printf "%09d\n" "$sub_id")
compressed_file="$(ls -N $repack_dir/$sub_id_str.* 2>/dev/null || :)"
[ -z "$compressed_file" ] && continue
# tmpfs: minimal FS overhead
# p: extract to pipe (stdout)
unzip -p "$compressed_file" >/dev/null
done
t2=$(date +%s)
dt=$((t2 - t1))
echo "$dt $repack_dir"

codec=xz
repack_dir=repack/$codec
t1=$(date +%s)
for ((sub_id=$start; sub_id<=$last_sub_id; sub_id++)); do
sub_id_str=$(printf "%09d\n" "$sub_id")
compressed_file="$(ls -N $repack_dir/$sub_id_str.* 2>/dev/null || :)"
[ -z "$compressed_file" ] && continue
# tmpfs: minimal FS overhead
# p: extract to pipe (stdout)
$codec -d -c -k "$compressed_file" >/dev/null
done
t2=$(date +%s)
dt=$((t2 - t1))
echo "$dt $repack_dir"

codec=brotli
repack_dir=repack/$codec
t1=$(date +%s)
for ((sub_id=$start; sub_id<=$last_sub_id; sub_id++)); do
sub_id_str=$(printf "%09d\n" "$sub_id")
compressed_file="$(ls -N $repack_dir/$sub_id_str.* 2>/dev/null || :)"
[ -z "$compressed_file" ] && continue
# tmpfs: minimal FS overhead
# p: extract to pipe (stdout)
$codec -d -c -k "$compressed_file" >/dev/null
done
t2=$(date +%s)
dt=$((t2 - t1))
echo "$dt $repack_dir"

codec=gzip
repack_dir=repack/$codec
t1=$(date +%s)
for ((sub_id=$start; sub_id<=$last_sub_id; sub_id++)); do
sub_id_str=$(printf "%09d\n" "$sub_id")
compressed_file="$(ls -N $repack_dir/$sub_id_str.* 2>/dev/null || :)"
[ -z "$compressed_file" ] && continue
# tmpfs: minimal FS overhead
# p: extract to pipe (stdout)
$codec -d -c -k "$compressed_file" >/dev/null
done
t2=$(date +%s)
dt=$((t2 - t1))
echo "$dt $repack_dir"

codec=deflate
repack_dir=repack/$codec
t1=$(date +%s)
for ((sub_id=$start; sub_id<=$last_sub_id; sub_id++)); do
sub_id_str=$(printf "%09d\n" "$sub_id")
compressed_file="$(ls -N $repack_dir/$sub_id_str.* 2>/dev/null || :)"
[ -z "$compressed_file" ] && continue
# tmpfs: minimal FS overhead
# p: extract to pipe (stdout)
#$codec -d -c -k "$compressed_file" >/dev/null
unzip -p "$compressed_file" >/dev/null
done
t2=$(date +%s)
dt=$((t2 - t1))
echo "$dt $repack_dir"
