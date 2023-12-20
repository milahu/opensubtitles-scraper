# asdf

## todo

### build index

compress index: 5 hours, 3 GB RAM, result 373 MB

```
Command being timed: "python -u index-compress.py group index.txt index.txt.grouped"
User time (seconds): 15802.22
System time (seconds): 1551.36
Percent of CPU this job got: 87%
Elapsed (wall clock) time (h:mm:ss or m:ss): 5:29:16
Average shared text size (kbytes): 0
Average unshared data size (kbytes): 0
Average stack size (kbytes): 0
Average total size (kbytes): 0
Maximum resident set size (kbytes): 3000672
Average resident set size (kbytes): 0
Major (requiring I/O) page faults: 202208
Minor (reclaiming a frame) page faults: 1240796
Voluntary context switches: 262176
Involuntary context switches: 9951274
Swaps: 0
File system inputs: 268106648
File system outputs: 25847664
Socket messages sent: 0
Socket messages received: 0
Signals delivered: 0
Page size (bytes): 4096
Exit status: 0
```

```
$ du -shc index.txt.grouped.* | sort -h | tail -n20
9.6M    index.txt.grouped.ger
9.8M    index.txt.grouped.heb
11M     index.txt.grouped.ara
11M     index.txt.grouped.hrv
11M     index.txt.grouped.rus
13M     index.txt.grouped.cze
13M     index.txt.grouped.ell
13M     index.txt.grouped.hun
13M     index.txt.grouped.scc
14M     index.txt.grouped.fre
14M     index.txt.grouped.ita
14M     index.txt.grouped.por
15M     index.txt.grouped.dut
16M     index.txt.grouped.tur
17M     index.txt.grouped.rum
20M     index.txt.grouped.pol
20M     index.txt.grouped.spa
26M     index.txt.grouped.pob
54M     index.txt.grouped.eng
373M    total
```

english; 54 of 373 = 14.47%

### repack

repack groups of files

group files by language and movie name, to maximize compression,
assuming that "same language" and "same movie"
will have very similar subtitle files (high redundancy)

general problem: how to group files?

criteria:

- good compression
- easy to append new files to collection

xz says: default compression level 6 is good for files up to 8MByte
so: make groups of 8MByte?

just use git? only group by language,
store uncompressed files in git.
file count is about 2.5 * 0.1 * 7M = about 2 million files
0.1 = fraction of english subs
2.5 = average files per zipfile. most/all zipfiles have a nfo file
git has the advantage of cheap updates
every day, there are 1200 new subs

### compress index

```py
import json
import pickle
f = open("index.txt.grouped_075.eng", "r")
d = json.load(f)
f = open("index.txt.grouped_075.eng.pickle", "wb")
pickle.dump(d, f)
```

```
cat index.txt.grouped_075.eng | jq -c >index.txt.grouped_075.eng.compact
gzip -k index.txt.grouped_075.eng{,.compact,.pickle}
bzip2 -k index.txt.grouped_075.eng{,.compact,.pickle}
```

```
$ du -sb index.txt.grouped_075.eng* | sort -n
6965742 index.txt.grouped_075.eng.pickle.bz2
7254055 index.txt.grouped_075.eng.bz2
7265530 index.txt.grouped_075.eng.compact.bz2
9511489 index.txt.grouped_075.eng.compact.gz
9715820 index.txt.grouped_075.eng.gz
9761924 index.txt.grouped_075.eng.pickle.gz
22176532        index.txt.grouped_075.eng.pickle
23536035        index.txt.grouped_075.eng.compact
25342668        index.txt.grouped_075.eng
```

... but bzip2 compression is slower than gzip

```
$ tar cf index.txt.grouped_078.tar index.txt.grouped_078*

$ $(which time) -v gzip -k index.txt.grouped_078.tar
        Command being timed: "gzip -k index.txt.grouped_078.tar"
        User time (seconds): 64.29
        System time (seconds): 2.50
        Percent of CPU this job got: 94%
        Elapsed (wall clock) time (h:mm:ss or m:ss): 1:10.96
        Average shared text size (kbytes): 0
        Average unshared data size (kbytes): 0
        Average stack size (kbytes): 0
        Average total size (kbytes): 0
        Maximum resident set size (kbytes): 3540
        Average resident set size (kbytes): 0
        Major (requiring I/O) page faults: 16
        Minor (reclaiming a frame) page faults: 491
        Voluntary context switches: 18
        Involuntary context switches: 29745
        Swaps: 0
        File system inputs: 485296
        File system outputs: 181736
        Socket messages sent: 0
        Socket messages received: 0
        Signals delivered: 0
        Page size (bytes): 4096
        Exit status: 0

$ $(which time) -v bzip2 -k index.txt.grouped_078.tar
        Command being timed: "bzip2 -k index.txt.grouped_078.tar"
        User time (seconds): 116.37
        System time (seconds): 4.63
        Percent of CPU this job got: 91%
        Elapsed (wall clock) time (h:mm:ss or m:ss): 2:11.60
        Average shared text size (kbytes): 0
        Average unshared data size (kbytes): 0
        Average stack size (kbytes): 0
        Average total size (kbytes): 0
        Maximum resident set size (kbytes): 7892
        Average resident set size (kbytes): 0
        Major (requiring I/O) page faults: 4
        Minor (reclaiming a frame) page faults: 1754
        Voluntary context switches: 7
        Involuntary context switches: 61114
        Swaps: 0
        File system inputs: 256
        File system outputs: 135496
        Socket messages sent: 0
        Socket messages received: 0
        Signals delivered: 0
        Page size (bytes): 4096
        Exit status: 0

$(which time) -v xz -k index.txt.grouped_078.tar
        Command being timed: "xz -k index.txt.grouped_078.tar"
        User time (seconds): 936.04
        System time (seconds): 31.56
        Percent of CPU this job got: 89%
        Elapsed (wall clock) time (h:mm:ss or m:ss): 18:02.87
        Average shared text size (kbytes): 0
        Average unshared data size (kbytes): 0
        Average stack size (kbytes): 0
        Average total size (kbytes): 0
        Maximum resident set size (kbytes): 96776
        Average resident set size (kbytes): 0
        Major (requiring I/O) page faults: 19
        Minor (reclaiming a frame) page faults: 27878
        Voluntary context switches: 50
        Involuntary context switches: 490143
        Swaps: 0
        File system inputs: 486032
        File system outputs: 119904
        Socket messages sent: 0
        Socket messages received: 0
        Signals delivered: 0
        Page size (bytes): 4096
        Exit status: 0

$(which time) -v 7z a index.txt.grouped_078.tar.7z index.txt.grouped_078.tar
        Command being timed: "7z a index.txt.grouped_078.tar.7z index.txt.grouped_078.tar"
        User time (seconds): 1026.33
        System time (seconds): 28.70
        Percent of CPU this job got: 219%
        Elapsed (wall clock) time (h:mm:ss or m:ss): 8:01.00
        Average shared text size (kbytes): 0
        Average unshared data size (kbytes): 0
        Average stack size (kbytes): 0
        Average total size (kbytes): 0
        Maximum resident set size (kbytes): 518780
        Average resident set size (kbytes): 0
        Major (requiring I/O) page faults: 80
        Minor (reclaiming a frame) page faults: 129754
        Voluntary context switches: 98629
        Involuntary context switches: 842305
        Swaps: 0
        File system inputs: 500080
        File system outputs: 117224
        Socket messages sent: 0
        Socket messages received: 0
        Signals delivered: 0
        Page size (bytes): 4096
        Exit status: 0

$(which time) -v brotli -k index.txt.grouped_078.tar
        Command being timed: "brotli -k index.txt.grouped_078.tar"
        User time (seconds): 3458.11
        System time (seconds): 103.68
        Percent of CPU this job got: 87%
        Elapsed (wall clock) time (h:mm:ss or m:ss): 1:08:13
        Average shared text size (kbytes): 0
        Average unshared data size (kbytes): 0
        Average stack size (kbytes): 0
        Average total size (kbytes): 0
        Maximum resident set size (kbytes): 237760
        Average resident set size (kbytes): 0
        Major (requiring I/O) page faults: 703
        Minor (reclaiming a frame) page faults: 108148
        Voluntary context switches: 1371
        Involuntary context switches: 2156285
        Swaps: 0
        File system inputs: 528120
        File system outputs: 113000
        Socket messages sent: 0
        Socket messages received: 0
        Signals delivered: 0
        Page size (bytes): 4096
        Exit status: 0

$(which time) -v zstd -k index.txt.grouped_078.tar
        Command being timed: "zstd -k index.txt.grouped_078.tar"
        User time (seconds): 14.64
        System time (seconds): 1.44
        Percent of CPU this job got: 100%
        Elapsed (wall clock) time (h:mm:ss or m:ss): 0:15.92
        Average shared text size (kbytes): 0
        Average unshared data size (kbytes): 0
        Average stack size (kbytes): 0
        Average total size (kbytes): 0
        Maximum resident set size (kbytes): 39352
        Average resident set size (kbytes): 0
        Major (requiring I/O) page faults: 12
        Minor (reclaiming a frame) page faults: 9453
        Voluntary context switches: 744
        Involuntary context switches: 6317
        Swaps: 0
        File system inputs: 485112
        File system outputs: 175368
        Socket messages sent: 0
        Socket messages received: 0
        Signals delivered: 0
        Page size (bytes): 4096
        Exit status: 0
```

```
Elapsed (wall clock) time (h:mm:ss or m:ss): 01:08:13.00 # brotli
Elapsed (wall clock) time (h:mm:ss or m:ss): 00:08:01.00 # 7z # fast
Elapsed (wall clock) time (h:mm:ss or m:ss): 00:18:02.87 # xz
Elapsed (wall clock) time (h:mm:ss or m:ss): 00:02:11.60 # bzip2
Elapsed (wall clock) time (h:mm:ss or m:ss): 00:00:15.92 # zstd
Elapsed (wall clock) time (h:mm:ss or m:ss): 00:01:10.96 # gzip

Maximum resident set size (kbytes): 237760 # brotli
Maximum resident set size (kbytes): 518780 # 7z
Maximum resident set size (kbytes): 96776 # xz # small
Maximum resident set size (kbytes): 7892 # bzip2
Maximum resident set size (kbytes): 39352 # zstd
Maximum resident set size (kbytes): 3540 # gzip
```

```
$ du -b index.txt.grouped_078.tar* | sort -n
57855084        index.txt.grouped_078.tar.br # 23.39% # small
60004828        index.txt.grouped_078.tar.7z # 24.26% # small
61389432        index.txt.grouped_078.tar.xz # 24.82% # small
69371519        index.txt.grouped_078.tar.bz2 # 28.05%
89787262        index.txt.grouped_078.tar.zst # 36.30%
93046620        index.txt.grouped_078.tar.gz # 37.62%

247306240       index.txt.grouped_078.tar # 100%

$ du -h index.txt.grouped_078.tar* | sort -h
56M     index.txt.grouped_078.tar.br
58M     index.txt.grouped_078.tar.7z
59M     index.txt.grouped_078.tar.xz
67M     index.txt.grouped_078.tar.bz2
86M     index.txt.grouped_078.tar.zst
89M     index.txt.grouped_078.tar.gz
236M    index.txt.grouped_078.tar
```

### uncompressed index on github

store the uncompressed index on github

provide compressed index as github releases?

downside: overall, this requires more disk space

most space-efficient solution is to store plaintext in git
and let git handle all the compression

git's gzip compression is not the best, but its fast,
and it can compress across multiple versions (commits, snapshots)

### repack subs

- group by movie to increase compression
- convert to utf8 (detect encoding with libmagic)
- compress with bzip2?
- maybe use extra metadata from subtitles_all.txt.gz

brotli is too slow, lzma/xz/7z wins

grouped archives: smallest is 0.44MB

```
$ du -b *tar* | sort -n
435647  alien 3 (1992).tar.br
453006  alien 3 (1992).tar.lzma
453120  alien 3 (1992).tar.xz # lzma2, level 6
473767  alien 3 (1992).tar.7z
550615  alien 3 (1992).tar.bz3
827642  alien 3 (1992).tar.bz2
858960  alien 3 (1992).tar.zst
1905106 alien 3 (1992).tar.gz
1905255 alien 3 (1992).tar.zip
5345280 alien 3 (1992).tar
```

split archives: smallest is 1.35MB

```
$ ./repack-split-archives-make.sh
$ du -sb split-archives/* | sort -n
1353127 split-archives/bz3
1479655 split-archives/bz2
1540377 split-archives/7z
1930617 split-archives/gz
1930617 split-archives/xz
1947465 split-archives/zip
5663760 split-archives/tar
```

#### group by movie name only

everything else is too complex
and makes sharing harder

torrent v2 can share identical files between multiple swarms

so lets make it simple:

one archive per movie.
when subs are added or removed, create a new archive per movie,
and create a new torrent with the new archive only

so, no fancy "hybrid grouping by movie name and sub number".
only one grouping: grouping by movie name.

so currently, i get 300K archives (many small files)

https://www.reddit.com/r/compsci/comments/168va6/bittorrent_doesnt_handle_small_files_efficiently/

TODO reduce number of archives by grouping seasons of TV shows
real-world use case: user has one season of a TV show and needs subtitles for all episodes
benefits: less archives, better compression

#### try larger groups

group movies by partial hash of movie name (movie name hash)

```py
import binascii

def crc16_xmodem(data: bytes, init_value=0):
  return binascii.crc_hqx(data, init_value)

def get_movie_group(movie_name):
    """
    16bit movie_group
    TODO use md5/sha1 for better distribution?
    """
    movie_group = crc16_xmodem(movie_name.encode("utf8"))
    movie_group_hex = f"{movie_group:04x}"
    return movie_group_hex

def get_movie_group_12bit(movie_name):
    """
    first 3 chars of 16bit movie_group
    TODO use last 3 chars?
    """
    return get_movie_group(movie_name)[0:3]
```

how many groups?

```
2Byte = 16bit: 2**16 = 65536

1.5Byte = 12bit: 2**12 = 4096

1Byte = 8bit: 2**8 = 256
```

how many subs per group?

```
2023-04-18: opensubtitles.org: 6633435 subtitles

16bit: 6633435/2**16 = 101

12bit: 6633435/2**12 = 1620

8bit: 6633435/2**8 = 25912
```

so: 12bit looks interesting,
16bit has too few subs per group (lower compression)
8bit has too many subs per group (large archives are less handy)

goal: better compression

problem: larger files are less handy

#### try grouping by sub number

example: group every 1000 subs

group 1: subs 1 to 1000

group 2: sub 1001 to 2000

group 3: sub 2001 to 3000

...

this makes it easy to append new subs to the collection
because new subs are sorted by sub number

### checksums of zip files

collect checksums of all the original zip files

useful for verification?

## filesystem

```
goal: compressed append-only filesystem with spatial and temporal grouping of files
hybrid grouping: spatial and temporal grouping
spatial grouping of files = group subs by movie name
  because read-access will request all files from one group
  = request all subs for one movie
temporal grouping of files = append updates
  old blocks must be immutable for P2P sharing

query: compressed append-only p2p network filesystem with spatial and temporal grouping of files append updates old blocks are immutable

alternatives:
apache hadoop
https://github.com/MTInformationalRepos/append-only-torrent
https://github.com/hypercore-protocol/hyperdrive
zfs
https://www.reddit.com/r/DataHoarder/comments/bn1f8j/introducing_datahoardercloud_a_new_standard_for/
  He's basically describing LBRY, Storj or Maidsafe.
  Or Sia, which is actually usable today.
  https://www.storj.io/ # closed source
  https://sia.tech/ # foss, cloud storage, private data, encrypted
  https://tahoe-lafs.org/trac/tahoe-lafs # cloud storage
  https://ipfs.tech/ # bittorrent over TCP -> bad performance

similar projects:
https://www.reddit.com/r/DataHoarder/comments/s6xueq/thingiverse_0000000000249999_files_images_and/
  200GB total
https://www.reddit.com/r/DataHoarder/comments/jb1hkn/p2p_free_library_help_build_humanitys_free/
  over 2.5 million scientific textbooks and 2.4 million fiction novels
  80 million articles of Sci-Hub
  A single CID of 1,000 books is only about 5GB. One shelf at a time :)
  https://freeread.org/torrents
    each torrent containing 1,000 books
  https://www.reddit.com/r/DataHoarder/comments/ed9byj/library_genesis_project_update_25_million_books/
  [they seem to prefer torrent over ipfs, probably for performance]

https://www.reddit.com/r/DataHoarder/comments/8hoj84/what_p2p_services_exist_to_participate_in/
  https://github.com/en3r0/awesome-distributed/tree/master#disk
    https://wiki.archiveteam.org/index.php/Dev/Infrastructure
    https://wiki.archiveteam.org/index.php/Dev/New_Project
    https://wiki.archiveteam.org/index.php/Dev/Seesaw
```

## archive format

wanted specs

- compression
- fast random read access
- reproducible? (deterministic)

candidates

- squashfs
  - compression
  - fast random read access
  - read-only
  - https://en.wikipedia.org/wiki/SquashFS
    - Squashfs compresses files, inodes and directories, and supports block sizes from 4 KiB up to 1 MiB for greater compression.
    - Squashfs is intended for general read-only file-system use and in constrained block-device memory systems (e.g. embedded systems) where low overhead is needed.
    - The tools unsquashfs and mksquashfs have been ported to Windows NT – Windows 8.1.
    - 7-Zip also supports Squashfs.
  - https://tldp.org/HOWTO/SquashFS-HOWTO/creatingandusing.html
    - read-only compressed file system
    - use cases: /usr partition, large FTP/HTTP-served archives that don't change often
    - mksquashfs some_folder some_folder.sqsh
- zim
  - https://en.wikipedia.org/wiki/ZIM_(file_format)
    - Its file compression uses LZMA2, as implemented by the xz-utils library, and, more recently, Zstandard.
  - https://wiki.openzim.org/wiki/ZIM_file_format
  - https://wiki.openzim.org/wiki/Features
  - https://github.com/openzim/libzim
  - https://en.wikipedia.org/wiki/Kiwix
  - for offline copies of Wikipedia
- btrfs
  - https://askubuntu.com/a/1337901/877276
  - Copy-on-Write filesystem
  - https://help.ubuntu.com/community/btrfs
- zfs
  - Copy-on-Write filesystem
  - https://wiki.ubuntu.com/ZFS
- qcow2
  - native format for qemu disk images
  - allows compression and random access
  - Copy-on-Write filesystem
- gz, bz2
  - block-based
  - Scanning for lzop is very fast, but for bzip2 and gzip it's slow, equivalent to decompressing the whole file. https://stackoverflow.com/a/23458181/10440128
- xz (lzma2)
  - http://tukaani.org/xz/format.html
  - Random-access reading: The data can be split into independently compressed blocks. Every .xz file contains an index of the blocks, which makes limited random-access reading possible when the block size is small enough.
  - PPM flushes it's model when it's statistics are full and LZMA2 intentionally flushes some state at some interval to enable multi-threaded decompression. Their random access implementation can be possible. https://stackoverflow.com/a/8627495/10440128
  - Note that for realistic random access, you will need to create your xz archive with a blocked encoder, such as pixz or the multithreaded mode of xz-utils 5.1.x alpha. For xz, as long as you do a blocked encode, seekability is cheap and built into the file format. https://stackoverflow.com/a/23458181/10440128
- pixz
  - Parallel, indexed xz compressor
  - https://github.com/vasi/pixz
- https://github.com/fidlej/idzip
  - The idzip file format allows seeking in gzip files.
  - not parallel
- dar
  - http://dar.linux.free.fr/home.html
- e2compr
  - dead project
  - https://askubuntu.com/questions/1328781/what-happened-to-e2compr
- clicfs
- cloop
- cramfs

see also

- https://superuser.com/questions/1385723/which-archival-formats-efficiently-extracts-a-single-file-from-an-archive
  - Some filesystems support compression directly (btrfs, reiserfs/reiser4, planned for ext?) but I'd just go with SquashFS
- https://stackoverflow.com/questions/429987/compression-formats-with-good-support-for-random-access-within-archives
- https://unix.stackexchange.com/questions/244604/archive-for-root-file-system-with-quick-random-access
- https://unix.stackexchange.com/questions/36487/indexed-archive-format
- https://stackoverflow.com/questions/4457997/indexing-random-access-to-7zip-7z-archives
- http://mattmahoney.net/dc/text.html # Large Text Compression Benchmark

## compression

### group by movie name

this still gives too many small files
so we still need a way to group movies
so: group by movie name hash?

### group by sub number

pack the first 1000 subs into one archive

```sh
#! /usr/bin/env bash
min_count=1000
set -e
cd done-zips
for zip in *.zip; do
    base=${zip%.*}
    [ -e "../unpacked-zips/$base" ] && continue
    echo $base
    unzip -q -B "$zip" -d "../unpacked-zips/$base"
    count=$(ls ../unpacked-zips/ | wc -l)
    ((count >= min_count)) && break
done
```

```
$ ls unpacked-zips | wc -l
1000

$ time tar czf unpacked-zips.tar.xz unpacked-zips
real    0m20.712s
user    0m19.600s
sys     0m1.229s

$ time mksquashfs unpacked-zips unpacked-zips.sqsh
real    0m18.702s
user    0m43.279s
sys     0m2.772s

$ du -sb unpacked-zips/ unpacked-zips.* | sort -n
26587136        unpacked-zips.sqsh
26667575        unpacked-zips.tar.xz
78457477        unpacked-zips/

$ ( cd done-zips/ && ls | head -n1000 | xargs -d'\n' du -bc) | tail -n1
27573783        total
```

so an archive of 1000 subs is only (27573783-26587136)/27573783 = 3.5% smaller

so "group by movie name" gives much better compression

## related

- https://github.com/AlJohri/OpenSubtitles/blob/master/opensubtitles.py downloader based on subliminal
