# repack

## file size

```
$ du -skL * | sort -n 
14636   1-17839.s=on.yx=9.x=9.f=off.0=PPMd:mem2g:o32.7z
17092   1-17839.7z
17236   1-17839.tar.lzma
17240   1-17839.tar.xz
17992   1-17839.tar.bz2
20616   1-17839.lzma.sqfs
20640   1-17839.xz.sqfs
23560   1-17839.zstd.sqfs
25248   1-17839.tar.zstd
25448   1-17839.tar.gz
25828   1-17839.gzip.sqfs
28484   1-17839.original-zipfiles.db
29756   1-17839.original-zipfiles
30168   1-17839.lzo.sqfs
40548   1-17839.lz4.sqfs
47236   1-17839.lz4.erofs
```

note: the archive formats `7z` and `tar` are horribly slow for random read access

the compressed filesystem `lz4.sqfs` is fast, but compression is worse than original zipfiles

## original zip files

### unpacking zipfiles

```
$ time find 1-17839.original-zipfiles/ -name '*.zip' -print0 | shuf -z | xargs -0 -n1 unzip -p | pv -r >/dev/null 
[3.09MiB/s]

real    0m23.686s
user    0m11.452s
sys     0m11.103s
```

```
$ time for zip in 1-17839.original-zipfiles/*.zip; do unzip -p "$zip"; done | pv -r >/dev/null 
[3.32MiB/s]

real    0m22.049s
user    0m11.749s
sys     0m10.063s
```

problem is: on the server side, we dont need to decompress at all!

we can simply send the original zip file to the client,
so we dont need to gzip-compress the http transfer,
and its the client's job to decompress

### reading zipfiles from ext4 filesystem on internal SATA-SSD

uncached versus cached

```
$ time cat 1-17839.original-zipfiles/* | pv -r >/dev/null
[28.3MiB/s]

real    0m0.964s
user    0m0.077s
sys     0m0.481s

$ time cat 1-17839.original-zipfiles/* | pv -r >/dev/null
[86.1MiB/s]

real    0m0.323s
user    0m0.064s
sys     0m0.303s
```

FIXME why is this so slow with `xargs -n1 cat`

why is `xargs cat` so much faster

```
$ time find 1-17839.original-zipfiles/ -name '*.zip' -print0 | shuf -z | xargs -0 -n1 cat | pv -r >/dev/null 
[2.03MiB/s]

real    0m13.324s
user    0m2.601s
sys     0m10.413s
```

### reading zipfiles from sqlite database on internal SATA-SSD

stupid workaround via python, to write a sqlite3 blob to stdout

https://stackoverflow.com/questions/10353467/how-to-insert-binary-data-into-sqlite3-database-in-bash

```
python -c "import sys, sqlite3; sys.stdout.buffer.write(sqlite3.connect(sys.argv[1]).execute('select content from zipfiles limit 1').fetchone()[0])" 1-17839.original-zipfiles.db | less
```

this is ridiculously slow

```
$ cat 1-17839.sub-numbers.txt | shuf | while read num; do python -c "import sys, sqlite3; sys.stdout.buffer.write(sqlite3.connect(sys.argv[1]).execute('select content from zipfiles where num = $num').fetchone()[0])" 1-17839.original-zipfiles.db; done | pv -r >/dev/null
[ 177KiB/s]
```

lets read all files in python only

sequential read

```
$ python -c "import sys, sqlite3; list(map(lambda r: sys.stdout.buffer.write(r[0]), sqlite3.connect(sys.argv[1]).execute('select content from zipfiles')))" 1-17839.original-zipfiles.db | pv -r >/dev/null
[69.1MiB/s]
```

random read: `order by random()`

```
$ python -c "import sys, sqlite3; list(map(lambda r: sys.stdout.buffer.write(r[0]), sqlite3.connect(sys.argv[1]).execute('select content from zipfiles order by random()')))" 1-17839.original-zipfiles.db | pv -r >/dev/null
[45.3MiB/s]
```

## compressing-many-similar-big-files

https://superuser.com/questions/730592/compressing-many-similar-big-files

xz --lzma2=dict=128M,mode=fast,mf=hc4 --memory=2G

---



https://stackoverflow.com/questions/61999831/compress-many-versions-of-a-text-with-fast-access-to-each

http://code.botcompany.de/1028167

---



see also

- opensubtitles_dump_client/readme.md
- opensubtitles_dump_client/repack-grouped-deleted.txt
- opensubtitles_dump_client/repack.py
- opensubtitles_dump_client/repack.py.log-average-smaller.sh
- opensubtitles_dump_client/repack.py.log-failed-to-verify.sh
- opensubtitles_dump_client/repack-split-archives-make.sh

## random read speed

the `tar` format sucks, because random read access is slow

the `squashfs` format would be better

TODO why not squashfs

see also new-subs-archive.py

https://stackoverflow.com/questions/429987/compression-formats-with-good-support-for-random-access-within-archives

## compressed filesystems

squashfs, clicfs, cloop, cramfs, e2compr, ...

[Embedded Linux: Using Compressed File Systems](https://lwn.net/Articles/219827/)

> SquashFS is a kind of successor to CramFS because it aims at the same target audience while providing a similar process for creation and use of the file system. What makes SquashFS an improvement over CramFS is best stated by Phillip Lougher in a linux-kernel mailing list post: "SquashFS basically gives better compression, bigger files/file system support, and more inode information."

> CramFS is integrated with the kernel source

> JFFS2 is integrated into the kernel

> jffs2 works only on directly-connected flash (i.e. not the USB and IDE flash drives that I use)

> e2compr is not included in the kernel because it doesn't have any fsck support

ideally this should work in userspace, so a fuse driver would be nice

or this should work out-of-the-box, at least on linux

https://sigma-star.at/blog/2022/07/squashfs-erofs/

> On embedded Linux systems, SquashFS is currently the dominating filesystem for such applications, having been merged into main line Linux in 2009, superseding the earlier cramfs.

### squashfs

opensubtitles_dump_client/repack.py

with default settings, xz.sqfs and lzma.sqfs are only 25% smaller than the original zip files

20616 / 28307 = 0.728

```
20616   repack-grouped/eng/group-size-1000/1-17839.lzma.sqfs
20640   repack-grouped/eng/group-size-1000/1-17839.xz.sqfs
23560   repack-grouped/eng/group-size-1000/1-17839.zstd.sqfs
25828   repack-grouped/eng/group-size-1000/1-17839.gzip.sqfs
28307   original zip files
30168   repack-grouped/eng/group-size-1000/1-17839.lzo.sqfs
40548   repack-grouped/eng/group-size-1000/1-17839.lz4.sqfs
```

lz4.sqfs has good speed and bad compression

```
$ sudo mount -o loop 1-17839.lz4.sqfs mnt/

$ time cat mnt/999.* >/dev/null 

real    0m0.034s
user    0m0.004s
sys     0m0.017s

$ time find mnt/ -type f -print0 | shuf -z | xargs -0 -n1 cat | pv -r >/dev/null 
[4.53MiB/s]

real    0m14.720s
user    0m2.727s
sys     0m11.845s
```

xz.sqfs has bad speed and good compression (27% smaller than original zip files)

```
$ sudo mount -o loop 1-17839.xz.sqfs mnt/

$ time find mnt/ -type f -print0 | shuf -z | xargs -0 -n1 cat | pv -r >/dev/null 
[1.75MiB/s]

real    0m38.215s
user    0m2.728s
sys     0m33.798s
```

### erofs

TODO

erofs = Enhanced Read-Only File System

faster reads than squashfs

https://sigma-star.at/blog/2022/07/squashfs-erofs/

worse compression that squashfs

not much faster than squashfs with lz4 (xz is slow)

## archives

problem: slow read access, no fast random access

worst case: extracting the last file requires processing ALL files

```
14636   repack-grouped/eng/group-size-1000/1-17839.s=on.yx=9.x=9.f=off.0=PPMd:mem2g:o32.7z
17236   repack-grouped/eng/group-size-1000/1-17839.tar.lzma
17240   repack-grouped/eng/group-size-1000/1-17839.tar.xz
17088   repack-grouped/eng/group-size-1000/1-17839.7z
17992   repack-grouped/eng/group-size-1000/1-17839.tar.bz2
25248   repack-grouped/eng/group-size-1000/1-17839.tar.zstd
25448   repack-grouped/eng/group-size-1000/1-17839.tar.gz
28307   original zip files
```

### PPMd

https://softwarerecs.stackexchange.com/questions/49019/which-compression-utility-should-i-use-for-an-extremely-large-plain-text-file

<blockquote>

```
7z a -t7z -ms=on -myx=9 -mx=9 -mf=off -m0=PPMd:mem2g:o32 1-17839.s=on.yx=9.x=9.f=off.0=PPMd:mem2g:o32.7z /run/user/1000/opensubs-repack/1-17839/
```

PPMd: Use the PPMd algorithm, which is said to provide a "very good compression ratio for plain text files."

mem2g: Use 2GB of RAM for compression and decompression.

</blockquote>

https://en.wikipedia.org/wiki/Prediction_by_partial_matching

https://manpages.ubuntu.com/manpages/trusty/man1/ppmd.1.html

http://compression.ru/ds/ - russian

http://mattmahoney.net/dc/text.html - Large Text Compression Benchmark

algos with fast `Decomp`

```
                Compression                      Compressed size      Decompresser  Total size   Time (ns/byte)
Program           Options                       enwik8      enwik9     size (zip)   enwik9+prog  Comp Decomp   Mem Alg Note
-------           -------                     ----------  -----------  -----------  -----------  ----- -----   --- --- ----
drt|lpaq9m        9                           17,964,751  143,943,759    110,579 x  144,054,338    868   898 1542 CM   41 # http://mattmahoney.net/dc/lpaq9.zpaq
mcm 0.83          -x11                        18,233,295  144,854,575     79,574 s  144,934,149    394   281 5961 CM   72 # closed source
zcm 0.93          -m8 -t1                     19,572,089  159,135,549    227,659 x  159,363,208    421   411 3100 CM   48 # closed source
nanozipltcb 0.09                              20,537,902  161,581,290    133,784 x  161,715,074     64    30 3350 BWT  40 # customized version of nanozip http://nanozip.net/
M03 1.1b          1000000000                  20,710,197  163,667,431     50,468 x  163,717,899    457   406 5735 BWT  52 # free
bcm 2.03          -b1000x-                    20,738,630  163,646,387    125,866 x  163,772,253     63    34 4096 BWT  98 # free
glza 0.10.1       -x -p3                      20,356,097  163,768,203     69,935 s  163,838,138   8184    12 8205 Dict 67 # open source, general purpose compressor optimized to compress text
bsc 3.25          -b1000 -e2                  20,786,794  163,884,462     74,297 xd 163,958,759     23     8 5000 BWT  96 # free
pcompress 3.1     -c libbsc -l14 -s1000m      20,769,968  163,391,884  1,370,611 x  164,762,495    359    74 3300 BWT  48 # open source https://github.com/moinakg/pcompress
BWTmix v1         c10000                      20,608,793  167,852,106      9,565 x  167,861,671   1794   690 5000 BWT  49
M1x2 v0.6         7 enwik7.txt                20,723,056  172,212,773     38,467 s  172,251,240    711   715 1051 CM   26
mcomp 2.00        -mw -M320m                  21,103,670  174,388,351    172,531 x  174,560,882    473   399 1643 BWT  26
dark 0.51         -b333mf                     21,169,819  175,471,417     34,797 x  175,506,214    533   453 1692 BWT
hook v1.4         1700                        21,990,502  176,648,663     37,004 x  176,685,667    741   695 1777 DMC  26
7zip 4.46a        -m0=ppmd:mem=1630m:o=10 ... 21,197,559  178,965,454          0 xd 178,965,454    503   546 1630 PPM  23
rings 2.5         -m8 -t1                     20,873,959  178,747,360    240,523 x  178,987,883    280   163 2518 BWT  48
```

### 

### Compression formats with good support for random access within archives

https://stackoverflow.com/questions/429987/compression-formats-with-good-support-for-random-access-within-archives

