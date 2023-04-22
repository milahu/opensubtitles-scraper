both deluge and tribler are based on libtorrent

https://github.com/deluge-torrent/deluge/blob/develop/requirements.txt

https://github.com/Tribler/tribler/blob/main/requirements-core.txt

... so we use libtorrent

## todo

all operations MUST be reproducible (bit-exact)
so the same result can be derived from the original data

### create a new torrent

#### split by language

split the database by language

real-world users are interested only in some languages

similar: hunspell dictionaries are split by language

todo: split the torrent by language

#### smaller chunk size

average file has 20 KBytes

current chunk size is 16 MBytes = 8000 chunks = 800 files per chunk

chunk size should be more like 1 MByte = 128000 chunks = 50 files per chunk

smaller chunks reduce the overhead of fetching only some files

#### different file format

sqlite is nice but overkill

use something simple like tar (tar --seek?)

split into multiple smaller files, so ...

- it works with old filesystems like FAT32 (max 4 GBytes)
- files are easy to send over network (around 1 GByte)
- files are fast to hash (around 1 GByte)

the archive should be "append only"
so all previous parts/chunks/pieces/blocks are immutable
so its trivial to create new torrents with more files

##### sort order

sort subtitles by movie name

real-world users are interested only in some movies

sorting by movie name reduces the overhead of fetching only some files
because interesting files are packed together

#### repack files

con: too expensive?

maybe repack the zip files

bzip2? 7z? brotli? zstd?

optimize for small size and fast decompression

on filename collisions, rename files (zip -B)

##### compression algo

the winner is: bzip2

- 30% smaller than the original zip files
- still 20% smaller than the best zip compression (repack-deflate) (zip -9)
- fast decompression, as fast as zip

compressed size:

```
$ ./repack-size.sh
14267891        repack-bzip3
15491495        repack-bzip2    # 30.7% smaller
15590956        repack-7z
15993304        repack-xz       # 28.5% smaller
17940041        repack-zstd     # 19.8% smaller
18799059        repack-brotli   # 16.0% smaller
18837551        repack-rar      # 15.8% smaller
19635889        repack-deflate  # 12.2% smaller
19828323        repack-gzip     # 11.4% smaller
22369830        original-zips   # reference
24882747        repack-lz4
```

decompression speed:

```
$ ./repack-speed.sh 1 1000 | sort -n
22 repack-brotli
24 repack-xz
25 repack-bzip2
27 original-zips
28 repack-deflate
28 repack-gzip
46 repack-7z       # too slow
123 repack-bzip3   # too slow
```

#### recode files to unicode

recode filenames and file-contents to utf8

utf8 is de-facto standard for text files

use python3.pkgs.chardet to detect encoding

detect encoding of filenames:

```
$ ( cd unpacked-zips/000000262.*/ && find . ) | chardetect --minimal
ISO-8859-1
```

problem: bug in chardet: filenames must be utf8

```
$ chardetect unpacked-zips/000000262.*/*.srt
Traceback (most recent call last):
  File "/nix/store/jnf6k84m7qp46bhs83ca92qwjwfkc57v-python3.10-chardet-5.1.0/bin/.chardetect-wrapped", line 9, in <module>
    sys.exit(main())
  File "/nix/store/jnf6k84m7qp46bhs83ca92qwjwfkc57v-python3.10-chardet-5.1.0/lib/python3.10/site-packages/chardet/cli/chardetect.py", line 104, in main
    print(
UnicodeEncodeError: 'utf-8' codec can't encode character '\udcbf' in position 106: surrogates not allowed
```

workaround: pipe file contents to stdin

```
$ cat unpacked-zips/000000262.*/*.srt | chardetect --minimal
utf-8
```
