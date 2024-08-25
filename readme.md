# opensubtitles-scraper

scrape subtitles from [opensubtitles.org](https://www.opensubtitles.org/)

## result

torrent RSS feed: [opensubtitles.org.dump.torrent.rss](release/opensubtitles.org.dump.torrent.rss)

<!-- <result-list> -->

- [opensubtitles.org.dump.9180519.to.9521948.by.lang.2023.04.26.torrent](release/opensubtitles.org.dump.9180519.to.9521948.by.lang.2023.04.26.torrent)
- [opensubtitles.org.dump.9500000.to.9599999.v20240306.torrent](release/opensubtitles.org.dump.9500000.to.9599999.v20240306.torrent)
- [opensubtitles.org.dump.9600000.to.9699999.torrent](release/opensubtitles.org.dump.9600000.to.9699999.torrent)
- [opensubtitles.org.dump.9700000.to.9799999.torrent](release/opensubtitles.org.dump.9700000.to.9799999.torrent)
- [opensubtitles.org.dump.9800000.to.9899999.v20240420.torrent](release/opensubtitles.org.dump.9800000.to.9899999.v20240420.torrent)
- [opensubtitles.org.dump.9900000.to.9999999.v20240609.torrent](release/opensubtitles.org.dump.9900000.to.9999999.v20240609.torrent)
- [opensubtitles.org.dump.10000000.to.10099999.v20240820.torrent](release/opensubtitles.org.dump.10000000.to.10099999.v20240820.torrent)

<!-- </result-list> -->

unreleased subs are stored in [github.com/milahu/opensubtitles-scraper-new-subs](https://github.com/milahu/opensubtitles-scraper-new-subs)

## usage

- download the torrents from section [result](#result)
- download `subtitles_all.txt.gz` from https://dl.opensubtitles.org/addons/export/
- run [subtitles_all.txt.gz-parse.py](subtitles_all.txt.gz-parse.py) to build `subtitles_all.db`
  - `python3 subtitles_all.txt.gz-parse.py subtitles_all.db subz_metadata subtitles_all.txt.gz subtitles_all.txt.gz-parse-errors.txt subtitles_all.txt.gz-parse-debug.txt`
- fix the values for `db_path` in [local-subtitle-providers.json](local-subtitle-providers.json)

run [get-subs.py](get-subs.py) to get subtitles for a movie:

```
~/src/opensubtitles-scraper/get-subs.py Scary.Movie.2000.mp4

video_path Scary.Movie.2000.mp4
video_filename Scary.Movie.2000.mp4
video_parsed MatchesDict([('title', 'Scary Movie'), ('year', 2000), ('container', 'mp4'), ('mimetype', 'video/mp4'), ('type', 'movie')])
output 'Scary.Movie.2000.en.00018286.sub' from 'Scary_eng.txt' (us-ascii)
output 'Scary.Movie.2000.en.00018615.sub' from 'Scary Movie.txt' (us-ascii)
output 'Scary.Movie.2000.en.00106539.sub' from 'Scary Movie - ENG.txt' (us-ascii)
output 'Scary.Movie.2000.en.00117707.sub' from 'scream_english.sub' (iso-8859-1)
output 'Scary.Movie.2000.en.00203573.sub' from 'Scary Movie - ENG.txt' (us-ascii)
output 'Scary.Movie.2000.en.00204203.sub' from 'Scary Movie_engl.sub' (iso-8859-1)
output 'Scary.Movie.2000.en.03112243.srt' from 'Scary Movie 1 (2000).en.bug-fixed.srt' (Windows-1252)
output 'Scary.Movie.2000.en.03142326.srt' from 'kns-sm.srt' (Windows-1252)
output 'Scary.Movie.2000.en.03279944.srt' from 'Scary Movie 1 iNT DvD RiP- WaCkOs.srt' (Windows-1252)
output 'Scary.Movie.2000.en.03318665.srt' from 'rvlt-scarymovie.srt' (us-ascii)
output 'Scary.Movie.2000.en.03552139.srt' from 'Scary Movie.srt' (us-ascii)
output 'Scary.Movie.2000.en.03686957.sub' from 'Scary.Movie.(2000).DVDRIP.Divx.DOMiNION.sub' (iso-8859-1)
output 'Scary.Movie.2000.en.04867080.srt' from 'Scary.Movie.2000.BrRip.720p.x264.YIFY-eng.srt' (Windows-1252)
output 'Scary.Movie.2000.en.05115082.srt' from 'Scary Movie 1.[2000].UNRATED.DVDRIP.XVID.[Eng]-DUQA®.srt' (Windows-1252)
...
```



### subtitles server

to run your own subtitles server,
see [docs/lighttpd.conf](docs/lighttpd.conf)
to expose [get-subs.py](get-subs.py) as a CGI script on an HTTP server



## based on

- [5719123 subtitles from opensubtitles.org](https://www.reddit.com/r/DataHoarder/comments/w7sgcz/5719123_subtitles_from_opensubtitlesorg/) by `-marked-4life`
  - [opensubtitles.org.Actually.Open.Edition.2022.07.25.torrent](release/opensubtitles.org.Actually.Open.Edition.2022.07.25.torrent)
- cloudflare bypassing with commercial [scraping services](opensubtitles_dump_client/scraping.md)
- bittorrent

## offline version of opensubtitles

useful for subtitle-fetchers like

- [bazarr](https://github.com/morpheus65535/bazarr)
- [subliminal](https://github.com/Diaoul/subliminal)
- [subdl](https://github.com/alexanderwink/subdl)

## scraping

opensubtitles.org is protected by cloudflare, so im using a scraping proxy ([zenrows.com](https://www.zenrows.com/)).
with `max_concurrency = 10` in fetch-subs.py, one request takes about 0.2 seconds.

videos:

- https://asciinema.org/a/6fG6TXEkF3UOOL0qu8tivViXF
- [docs/fetch-subs.py.cast](docs/fetch-subs.py.cast)
