#!/usr/bin/env python3

# add release torrent file to git

# FIXME refactor with reddit_add_torrent.py

# TODO before this...
# run shards2release.py
# create torrent



import os
import re
import sys
import json
import shlex
import subprocess

import torf # torrent file



# dynamic paths
torrent_path = sys.argv[1]

# static paths
readme_path = "readme.md"
local_subtitle_providers_json_path = "local-subtitle-providers.json"
torrent_rss_path = "release/opensubtitles.org.dump.torrent.rss"
reddit_posts_json_path = "release/reddit-posts.json"



def git_add(path):
    args = [
        "git",
        "add",
        path,
    ]
    print(">", shlex.join(args))
    #subprocess.run(args)
    subprocess.check_call(args)



git_add(torrent_path)



torrent_basename = os.path.basename(torrent_path)



# FIXME refactor with reddit_add_torrent.py

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



print("adding torrent file to git")

# git add release/opensubtitles.org.dump.10000000.to.10099999.v20240820.torrent

git_add(torrent_path)



print(f"adding release to {readme_path}")

with open(readme_path) as f:
    readme_text = f.read()

def replace_match(match):
    global torrent_basename, torrent_path
    group2 = match.group(2)
    li_list = group2.strip().split("\n")
    li = f"- [{torrent_basename}]({torrent_path})"
    if li_list[-1] != li:
        li_list.append(li)
    group2 = "\n\n" + "\n".join(li_list) + "\n\n"
    return match.group(1) + group2 + match.group(3)

group1 = "<!-- <result-list> -->"
group3 = "<!-- </result-list> -->"

readme_text_bak = readme_text

readme_text = re.sub(f"({group1})(.*?)({group3})", replace_match, readme_text, flags=re.DOTALL)

if readme_text != readme_text_bak:
    with open(readme_path, "w") as f:
        f.write(readme_text)
    git_add(readme_path)

del readme_text
del readme_text_bak



print(f"adding release to {local_subtitle_providers_json_path}")

with open(local_subtitle_providers_json_path) as f:
    local_subtitle_providers = json.load(f)

provider = {
    "id": provider_id,
    "source": "opensubtitles.org",
    "url": torrent_magnet_link,
    "num_range_from": subs_from,
    "num_range_to": subs_to,
    "type": "sqlite",
    "db_path": torrent_db_path,
    "zipfiles_table": "zipfiles",
    "zipfiles_num_column": "num",
    "zipfiles_zipfile_column": "content"
}

provider_exists = False
for p in local_subtitle_providers["providers"]:
    if p["id"] == provider["id"]:
        provider_exists = True
        break

if not provider_exists:
    # insert before the last provider
    provider_idx = len(local_subtitle_providers["providers"]) - 1
    local_subtitle_providers["providers"].insert(provider_idx, provider)

    with open(local_subtitle_providers_json_path, "w") as f:
        f.write(json.dumps(local_subtitle_providers, indent=2) + "\n")

    git_add(local_subtitle_providers_json_path)



print(f"adding release to {torrent_rss_path}")

# TODO rewrite in python
args = [
    "./release/opensubtitles.org.dump.torrent.rss.sh",
    # we need to pass torrent_path here
    # otherwise opensubtitles.org.dump.torrent.rss.sh
    # would process only committed torrent files
    torrent_path,
]

print(">", shlex.join(args))
#subprocess.run(args)
subprocess.check_call(args)

git_add(torrent_rss_path)



args = [
    "git",
    "status",
]

print(">", shlex.join(args))
#subprocess.run(args)
subprocess.check_call(args)



commit_message = f"add {torrent_basename}"

args = [
    "git",
    "status",
    "commit",
    "-m", commit_message,
]

print(">", shlex.join(args))
#subprocess.run(args)
subprocess.check_call(args)
