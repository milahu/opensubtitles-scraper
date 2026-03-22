- <https://github.com/jellyfin/jellyfin-plugin-opensubtitles/issues/199>
- <https://github.com/josdion/subbuzz/issues/40>
- <https://github.com/exebetche/vlsub/issues/260>
- <https://github.com/emericg/OpenSubtitlesDownload/issues/124>
- <https://github.com/QNapi/qnapi/issues/204>
- <https://github.com/matcornic/subify/issues/23>

------------------------------------------------------------------------

# add integration with opensubtitles mirrors

------------------------------------------------------------------------

**2026-03-22 09:48 +0100 milahu**

many subtitles from opensubtitles have been scraped  
and have been made available for free via bittorrent

> many subtitles

about  
5_719_123 + (9_521_948 - 9_180_519) + 10\*100_000  
= 7_060_552 of currently 10_772_237 subtitles  
7_060_552 / 10_772_237 = 65%

see also my project [opensubtitles-scraper](https://github.com/milahu/opensubtitles-scraper)  
which is currently not active, because [they stole my VIP accounts for "abuse"](https://github.com/milahu/opensubtitles-scraper/blob/main/docs/dont-copy-our-website.md)  
which will have to be adapted to [the new opensubtitles.com API](https://opensubtitles.stoplight.io/docs/opensubtitles-api/f65bc8dd4aef7-subtitle-exports)

ideally, all opensubtitles clients should ...

1\. try to get subtitles from a local subtitles database  
such a database costs around 160 GB of disk space

2\. try to download subtitles from a remote subtitles database  
remote subtitles database = opensubtitles mirror  
example implementation: [get-subs.py](https://github.com/milahu/opensubtitles-scraper/blob/main/get-subs.py)  
demo server: [milahu.duckdns.org/bin/get-subtitles](https://milahu.duckdns.org/bin/get-subtitles)

3\. cache all opensubtitles API requests to disk  
so later, the cached API responses can be released via bittorrent  
so future users can get free access to subtitles  
the new opensubtitles.com API does no longer return zip files  
but now it returns the subtitle files directly  
so for releasing, the subtitles have to be compressed  
the simplest solution is to compress each subtitle individually into a zip file  
and store these zip files in a sqlite database  
using the same database layout as previous releases  
(feel free to experiment and do your own benchmarks)  
ideally such releases should be usable directly  
without extraction, to reduce disk usage

4\. send random opensubtitles API requests  
to use more of the daily quota of a VIP account  
note: if a VIP account uses 100% of his daily quota every day  
then [opensubtitles admins will close the VIP account (without a refund!)](https://github.com/milahu/opensubtitles-scraper/blob/main/docs/dont-copy-our-website.md)  
claiming that such behavior is "abuse of their service"  
so these random requests should  
be splitted into multiple smaller batches, distributed over the day  
and it should use a random fraction of the daily quota, between 80 and 100%

duplicate issues

- <https://github.com/jellyfin/jellyfin-plugin-opensubtitles/issues/199>
- <https://github.com/josdion/subbuzz/issues/40>
- <https://github.com/exebetche/vlsub/issues/260>
- <https://github.com/emericg/OpenSubtitlesDownload/issues/124>
- <https://github.com/QNapi/qnapi/issues/204>
- <https://github.com/matcornic/subify/issues/23>
- todo: more opensubtitles clients?
