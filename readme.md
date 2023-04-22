# opensubtitles-scraper

scrape subtitles from [opensubtitles.org](https://www.opensubtitles.org/)

## based on

- [5719123 subtitles from opensubtitles.org](https://www.reddit.com/r/DataHoarder/comments/w7sgcz/5719123_subtitles_from_opensubtitlesorg/) by `-marked-4life`
- cloudflare bypassing with commercial [scraping services](opensubtitles_dump_client/scraping.md)
- bittorrent

## offline version of opensubtitles

useful for subtitle-fetchers like

- [subliminal](https://github.com/Diaoul/subliminal)
- [subdl](https://github.com/alexanderwink/subdl)

there is an archive of 5.7 million subtitles in [reddit.com/r/DataHoarder](https://www.reddit.com/r/DataHoarder/comments/w7sgcz/5719123_subtitles_from_opensubtitlesorg/)

the archive is shared as [torrent](https://files.catbox.moe/lrmid1.torrent) and [nzb](https://files.catbox.moe/ewv9cs.xz). torrent magnet link:

```
magnet:?xt=urn:btih:c2f0b5d26a886ba12f7f667d69c0459056dcda9b&dn=opensubtitles.org.Actually.Open.Edition.2022.07.25&tr=udp%3a%2f%2fexplodie.org%3a6969%2fannounce&tr=udp%3a%2f%2fopen.stealth.si%3a80%2fannounce&tr=udp%3a%2f%2ftracker.moeking.me%3a6969%2fannounce&tr=https%3a%2f%2ftracker.nanoha.org%3a443%2fannounce&tr=udp%3a%2f%2ftracker.publictracker.xyz%3a6969%2fannounce&tr=https%3a%2f%2ftr.abiir.top%3a443%2fannounce&tr=udp%3a%2f%2fzecircle.xyz%3a6969%2fannounce&tr=http%3a%2f%2ftracker.aeerso.space%3a6969%2fannounce&tr=http%3a%2f%2ftracker.iro.moe%3a80%2fannounce&tr=http%3a%2f%2fincine.ru%3a6969%2fannounce&tr=udp%3a%2f%2fepider.me%3a6969%2fannounce&tr=udp%3a%2f%2flloria.fr%3a6969%2fannounce&tr=udp%3a%2f%2fopen.demonii.com%3a1337%2fannounce&tr=https%3a%2f%2ftracker.lilithraws.cf%3a443%2fannounce&tr=https%3a%2f%2ftr.burnabyhighstar.com%3a443%2fannounce&tr=https%3a%2f%2ftracker.loligirl.cn%3a443%2fannounce&tr=udp%3a%2f%2fthouvenin.cloud%3a6969%2fannounce&tr=udp%3a%2f%2fhtz3.noho.st%3a6969%2fannounce&tr=udp%3a%2f%2ftamas3.ynh.fr%3a6969%2fannounce&tr=http%3a%2f%2fopen.nyap2p.com%3a8080%2fannounce&tr=http%3a%2f%2ftracker4.itzmx.com%3a2710%2fannounce&tr=udp%3a%2f%2fexodus.desync.com%3a6969%2fannounce&tr=udp%3a%2f%2fopen.free-tracker.ga%3a6969%2fannounce&tr=http%3a%2f%2ft.nyaatracker.com%3a80%2fannounce&tr=udp%3a%2f%2frun.publictracker.xyz%3a6969%2fannounce&tr=udp%3a%2f%2ftracker.torrent.eu.org%3a451%2fannounce&tr=http%3a%2f%2ftracker.bt4g.com%3a2095%2fannounce&tr=udp%3a%2f%2ftracker.exorditech.com.tr%3a8000%2fannounce&tr=udp%3a%2f%2ffree.open.tracker.4.starka.st%3a15480%2fannounce&tr=https%3a%2f%2ftracker.moeblog.cn%3a443%2fannounce&tr=https%3a%2f%2fchihaya-heroku.120181311.xyz%3a443%2fannounce&tr=udp%3a%2f%2fwww.torrent.eu.org%3a451%2fannounce&tr=udp%3a%2f%2fblack-bird.ynh.fr%3a6969%2fannounce&tr=udp%3a%2f%2ftheodoric.fr%3a6969%2fannounce&tr=http%3a%2f%2fipv4announce.sktorrent.eu%3a6969%2fannounce
```

in its current form, the archive is not ideal for end-users, simply because its too large: 130GB

im currently in the process of repacking the archive from 130GB to 50GB, by grouping subtitles by movie name, and by using xz compression. this is good for the real-world use case "i have one movie and want all subtitles, so i can compare and pick the best subtitle". personally, i dont use "movie hash" or the user ratings on opensubtitles.org. movie hash is too narrow (example: does not find 1080p subs for a 720p movie), and user ratings suffer from the general problem that rating systems are not reliable

also i will split the archive by language. english subs are the largest part, and make only 10% of the archive. so when repacked, subtitles for all english movies are only 5GB, which is much easier to handle than the original 130GB archive. this is similar to spelling dictionaries, which have one package per language (hunspell-en_US, hunspell-es_ES, ...)

finally, i want to update the archive. currently, [opensubtitles.org](https://www.opensubtitles.org/) has 6637502 subtitles, so currently im missing 6637502 - 5719123 = 918379 = about 1 million subtitles

future updates: every day, about 1000 subs are added to opensubtitles. i plan to do "live" releases on github (with a delay of some days, to give opensubtitles time for moderation), and maybe monthly releases as torrent, so i can delete old git repos. we will see...

### question

how should i clean the data?

ideally i would do the same transformations as subliminal

currently i do

- rename duplicate files (zip archives allow duplicate files)
- recode file names and file contents to utf8
- add missing file extensions when file type is detected
  - sub files
  - sami files (simple check)
  - TODO more files. libmagic does not always help
- change file extension from txt to sub for sub files
  - mpv player ignores txt files https://github.com/mpv-player/mpv/issues/4144
- add FPS header to sub files when its missing. example "{1}{1}25.000"
- todo: fix broken file extensions like ".sr" (should be ".srt")
- todo: fix broken utf8 in file content. replace broken bytes with "?"
