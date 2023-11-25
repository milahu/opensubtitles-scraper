# local subtitles provider



## search via movie ID

this assumes correct data in subtitles_all.db

use the movie name and year to search the movie ID in imdb/title.basics.db

```
$ sqlite3 imdb/title.basics.db 'select * from imdb_title_basics where primaryTitle like "XXX" and startYear = 2002 and titleType = "movie" limit 1' -line 
        tconst = 295701
     titleType = movie
  primaryTitle = xXx
 originalTitle = xXx
       isAdult = 0
     startYear = 2002
       endYear = 0
runtimeMinutes = 124
        genres = Action,Adventure,Thriller
```

use the movie ID 295701 to search subtitles in subtitles_all.db

```
$ sqlite3 subtitles_all.db 'select * from metadata where ImdbID = 295701 and ISO639 = "en" limit 1;' -line
      IDSubtitle = 35227
       MovieName = xXx
       MovieYear = 2002
    LanguageName = English
          ISO639 = en
      SubAddDate = 2002-11-23 00:00:00
          ImdbID = 295701
       SubFormat = srt
        SubSumCD = 4
MovieReleaseName = XXX (2002)
        MovieFPS = 23.98
    SeriesSeason = 0
   SeriesEpisode = 0
SeriesIMDBParent = 0
       MovieKind = movie
             URL = http://www.opensubtitles.org/subtitles/35227/xxx-en
```

use the subtitle ID 35227 to get the subtitle's zip file

```
$ sqlite3 opensubtitles.org.Actually.Open.Edition.2022.07.25/opensubs.db "select writefile('sub.zip', file) from subz where num = 35227"
```

```
$ unzip -l sub.zip
Archive:  sub.zip
  Length      Date    Time    Name
---------  ---------- -----   ----
    44857  07-24-2022 09:26   Triple_X-Proper-DVDrip-DivX-PosTX_CD1_English.srt
    22841  07-24-2022 09:26   Triple_X-Proper-DVDrip-DivX-PosTX_CD2_English.srt
    45025  07-24-2022 09:26   Triple_X-Proper-DVDrip-DivX-PosTX_CD1_Eng_with_italics.srt
    23016  07-24-2022 09:26   Triple_X-Proper-DVDrip-DivX-PosTX_CD2_Eng_with_italics.srt
     8097  07-24-2022 09:26   xxx.(35227).nfo
---------                     -------
   143836                     5 files
```



## search via movie name and year

use the movie name and year to search subtitles in subtitles_all.db

```
$ sqlite3 subtitles_all.db 'select * from metadata where MovieName like "xxx" and MovieYear = 2002 and ISO639 = "en" limit 1;' -line
      IDSubtitle = 35227
       MovieName = xXx
       MovieYear = 2002
    LanguageName = English
          ISO639 = en
      SubAddDate = 2002-11-23 00:00:00
          ImdbID = 295701
       SubFormat = srt
        SubSumCD = 4
MovieReleaseName = XXX (2002)
        MovieFPS = 23.98
    SeriesSeason = 0
   SeriesEpisode = 0
SeriesIMDBParent = 0
       MovieKind = movie
             URL = http://www.opensubtitles.org/subtitles/35227/xxx-en
```
