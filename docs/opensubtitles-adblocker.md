# opensubtitles adblocker

my original motivation for scraping subtitles
were the annoying ads
added to subtitles by opensubtitles

i wanted to have a large test corpus
to create an "adblocker" for subtitles

but well, its still on my todo list ^^
the ads are annoying, but not annoying enough

## parsing ads

ads are usually at the start or end of a subtitles file

for the same language, always the same text-blocks are inserted
so we can compare many subs from one language
and look for identical text-blocks

i assume that ads can also be "hidden" in the middel of subtitles files
so i would not reduce the search space to the start and end
