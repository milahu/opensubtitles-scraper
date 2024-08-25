#!/usr/bin/env python3

# post torrent to reddit

# FIXME refactor with release_add_to_git.py

# TODO before this...
# run shards2release.py
# create torrent

import os
import re
import sys
import json

import praw # python reddit api wrapper
import torf # torrent file

from fetch_subs_secrets import (
    reddit_client_id,
    reddit_client_secret,
    reddit_user_agent,
    reddit_username,
    reddit_password,
)



is_test = False
#is_test = True

reddit_posts_json_path = "release/reddit-posts.json"

# https://old.reddit.com/r/DHExchange/comments/1dc0dly/subtitles_from_opensubtitlesorg_subs_9900000_to/?
subreddit_name = "DHExchange"

# https://old.reddit.com/r/DHExchange/submit?selftext=true
# flairs: Request, Sharing, Meta
# FIXME praw.exceptions.RedditAPIException: BAD_FLAIR_TEMPLATE_ID: 'Flair template not found' on field 'flair'
#flair_id = "Sharing"
# FIXME praw.exceptions.RedditAPIException: BAD_FLAIR_TEMPLATE_ID: 'Flair template not found' on field 'flair'
#flair_id = 1
#flair_id = "sharing"
# praw.exceptions.RedditAPIException: SUBMIT_VALIDATION_FLAIR_REQUIRED: 'Your post must contain post flair.' on field 'flair'
#flair_id = None
# https://old.reddit.com/r/redditdev/comments/kar2ld/praw_posting_new_submission_with_a_flair/
# To get the flair_id, use subreddit.flair.templates or subreddit.flair.link_templates. The flair_id is an UUID.
# https://github.com/praw-dev/praw/issues/1948
# Unable to get flairs in a subreddit
# from flair-dropdown.html
flair_text = "Sharing"
#flair_id = "07baffd6-e6ed-11eb-af31-0eab196cd081"



torrent_path = sys.argv[1]

print("reading", torrent_path)
torrent = torf.Torrent.read(torrent_path)

torrent_btih = torrent.infohash
print("torrent_btih", torrent_btih)

torrent_name = torrent.name
print("torrent_name", torrent_name)

torrent_magnet_link = f"magnet:?xt=urn:btih:{torrent_btih}&dn={torrent_name}"

m = re.fullmatch(r"opensubtitles\.org\.dump\.([0-9]+)\.to\.([0-9]+)(?:\.v([0-9]+))?", torrent_name)

assert m != None, f"unexpected torrent_name {torrent_name!r}"

subs_per_release = 100_000

subs_from = int(m.group(1))
print("subs_from", subs_from)

subs_to = int(m.group(2))
print("subs_to", subs_to)
assert subs_from + subs_per_release - 1 == subs_to, f"unexpected: subs_from={subs_from} subs_to={subs_to}"

subs_range_id = subs_from // subs_per_release
print("subs_range_id", subs_range_id)
assert subs_from == subs_range_id * subs_per_release

#torrent_version = m.group(3)

#subs_range_id = 100
#subs_from = subs_range_id * 100000
#subs_to = ((subs_range_id + 1) * 100000) - 1
subs_pattern = f"{subs_range_id}xxxxx"
post_title = f"subtitles from opensubtitles.org - subs {subs_from} to {subs_to}"
#post_title = f"subtitles from opensubtitles.org {subs_pattern}"
#torrent_version = "TODO_torrent_version_20240609"
#torrent_name = f"opensubtitles.org.dump.{subs_from}.to.{subs_to}.v{torrent_version}"
provider_id = f"opensubtitles_org_{subs_from}_{subs_to}"

torrent_db_path = f"$HOME/down/torrent/done/{torrent_name}/{subs_pattern}.db"



# https://github.com/praw-dev/praw/issues/1948
# Unable to get flairs in a subreddit

def get_flair_id(subreddit, flair_text):
    """
    return the first flair_id that matches flair_text

    note: the mapping from flair_text to flair_id can be ambiguous
    """
    # subreddit.flair.templates
    # subreddit.flair.link_templates
    for attr in ["templates", "link_templates"]:
        try:
            for template in getattr(subreddit.flair, attr):
                if template["text"] == flair_text:
                    return template["id"]
        except Exception as exc:
            # prawcore.exceptions.Forbidden: received 403 HTTP response
            # https://github.com/praw-dev/praw/issues/1948
            # Unable to get flairs in a subreddit
            #traceback.print_exception(exc, limit=0, chain=False)
            pass
    raise KeyError # flair was not found



reddit = praw.Reddit(
    client_id=reddit_client_id,
    client_secret=reddit_client_secret,
    user_agent=reddit_user_agent,
    username=reddit_username,
    password=reddit_password,
)

#is_test = True

if is_test:
    subreddit_name = "test" # debug

subreddit = reddit.subreddit(subreddit_name)

flair_id = get_flair_id(subreddit, flair_text)

print("flair", flair_id, repr(flair_text))

# fix: praw.exceptions.RedditAPIException: BAD_FLAIR_TEMPLATE_ID: 'Flair template not found' on field 'flair'
if subreddit_name == "test":
    flair_id = None

print("reading", reddit_posts_json_path)
with open(reddit_posts_json_path) as f:
    reddit_posts = json.load(f)

selftext_continue = ""

def escape_link_title(title):
    return re.sub(r"([][])", r"\\\1", title)

def escape_link_url(url):
    return url.replace("(", "%28").replace(")", "%29").replace(" ", "%20")

for post in reddit_posts:
    if post is None:
        continue
    title = escape_link_title(post["title"])
    url = escape_link_url(post["url"])
    selftext_continue += f"* [{title}]({url})\n"

selftext = f"""\
continue

{selftext_continue}

## {torrent_name}

2GB = 100\_000 subtitles = 1 sqlite file

    {torrent_magnet_link}

## future releases

please consider subscribing to my release feed:
[opensubtitles.org.dump.torrent.rss](https://github.com/milahu/opensubtitles-scraper/raw/main/release/opensubtitles.org.dump.torrent.rss)

there is one major release every 50 days

there are daily releases in [opensubtitles-scraper-new-subs](https://github.com/milahu/opensubtitles-scraper-new-subs)

## scraper

[opensubtitles-scraper](https://github.com/milahu/opensubtitles-scraper)

most of this process is automated

my scraper is based on my [aiohttp\_chromium](https://github.com/milahu/aiohttp_chromium) to bypass cloudflare

i have 2 VIP accounts (20 euros per year) so i can download 2000 subs per day.
for continuous scraping, this is cheaper than a scraping service like zenrows.com.
also, with VIP accounts, i get subtitles without ads.

## problem of trust

one problem with this project is:
the files have no signatures, so i cannot prove the data integrity,
and others will have to trust me that i dont modify the files

## subtitles server

subtitles server to make this usable for thin clients (video players)

working prototype: [get-subs.py](https://github.com/milahu/opensubtitles-scraper/raw/main/get-subs.py)

live demo:
[erebus.feralhosting.com/milahu/bin/get-subtitles](https://erebus.feralhosting.com/milahu/bin/get-subtitles)
([http](http://erebus.feralhosting.com:9591/bin/get-subtitles))

## remove ads

subtitles scraped without VIP accounts have ads, usually on start and end of the movie

we all hate ads, so i made an adblocker for subtitles

* [opensubtitles_adblocker.py](https://github.com/milahu/opensubtitles-scraper/raw/main/opensubtitles_adblocker.py)
* [opensubtitles_adblocker_add.py](https://github.com/milahu/opensubtitles-scraper/raw/main/opensubtitles_adblocker_add.py)

this is not-yet integrated to get-subs.sh ... PRs welcome : P

similar projects:

* [KBlixt/subcleaner](https://github.com/KBlixt/subcleaner)
([reddit](https://www.reddit.com/r/bazarr/comments/qh0yjm/i_built_a_smart_ad_remove_script_with_a_clean/))
* [rogs/subscleaner](https://gitlab.com/rogs/subscleaner)
([reddit](https://www.reddit.com/r/selfhosted/comments/1bce93q/subscleaner_a_simple_program_that_removes_the_ads/))

... but my "subcleaner" is better, because it operates on raw bytes, so no errors at text encoding

## maintainers wanted

in the long run, i want to "get rid" of this project

so im looking for maintainers, to keep my scraper running in the future

## donations wanted

the more VIP accounts i have, the faster i can scrape

currently i have 2 VIP accounts = 20 euro per year
"""

# https://praw.readthedocs.io/en/stable/code_overview/models/subreddit.html#praw.models.Subreddit.submit
submit_args = dict(
    title=post_title,
    #url="https://reddit.com",
    # only moderators can create collections
    #collection_id=collection_id,
    flair_id=flair_id,
    selftext=selftext, # markdown
)

if is_test:
    print("test: not calling subreddit.submit", submit_args)
else:
    # https://praw.readthedocs.io/en/stable/code_overview/models/submission.html#praw.models.Submission
    submission = subreddit.submit(**submit_args)

if is_test:
    submission_url = "test_fake_submission_url"
else:
    submission_url = submission.url

print("submission_url", submission_url)

while reddit_posts[-1] == None:
    reddit_posts.pop()

reddit_posts.append(dict(
    id=provider_id,
    title=post_title,
    url=submission_url,
))

# avoid diff noise from comma
reddit_posts.append(None)

if is_test:
    print("test: not writing", reddit_posts_json_path)
else:
    print("writing", reddit_posts_json_path)
    with open(reddit_posts_json_path, "w") as f:
        json.dump(reddit_posts, f, indent=2)
