# repack

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

```
17236   repack-grouped/eng/group-size-1000/1-17839.tar.lzma
17240   repack-grouped/eng/group-size-1000/1-17839.tar.xz
17088   repack-grouped/eng/group-size-1000/1-17839.7z
17992   repack-grouped/eng/group-size-1000/1-17839.tar.bz2
25248   repack-grouped/eng/group-size-1000/1-17839.tar.zstd
25448   repack-grouped/eng/group-size-1000/1-17839.tar.gz
28307   original zip files
```

### erofs

TODO

faster reads than squashfs

https://sigma-star.at/blog/2022/07/squashfs-erofs/
