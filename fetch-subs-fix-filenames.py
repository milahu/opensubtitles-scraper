#! /usr/bin/env python3

# fix filenames r"^[0-9]+\.zip$" in 4781 of 111192 files

# WONTFIX rate limiting after 30 requests


new_subs_dir = "new-subs"


import os
import re
import time
import random

import requests


def change_ipaddr():
    #dev = "wan"
    # note: you must setup ssh public key authentication in openwrt
    # https://openwrt.org/docs/guide-user/security/dropbear.public-key.auth
    dev = "wan"
    dev_ifconfig = "pppoe-wan"

    def get_ipaddr():
        # get current IP address
        proc = subprocess.run(
            [
                "ssh",
                "root@192.168.178.1",
                f"ifconfig {dev_ifconfig}"
            ],
            check=True,
            capture_output=True,
            timeout=10,
            encoding="utf8",
        )
        # inet addr:79.253.14.204  P-t-P:62.155.242.79  Mask:255.255.255.255
        #print("proc.stdout", repr(proc.stdout))
        match = re.search(r"inet addr:(\d+\.\d+\.\d+\.\d+) ", proc.stdout)
        #print("match", repr(match))
        ipaddr = match.group(1)
        return ipaddr

    old_ipaddr = get_ipaddr()

    proc = subprocess.Popen(
        [
            "ssh",
            "root@192.168.178.1",
            #"sh",
            #"-c",
            f"""
                echo
                dev={dev}
                dev_ifconfig={dev_ifconfig}
                echo restarting network interface: $dev
                #set -x # debug
                ifdown $dev
                ifup $dev
                sleep 5
                while true; do
                    printf .
                    ifconfig $dev_ifconfig 2>/dev/null | grep "inet addr" && break
                    sleep 1
                done
            """,
        ],
        stdin=subprocess.DEVNULL,
    )

    try:
        proc.wait(timeout=2*60)

    except subprocess.TimeoutExpired:
        logger.info(f"killing ssh client")
        proc.kill()

    new_ipaddr = get_ipaddr()
    logger.info(f"changed IP address from {old_ipaddr} to {new_ipaddr}")
    return old_ipaddr, new_ipaddr


for filename in os.listdir(new_subs_dir):
    if not re.match(r"^[0-9]+\.zip$", filename):
        continue
    num = int(filename.split(".")[0])
    url = f"http://dl.opensubtitles.org/en/download/sub/{num}"
    print(url)
    response = requests.head(url)
    #print("response", response)
    if response.status_code != 200:
        for key in response.headers:
            value = response.headers.get(key)
            print(f"  {key}: {value}")
    assert response.status_code == 200, f"unexpected status_code {response.status_code} from url {url}"
    print("response.headers", response.headers)
    keys = []
    for key in response.headers:
        keys += [key]
    #print(", ".join(map(lambda s: f'"{s}"', keys)))
    ignore_keys = {"Date", "Connection", "Set-Cookie", "Access-Control-Allow-Headers", "Access-Control-Allow-Origin", "X-Robots-Tag", "P3P", "Content-Disposition", "Pragma", "Expires", "Content-Transfer-Encoding", "Cache-Control", "X-Cache-Backend", "Age", "X-Var-Cache", "X-Via", "CF-Cache-Status", "Report-To", "NEL", "Server", "CF-RAY", "alt-svc"}
    for key in response.headers:
        if key in ignore_keys:
            continue
        value = response.headers.get(key)
        print(f"  {key}: {value}")
    download_quota = int(response.headers.get("Download-Quota"))
    x_rateLimit_remaining = int(response.headers.get("X-RateLimit-Remaining"))
    content_disposition = response.headers.get("Content-Disposition")
    content_length = response.headers.get("Content-Length")
    new_filename = content_disposition[22:-1]
    print(f"mv {new_subs_dir}/{filename} {new_subs_dir}/{new_filename}")
    os.rename(f"{new_subs_dir}/{filename}", f"{new_subs_dir}/{new_filename}")
    #assert content_length == os.path.getsize(f"{new_subs_dir}/{new_filename}")
    print()
    time.sleep(random.randrange(1, 5))
