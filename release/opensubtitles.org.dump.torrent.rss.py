#!/usr/bin/env python3

import os
import re
import sys
import html
import subprocess
from datetime import datetime, timezone

from torf import Torrent

# Paths
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
rss_path = os.path.join(base_dir, "release", "opensubtitles.org.dump.torrent.rss")

print(f"writing {rss_path}")

# TTL: number of minutes (5 days)
ttl = 60 * 24 * 5

# Helper functions
def escape_html(s: str) -> str:
    return html.escape(s)

def get_git_tree_torrents():
    """Return a list of .torrent files tracked in git under release/."""
    result = subprocess.run(
        ["git", "ls-tree", "HEAD", "release/"],
        cwd=base_dir,
        text=True,
        capture_output=True,
        check=True
    )
    return [
        line.split("\t", 1)[1]
        for line in result.stdout.splitlines()
        if line.endswith(".torrent")
    ]

def get_creation_timestamp(torrent_path: str) -> int:
    """Return the creation date as a UNIX timestamp."""
    t = Torrent.read(torrent_path)
    if t.creation_date:
        return int(t.creation_date.timestamp())
    if m := re.search(r"\.v([0-9]{8})\.torrent$", torrent_path):
        # get creation_date from filename
        date_str = m.group(1)
        dt = datetime.strptime(date_str, "%Y%m%d")
        dt_utc = dt.replace(tzinfo=timezone.utc)
        return int(dt_utc.timestamp())
    return 0

def get_pub_date(timestamp: int) -> str:
    """Format date as RFC 2822."""
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime("%a, %d %b %Y %H:%M:%S %z")

def get_magnet_link(t: Torrent) -> str:
    """Return a magnet link without trackers."""
    magnet = str(t.magnet())
    # TODO use urllib.parse
    parts = magnet.split("&")
    # remove trackers
    parts = [p for p in parts if not p.startswith("tr=")]
    # remove exact length
    parts = [p for p in parts if not p.startswith("xl=")]
    return "&".join(parts)

# Collect torrent files: committed + args
torrent_paths = get_git_tree_torrents() + sys.argv[1:]
torrent_paths = [os.path.join(base_dir, p) for p in torrent_paths if p.endswith(".torrent")]

# Collect metadata
torrent_data = []
for path in torrent_paths:
    try:
        timestamp = get_creation_timestamp(path)
        torrent_data.append((timestamp, path))
    except Exception as e:
        print(f"Warning: failed to read {path}: {e}")

# Sort by creation date descending
torrent_data.sort(key=lambda x: x[0], reverse=True)

# Write RSS
os.makedirs(os.path.dirname(rss_path), exist_ok=True)
with open(rss_path, "w", encoding="utf-8") as f:
    f.write('<?xml version="1.0" encoding="utf-8"?>\n')
    f.write("<rss version=\"2.0\">\n")
    f.write("  <channel>\n")
    f.write("    <title>opensubtitles.org dump</title>\n")
    f.write("    <description>subtitles from opensubtitles.org</description>\n")
    f.write("    <link>https://github.com/milahu/opensubtitles-scraper</link>\n")
    f.write("    <copyright>public domain</copyright>\n")
    f.write("    <category>subtitles</category>\n")
    f.write(f"    <ttl>{ttl}</ttl>\n")

    done_first = False
    for timestamp, torrent_path in torrent_data:
        t = Torrent.read(torrent_path)
        pub_date = get_pub_date(timestamp)

        if not done_first:
            f.write(f"    <lastBuildDate>{pub_date}</lastBuildDate>\n")
            done_first = True

        guid = t.infohash
        magnetURI = get_magnet_link(t)
        title = t.name or os.path.basename(torrent_path)

        f.write("    <item>\n")
        f.write(f"      <title>{escape_html(title)}</title>\n")
        f.write(f"      <pubDate>{pub_date}</pubDate>\n")
        f.write(f"      <guid isPermaLink=\"false\">{guid}</guid>\n")
        f.write(f"      <enclosure type=\"application/x-bittorrent\" url=\"{escape_html(magnetURI)}\"/>\n")
        f.write("    </item>\n")

    f.write("  </channel>\n")
    f.write("</rss>\n")

print("done")
