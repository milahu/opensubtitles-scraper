https://www.reddit.com/r/Piracy/comments/1qymihh/opensubtitlesorg_is_run_by_greedy_idiots/

opensubtitles.org is run by greedy idiots

[opensubtitles.org VIP accounts](https://www.opensubtitles.org/en/support#vip) promise

> Higher download limits - 1000 subtitles/24 hours (but no abusing!)

but if you download 1000 subtitles per day and [redistribute the subtitles for free](https://github.com/milahu/opensubtitles-scraper), then they close your VIP account with no refund

but that "no abusing" clause has no legal effect, because they dont own the intellectual property rights on the subtitles. i am stealing from pirates who want to sell their stolen goods...

they let users upload subtitles, but uploaders get no money. the admins get all the money from VIP accounts, and only a small part of that money is needed to run the servers...

possible solution: all opensubtitles.org clients should by default scrape random subtitles to saturate the daily download quota (starting from number [10511000](https://github.com/milahu/opensubtitles-scraper-new-subs/tree/shards-105xxxxx)) (distribute downloads over the day to avoid getting blocked), and at the end of the VIP account (after one year), all scraped subtitles are uploaded to github.com (365000 subtitles are around 7GB), the VIP account is closed, and a new account (new identity) is created for the next year (to avoid getting blocked). the uploaded subtitles can be aggregated to new releases like 105xxxxx, 106xxxxx, 107xxxxx, ...

problem of trust: the subtitles are not signed, so there is no way to check the data integrity, so ideally, the aggregation part would require a consensus of multiple uploaders per file. but such a voting system can be tricked, so it should be possible to use the uploaded subtitles directly, and if subtitles are broken, they can be traced back to the uploader, and maybe all subtitles from that uploader can be blacklisted. see also my subtitles server [get-subs.py](https://github.com/milahu/opensubtitles-scraper/blob/main/get-subs.py) ([live demo](https://milahu.duckdns.org/bin/get-subtitles))

currently my scraper is broken, but there are enough API clients that could be extended with a scraping feature

see also [dont copy our website](https://github.com/milahu/opensubtitles-scraper/blob/main/docs/dont-copy-our-website.md) and [Re: Opensubtitles.org is like malware now](https://www.reddit.com/r/PleX/comments/rbaike/opensubtitlesorg_is_like_malware_now/o430wit/)

ideas?

---

Sorry, this post was removed by Reddit’s filters.
