# add local subtitles providers

https://github.com/morpheus65535/bazarr/issues/new



continue https://bazarr.featureupvote.com/suggestions/275382/local-subtitle-as-provider

im currently scraping an update to [5,719,123 subtitles from opensubtitles.org](https://www.reddit.com/r/DataHoarder/comments/w7sgcz/5719123_subtitles_from_opensubtitlesorg/)

reddit: [opensubtitles.org dump - 1 million subtitles - 23 GB](https://www.reddit.com/r/DataHoarder/comments/12yxcoy/opensubtitlesorg_dump_1_million_subtitles_23_gb/)
scraper: https://github.com/milahu/opensubtitles-scraper

my goal is to integrate these archives with subtitle fetchers (bazarr, subliminal, subdl, ...)
i will implement the feature myself, thats not the problem ... the problem is performance
so im doing early releases and collecting feedback, maybe someone has better ideas

so here is my plan ...

### split by language

the first optimization is splitting by language.
the full dataset has about 150GB.
all english subs are only 10% of the dataset, so 15GB.
all other languages have less subtitles.
this optimization is cheap, because no need to recompress files

### repack by movie name

the second optimization is repacking by movie name.
with xz compression, this will reduce size by 66%.
so 50GB for the full dataset, 5GB for english-only.
problem: this optimization is expensive in terms of CPU time.
problem: adding new subtitles to existing movies requires repacking.

### hybrid

... so probably i will use both strategies.
"split by language" for frequent releases (monthly).
"split by language and repack by movie name" for less-frequent releases (yearly)

### storage format

this part is still experimental.
the previous dataset was released as sqlite database. problem: blocksize is only 512B (average filesize is 20KB), so everything is fragmented and performance is bad.
i did my first 3 releases as tar files, but tar files have terrible performance on random read access.
better are actual filesystems like ISO, UDF, FAT32, EXT2, ...

### storage names

in my first 3 releases, i used the full zipfile names, for example 