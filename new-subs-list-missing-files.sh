#!/usr/bin/env bash

set -e

new_subs_repo_shards_dir="opensubtitles-scraper-new-subs"

debug=false
# debug=true

# TODO simplify?
# diff <(seq 10305000 10305999) <(ls new-subs/10305* | cut -c10-17 | sort -n -u) | grep '^< ' | cut -c3-

debug_not_missing_zipfile_num=
# debug_not_missing_zipfile_num=10305138
# 10305138 is not missing:
# $ ls new-subs/10305138*
# 'new-subs/10305138.5ive.days.to.midnight.(2004).ara.1cd.zip'
#
# values get lost between "ls new-subs/ | sort -n" and "while read zipfile_path"
# but there is no "read" inside the "while read zipfile_path" loop
#
# zipfile_num: 10305136
# loop_num: 129 -- zipfile_path: 10305137.the.middle.s01.e24.average.rules.(2010).nor.1cd.zip
# zipfile_num: 10305137
# loop_num: 130 -- zipfile_path: 10305139.the.exorcist.iii.(1990).per.1cd.zip
# zipfile_num: 10305139
# missing zipfiles between 10305137 and 10305139 = 1 zipfiles are missing
# missing_zipfile_num 10305138
# FIXME zipfile is not missing: 10305138
#
# blame "sort -n"
#
# test:
# printf "10305138.5\n10305137.t\n10305139.t\n10319013.s\n10305703.8\n" | LANG=C sort -n
# printf "10305138.5\n10305137.t\n10305139.t\n10319013.s\n10305703.8\n" | LANG=C sort -n -k1,1 -t.
#
# fix: "sort -n" -> "sort -n -k1,1 -t."
# note: -k1 means field 1 to end of line. -k1,1 means only field 1

min_release_id=100 # ignore release 74
next_release_id="$1"
if [ -z "$next_release_id" ]; then
  next_release_id=100 # ignore release 74
  while read release_id; do
    if ((release_id < min_release_id)); then continue; fi
    # is this release complete?
    num_shards=$(ls "$new_subs_repo_shards_dir/shards/${release_id}xxxxx/${release_id}"[0-9][0-9]xxx.db | wc -l)
    if ((num_shards < 100)); then
      next_release_id=$release_id
      break
    fi
  done < <(
    ls "$new_subs_repo_shards_dir/shards" |
    grep -E -x '[0-9]+xxxxx' | sed 's/x//g' | sort -n
  )
fi
echo "next_release_id: $next_release_id"

debug_zipfile_num=
# debug_zipfile_num=10294000
debug_shard_num=
if [ -n "$debug_zipfile_num" ]; then
  debug_shard_num="${debug_zipfile_num:0: -3}"
  echo "debug_zipfile $debug_zipfile_num: shard $debug_shard_num"
fi

workdir="$PWD"

cd "$(dirname "$0")"

last_shard_id=
first_shard_id=
num_zipfiles_missing=0
total_num_files_missing=0
missing_zipfiles_list=""

# filter
# opensubtitles.org.dump.9180519.to.9521948.by.lang.2023.04.26
# opensubtitles.org.dump.9700000.to.9799999
min_shard_id=9521
min_shard_id=9520
min_shard_id=9500
min_shard_id=9800
min_shard_id=${next_release_id}00

#last_shard_id=$min_shard_id

shard_id=
last_shard_id_in_sequence=

done_shards=""

# find last shard in steady sequence
while read shard_path; do

  shard_id=${shard_path##*/}
  shard_id=${shard_id%xxx.db}

  ((shard_id < min_shard_id)) && continue

  #echo "shard_id $shard_id"

  if [ -z "$first_shard_id" ]; then
    first_shard_id=$shard_id
  fi

  if [ -n "$last_shard_id" ]; then
    if [ -z "$last_shard_id_in_sequence" ]; then
      if ((shard_id - last_shard_id != 1)); then
        # found first outlier after steady sequence
        last_shard_id_in_sequence=$last_shard_id
        done_shards="$shard_id"
      fi
    else
      # shard after last_shard_id_in_sequence
      done_shards+=" $shard_id"
    fi
  fi

  last_shard_id=$shard_id

done < <(
  #find shards/ -name '*.db' | LANG=C sort
  ls "$new_subs_repo_shards_dir"/shards/*xxxxx/*xxx.db | LANG=C sort --version-sort
)

if [ -z "$last_shard_id_in_sequence" ]; then
  last_shard_id_in_sequence=$shard_id
fi

echo "last_shard_id_in_sequence: $last_shard_id_in_sequence"



min_shard_id=$last_shard_id_in_sequence

min_zipfile_num=$((min_shard_id * 1000))
#last_zipfile_num=$min_zipfile_num
last_zipfile_num=

echo "min_shard_id: $min_shard_id"
echo "min_zipfile_num: $min_zipfile_num"
# FIXME shard 10294: missing num 10294000
# next_release_id: 102
# min_shard_id: 10293
# min_zipfile_num: 10293000

declare -A missing_zipfiles_by_shard

loop_num=0

while read zipfile_path; do

  if $debug; then
    loop_num=$((loop_num + 1))
    echo "loop_num: $loop_num -- zipfile_path: $zipfile_path"
  fi

  zipfile_num=${zipfile_path##*/}
  zipfile_num=${zipfile_num%%.*}

  if ((zipfile_num < min_zipfile_num)); then
    if $debug; then
      echo "ignoring too-low zipfile_num: $zipfile_num"
    fi
    continue
  fi

  if $debug; then
    echo "zipfile_num: $zipfile_num"
  fi

  if [ -z "$last_zipfile_num" ]; then
    zipfile_shard_num="${zipfile_num:0: -3}"
    # FIXME this fails on zipfile_shard_num == 0
    prev_zipfile_shard_num=$((zipfile_shard_num - 1))
    # assume that the previous shard is complete
    last_zipfile_num=${prev_zipfile_shard_num}999
    echo "zipfile $zipfile_num: setting last_zipfile_num = $last_zipfile_num"
    #continue
  fi

  if ((zipfile_num - last_zipfile_num != 1)); then

    # zipfile_num 10310222: last 10310219
    # zipfile_num 10310222: seq 10310220 10310221

    num_zipfiles_missing_here=$((zipfile_num - last_zipfile_num - 1)) # TODO?
    num_zipfiles_missing=$((num_zipfiles_missing + num_zipfiles_missing_here))

    if $debug; then
      echo "missing zipfiles between $last_zipfile_num and $zipfile_num = $num_zipfiles_missing_here zipfiles are missing"
      # echo "missing zipfiles from $((last_zipfile_num + 1)) to $((zipfile_num - 1)) = $num_zipfiles_missing_here zipfiles are missing"
      # echo "seq $((last_zipfile_num + 1)) $((zipfile_num - 1))"
    fi

    zipfile_shard_num="${zipfile_num:0: -3}"
    #echo "zipfile $zipfile_num: shard $zipfile_shard_num"

    if [ "$zipfile_shard_num" = "$debug_shard_num" ]; then
      echo "zipfile $zipfile_num: last $last_zipfile_num"
      echo "zipfile $zipfile_num: seq $((last_zipfile_num + 1)) $((zipfile_num - 1))"
    fi

    for missing_zipfile_num in $(seq $((last_zipfile_num + 1)) $((zipfile_num - 1))); do

      #if [ "$zipfile_shard_num" = "$debug_shard_num" ]; then
      #  echo "zipfile $zipfile_num: missing $missing_zipfile_num"
      #  exit
      #fi

      shard_id=${missing_zipfile_num:0: -3}

      if [[ " $done_shards " == *" $shard_id "* ]]; then
        continue
      fi

      if $debug; then
        echo "missing_zipfile_num $missing_zipfile_num"

        if [ "$missing_zipfile_num" == "$debug_not_missing_zipfile_num" ]; then
          echo "FIXME zipfile is not missing: $missing_zipfile_num"
          exit 1
        fi

        # echo "shard_id $shard_id"
      fi

      #missing_zipfiles_list+="$missing_zipfile_num"$'\n'
      # TODO perf: exploit the fact that nums are sorted
      # add missing nums to this_shard_missing_zipfiles
      missing_zipfiles_by_shard[$shard_id]+="$missing_zipfile_num"$'\n'
    done

  fi

  if $debug; then
    :
    # echo "shard: $zipfile_shard_num -- zipfile_num: $zipfile_num -- last zipfile_num: $last_zipfile_num"
    # echo "done shard $zipfile_num"
    # echo "+ $zipfile_num"
  fi

  #last_zipfile_num=$zipfile_num
  last_zipfile_num=$zipfile_num

done < <(
  ls -U new-subs/ | LANG=C sort -n -k1,1 -t.
)


# sort ascending by nums-missing-per-shard
shard_id_list_sorted=$(
  for shard_id in ${!missing_zipfiles_by_shard[@]}; do
    num_missing_zipfiles=$(echo "${missing_zipfiles_by_shard[$shard_id]}" | wc -l)
    echo "$num_missing_zipfiles $shard_id"
  done |
  sort -n |
  cut -d' ' -f2
)

missing_zipfiles_list=
for shard_id in $shard_id_list_sorted; do
  missing_zipfiles_list+="${missing_zipfiles_by_shard[$shard_id]}"
done

#echo "first zipfile_num: $first_zipfile_num"
echo "last zipfile_num: $last_zipfile_num"
echo "missing zipfiles: $num_zipfiles_missing"

write_missing_zipfiles_list=false
write_missing_zipfiles_list=true

if $write_missing_zipfiles_list && [ -n "$missing_zipfiles_list" ]; then
  missing_files_path="missing_numbers.txt"
  echo "writing $missing_files_path"
  #echo -n "$missing_zipfiles_list" >"$workdir/$missing_files_path"
  num_first_missing=100
  num_first_missing=200
  # write only the first $num_first_missing missing

  #echo -n "$missing_zipfiles_list" | head -n$num_first_missing >"$workdir/$missing_files_path"
  # prefer to finish the next release
  echo -n "$missing_zipfiles_list" | grep ^$next_release_id | sort -n | head -n$num_first_missing >"$workdir/$missing_files_path"
  wc -l "$workdir/$missing_files_path"
fi
