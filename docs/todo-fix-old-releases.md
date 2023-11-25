# todo: fix old releases

## opensubtitles.org.Actually.Open.Edition.2022.07.25

### subs are missing

```
$ sqlite3 opensubs-metadata.db "select * from subz_metadata where IDSubtitle = 504"
504|Bad Education|2004|English|en|2005-04-14 02:35:02|275491|srt|1|bad education|0.0|0|0|0|movie|http://www.opensubtitles.org/subtitles/504/bad-education-en

$ sqlite3 opensubs.db "select name from subz where num = 504" | wc -l 
0
```

opensubtitles_dump_client/repack.py

```
FIXME zipfile not found for sub_number 742
FIXME zipfile not found for sub_number 2483
FIXME zipfile not found for sub_number 2494
FIXME zipfile not found for sub_number 2496
FIXME zipfile not found for sub_number 2498
FIXME zipfile not found for sub_number 2500
```

## opensubtitles.org.dump.9180519.to.9521948.by.lang.2023.04.26-archive.org

### subs are in the wrong language database

for this release, the language was parsed from the zip filename

but the filename (and the metadata) can change over time
so the metadata from subtitles_all.txt.gz should be the source of truth
