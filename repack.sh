#! /usr/bin/env bash

set -e
set -u
#set -x # debug

# TODO get last id from done-zips folder
# $ ls done-zips/ | tail -n1
# 000001759.the.trouble.with.harry.(1955).cze.1cd.(1759).zip

batch_count=10

batch_size=10

# TODO lzham

# xz = lzm

# lrzip: frontend for bzip2, gzip, lzo, zpaq
# zpaq decompression is too slow per http://compressionratings.com/sort.cgi?s_enwik6.full+4n
# lzo is too large

# xwrt https://github.com/inikep/XWRT
# frontend for zlib (default), LZMA, PPMd, lpaq6

#codecs="brotli xz zstd deflate gzip bzip2 bzip3 7z lz4 rar"
codecs="cmix"

declare -A extension_map
extension_map[deflate]=zip
extension_map[brotli]=tar.br
extension_map[zstd]=tar.zst
extension_map[xz]=tar.xz
extension_map[gzip]=tar.gz
extension_map[bzip2]=tar.bz2
extension_map[bzip3]=tar.bz3
extension_map[7z]=7z
extension_map[lz4]=tar.lz4
extension_map[cmix]=tar.cmix
extension_map[rar]=rar # closed source. just for curiosity
# rar fails on non-utf8 filenames:
# Cannot open Indiana Jones Et La Derni+￾re Croissade - US.sr
# No such file or directory

zips_dir="zip-files"
unpacked_zips_dir="unpacked-zips"
repack_dir_prefix="repack/"
repack_tar_dir="tar-files"

# get absolute paths
zips_dir=$(readlink -f "$zips_dir")
unpacked_zips_dir=$(readlink -f "$unpacked_zips_dir")
repack_dir_prefix=$(readlink -f "$repack_dir_prefix")
repack_tar_dir=$(readlink -f "$repack_tar_dir")

mkdir -p $repack_tar_dir

start="${1:-1}"
last_sub_id="${2:-}"

if [ -z "$last_sub_id" ]; then
  last_sub_id="$(ls -N "$zips_dir" | sort | tail -n1 | sed -E 's/^0*([1-9][0-9]*)\..*$/\1/')"
fi
echo "last_sub_id: $last_sub_id"

for codec in $codecs; do
  output_dir="$repack_dir_prefix$codec"
  mkdir -p $output_dir
done

for ((sub_id=$start; sub_id<=$last_sub_id; sub_id++)); do

  # extract.py: name = f'{num:09d}.{name}'
  sub_id_str=$(printf "%09d\n" "$sub_id")
  #echo "sub_id_str: $sub_id_str"

  last_digit=${sub_id: -1}
  if ((sub_id % 100 == 0)); then
    printf "\n"
    printf "%s+" "$sub_id" # no leading space
  elif [ "$last_digit" = "0" ]; then # == ((sub_id % 10 == 0))
    printf " %s+" "$sub_id"
  fi
  printf "%s" "$last_digit"

  zip_file="$(ls -N $zips_dir/$sub_id_str.* 2>/dev/null || :)"
  if [ -z "$zip_file" ]; then continue; fi
  #echo "zip_file: $zip_file"

  base="$(basename "$zip_file" .zip)"

  unpacked_dir="$unpacked_zips_dir/$base"
  if ! [ -d "$unpacked_dir" ]; then
    rm -rf "$unpacked_dir.tmp"
    mkdir -p "$unpacked_dir.tmp"
    pushd "$unpacked_dir.tmp" >/dev/null
    # modification: rename duplicate files
    # example: 5 duplicate files:
    # some_file.txt
    # some_file.txt~
    # some_file.txt~1
    # some_file.txt~2
    # some_file.txt~3
    # zip archives can contain duplicate files
    # https://superuser.com/questions/224164/how-is-it-that-during-extraction-of-a-zip-i-get-two-files-of-the-same-name-in-t
    # https://stackoverflow.com/questions/22143908/python-zipfile-module-creates-multiple-files-with-same-name
    unzip -B -q "$zip_file"
    # rename duplicate files to restore file extension:
    # some_file.1.txt
    # some_file.2.txt
    # some_file.3.txt
    # some_file.4.txt
    # some_file.5.txt
    find . -name ".*~\d*"
    popd >/dev/null
    mv "$unpacked_dir.tmp" "$unpacked_dir"
  fi
  #echo "unpacked_dir: $unpacked_dir"

  # modification: convert files to utf8
  # TODO? unzip -a: auto-convert any text files
  # test IDs: 238
  rm -rf "$unpacked_dir.tmp"
  mv "$unpacked_dir" "$unpacked_dir.tmp"
  pushd "$unpacked_dir.tmp" >/dev/null
  while IFS= read -d '' file_path; do
    # convert file names to utf8
    # https://stackoverflow.com/questions/11530324/how-to-recursively-rename-files-and-folder-with-iconv-from-bash
    file_name=$(basename "$file_path")
    file_name_encoding=$(echo "$file_name" | chardetect --minimal)
    if [ "$file_name_encoding" != "ascii" ] && [ "$file_name_encoding" != "utf-8" ]; then
      #echo "file_name_encoding: $file_name_encoding"
      file_name_new=$(echo "$file_name" | iconv -f "$file_name_encoding" -t UTF8)
      if [ "$file_name" != "$file_name_new" ]; then
        file_dir=$(dirname "$file_path")
        mv "$file_dir/$file_name" "$file_dir/$file_name_new"
        file_path="$file_dir/$file_name_new"
        file_name="$file_name_new"
      fi
    fi
    [ -d "$file_path" ] && continue
    # convert file contents to utf8
    # pipe file content to stdin as workaround for
    # https://github.com/chardet/chardet/issues/278
    # the basename is converted at this point
    # but the dirname can still be non-utf8
    file_content_encoding=$(cat "$file_path" | chardetect --minimal)
    if [ "$file_content_encoding" != "ascii" ] && [ "$file_content_encoding" != "utf-8" ]; then
      #echo "file_content_encoding: $file_content_encoding"
      iconv -f "$file_content_encoding" -t UTF8 "$file_path" | sponge "$file_path"
    fi
  done < <(find . -depth -print0)
  popd >/dev/null
  mv "$unpacked_dir.tmp" "$unpacked_dir"

  tar_file="$repack_tar_dir/$base.tar"
  if ! [ -e "$tar_file" ]; then
    # TODO avoid cd
    rm -f "$repack_tar_dir/$base.tmp.tar"
    pushd "$unpacked_dir" >/dev/null
    tar cf "$repack_tar_dir/$base.tmp.tar" *
    popd >/dev/null
    mv "$repack_tar_dir/$base.tmp.tar" "$tar_file"
  fi

  for codec in $codecs; do

    #echo "codec: $codec"
    output_dir="$repack_dir_prefix$codec"
    extension="${extension_map[$codec]}"
    output_file="$output_dir/$base.$extension"

    [ -e "$output_file" ] && continue

    temp_file="$output_dir/$base.tmp.$extension"

    rm -f "$temp_file"

    case $codec in
      brotli)
        # TODO level 11?
        brotli -9 -k "$tar_file" -o "$temp_file"
        ;;
      zstd)
        # TODO level 22?
        zstd -19 -q "$tar_file" -o "$temp_file"
        ;;
      deflate)
        # TODO avoid cd
        pushd "$unpacked_dir" >/dev/null
        zip -9 -r -q "$temp_file" *
        popd >/dev/null
        ;;
      7z)
        # TODO avoid cd
        pushd "$unpacked_dir" >/dev/null
        7z a -mx9 "$temp_file" * >/dev/null
        popd >/dev/null
        ;;
      rar)
        # TODO avoid cd
        pushd "$unpacked_dir" >/dev/null
        rar a "$temp_file" * >/dev/null
        popd >/dev/null
        ;;
      bzip2)
        bzip2 -9 -k "$tar_file" --stdout >"$temp_file"
        ;;
      bzip3)
        # bzip3 has no levels
        bzip3 -k "$tar_file" --stdout >"$temp_file"
        ;;
      gzip)
        gzip -9 -k "$tar_file" --stdout >"$temp_file"
        ;;
      xz)
        xz -9 --extreme -k "$tar_file" --stdout >"$temp_file"
        ;;
      lz4)
        lz4 -9 -q "$tar_file" "$temp_file"
        ;;
      cmix)
        # https://github.com/byronknoll/cmix
        cmix -c "$tar_file" "$temp_file"
        ;;
      *)
        echo "unknown codec: $codec"
        exit 1
        ;;
    esac

    mv "$temp_file" "$output_file"

  done # codec

done # sub_id

exit

# fixme: iconv: failed to start conversion processing

308
iconv: failed to start conversion processing

311
iconv: failed to start conversion processing

406
iconv: illegal input sequence at position 170

407
iconv: illegal input sequence at position 356

420
iconv: failed to start conversion processing

459
iconv: failed to start conversion processing
iconv: failed to start conversion processing

465
iconv: illegal input sequence at position 4019

466
iconv: illegal input sequence at position 243

555
iconv: illegal input sequence at position 312

594
iconv: illegal input sequence at position 4143

596
iconv: failed to start conversion processing

624
iconv: illegal input sequence at position 34
iconv: illegal input sequence at position 202

646
iconv: failed to start conversion processing

649
iconv: illegal input sequence at position 7325

775
iconv: illegal input sequence at position 299

800
iconv: failed to start conversion processing

801
iconv: failed to start conversion processing

816
iconv: failed to start conversion processing

818
iconv: illegal input sequence at position 13072

822
iconv: illegal input sequence at position 11583

825
iconv: illegal input sequence at position 14189

862
iconv: illegal input sequence at position 129

872
iconv: failed to start conversion processing

884
iconv: illegal input sequence at position 995

886
iconv: illegal input sequence at position 7198

897
iconv: failed to start conversion processing

921
iconv: illegal input sequence at position 813

934
iconv: illegal input sequence at position 34757

936
iconv: illegal input sequence at position 170

948
iconv: failed to start conversion processing

964
iconv: illegal input sequence at position 148

976
iconv: illegal input sequence at position 1424

1060
iconv: failed to start conversion processing

1061
iconv: failed to start conversion processing

1085
iconv: illegal input sequence at position 496

1118
iconv: illegal input sequence at position 10883




