# github repo limits

https://stackoverflow.com/questions/38768454/repository-size-limits-for-github-com

> Individual files in a repository are strictly limited to a 100 MB maximum size limit.

> you will see warnings for pushing files bigger than 50 MB and files bigger than 100 MB won't be accepted

- soft limit: 5 GB per repo
- hard limit: 100 GB per repo
- soft limit: 50 MB per file
- hard limit: 100 MB per file

the shard files like `10395xxx.db` are designed to be smaller than 100 MB in most cases...

but the risk of exceeding 100 MB is bigger than zero,  
so maybe in the future i will have to redesign the shard files to store less subtitles per shard file

```
+ ./opensubtitles-scraper-new-subs/git-push.sh
> git push https://github.com/milahu/opensubtitles-scraper-new-subs main:main shards-103xxxxx:shards-103xxxxx shards-74xxxxx:shards-74xxxxx
Enumerating objects: 16, done.
Counting objects: 100% (16/16), done.
Delta compression using up to 16 threads
Compressing objects: 100% (10/10), done.
Writing objects: 100% (15/15), 148.72 MiB | 213.88 MiB/s, done.
Total 15 (delta 5), reused 0 (delta 0), pack-reused 0 (from 0)
remote: Resolving deltas: 100% (5/5), completed with 1 local object.
remote: warning: See https://gh.io/lfs for more information.
remote: warning: File 10395xxx.db is 60.36 MB; this is larger than GitHub's recommended maximum file size of 50.00 MB
remote: warning: GH001: Large files detected. You may want to try Git Large File Storage - https://git-lfs.github.com.
To https://github.com/milahu/opensubtitles-scraper-new-subs
   a528e48..c48730d  shards-103xxxxx -> shards-103xxxxx
```
