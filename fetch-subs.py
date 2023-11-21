#!/usr/bin/env python3

# watch "ls -lt new-subs/ | head"

# FIXME postprocess: fix wrong dcma entries
# examples:
# these files were not processed by new-subs-migrate.py
# because dcma entries exist in new-subs-repo/files.txt
# TODO also check files in new-subs-repo/trash/
"""
$ ls new-subs-repo/ | cat
9540221.aint.she.tweet.(1952).eng.1cd.zip
9540240.book.revue.(1946).eng.1cd.zip
9540304.forget.me.(1994).dut.1cd.zip
9540310.premier.voyage.(1980).ell.1cd.zip
9540353.queen.slim.(2019).fin.1cd.zip
9540451.jewish.matchmaking.s01.e01.episode.1.1.(2023).spa.1cd.zip
9540476.jewish.matchmaking.s01.e07.so.the.song.goes.().heb.1cd.zip
9540515.jewish.matchmaking.s01.e01.episode.1.1.(2023).dut.1cd.zip
9540545.jewish.matchmaking.s01.e04.year.of.the.cindy.().rus.1cd.zip
9540550.not-found
9540572.jewish.matchmaking.s01.e04.year.of.the.cindy.().chi.1cd.zip
9540630.love.village.s01.e04.episode.1.4.().ita.1cd.zip
9540653.love.village.s01.e03.episode.1.3.().ara.1cd.zip
9540664.love.village.s01.e02.episode.1.2.().pob.1cd.zip
9540667.luke.cage.s01.e03.whos.gonna.take.the.weight.(2016).spl.1cd.zip
9540722.mama.ist.unmoglich.s01.e03.familientreffen.(1997).ger.1cd.zip

$ cat new-subs-repo/files.txt | grep -e 9540221 -e 9540240 -e 9540304 -e 9540310 -e 9540353 -e 9540451 -e 9540476
9540304.dcma
9540451.dcma
9540221.dcma
9540240.dcma
9540353.dcma
9540310.dcma
9540476.dcma



TODO verify status 404
https://github.com/milahu/opensubtitles-scraper-test/actions/runs/4908766906/jobs/8764739331
2023-05-07 18:47:38,811 INFO 9540550 404 dt=0.551 dt_avg=0.536 type=text/html; charset=UTF-8 quota=None
# https://www.opensubtitles.org/en/subtitles/9540550/jewish-matchmaking-sv
# These subtitles were disabled, you should not use them (pipporan @ 06/05/2023 04:28:54)
# Subtitles was splitted to - 9540551 - 9540552 - 9540553 - 9540554 - 9540555 - 9540556 - 9540557 - 9540558

TODO store the 404 error message? example: "These subtitles were disabled ..."

"""

# TODO quiet: remove logging output " dt={dt_download:.3f} dt_avg={dt_download_avg:.3f}"

# FIXME missing subs from github action
# bug in nums_done?

# FIXME deadloop. stop scraper at http 429 = rate-limit exceeded
# https://github.com/milahu/opensubtitles-scraper-test/actions/runs/4906991416/jobs/8761814969

# expected time: 1E6 * 0.1 / 3600 = 28 hours
# no. i over-estimated the number of requests
# it was only 300K requests, and it was done in about 1.5 days
# not bad, zenrows.com! :)

# TODO fe-fetch recent downloads
# give opensubtitles.org some time for moderation
# some time = some days = 3 days?

# NOTE zipfiles can change name over time
# example:
# a: 9524294.delete.me.new.beginnings.().eng.1cd.zip
# b: 9524294.delete.me.s02.e06.new.beginnings.().eng.1cd.zip

import sys
import os
import re
import urllib.request
import logging
import time
import datetime
import random
import hashlib
import subprocess
import json
import glob
import collections
import zipfile
import base64
import asyncio
import argparse
import atexit
import traceback
import shlex
import shutil
import tempfile

import aiohttp
import requests
import magic # libmagic
import psutil



# https://www.zenrows.com/ # Startup plan
#max_concurrency = 25 # concurrency limit was reached
max_concurrency = 10
# unexpected response_status 403. content: b'{"code":"BLK0001","detail":"Your IP address has been blocked for exceeding the maximum error rate al'...
# -> change_ipaddr()


# no. not needed because i over-estimated the missing number (?)
# the last batches should run in sequential order
# last batches = we are limited by API credits
# we dont want holes in the dataset
# done 300K = 30% of 1M
# start sequential at around 80% (better too early)
# so 80% would be
# first_num = 9180519
# options.last_num = 9520468
# 9180519 + 0.8 * 1E6 = 9980519
# 9520468 - 0.2 * 1E6 = 9320468 # pick
#sequential_fetching_after_num = 9320468


#options.sample_size = 10000 # randomize the last 4 digits
#options.sample_size = 1000 # randomize the last 3 digits
#options.sample_size = 100 # randomize the last 2 digits
#options.sample_size = 10 # randomize the last 1 digit


#if False:
#if True:
    # debug
    #max_concurrency = 1
    #options.sample_size = 10


# captcha after 30 requests
#options.proxy_provider = "chromium"

# not working. blocked by cloudflare
#options.proxy_provider = "pyppeteer"


#fetcher_lib = "requests"


pyppeteer_headless = True
pyppeteer_headless = False # debug


# note: these API keys are all expired

#options.proxy_provider = "scrapfly.io"
proxy_scrapfly_io_api_key = "scp-live-65607ed58a5449f791ba56baa5488098"

#options.proxy_provider = "scrapingdog.com"
api_key_scrapingdog_com = "643f9f3b575aa419c1d7218a"

#options.proxy_provider = "webscraping.ai"
api_key_webscraping_ai = "b948b414-dd1d-4d98-8688-67f154a74fe8"
webscraping_ai_option_proxy = "datacenter"
#webscraping_ai_option_proxy = "residential"

#options.proxy_provider = "zenrows.com"
fetcher_lib = "aiohttp"
try:
    from fetch_subs_secrets import api_key_zenrows_com
except ImportError:
    api_key_zenrows_com = "88d22df90b3a4c252b480dc8847872dac59db0e0" # expired


class Config:
    zenrows_com_antibot = False
    zenrows_com_js = False
config = Config()

#options.proxy_provider = "scraperbox.com"
proxy_scraperbox_com_api_key = "56B1354FD63EB435CA1A9096B706BD55"

#options.proxy_provider = "scrapingant.com"
api_key_scrapingant_com = "6ae0de59fad34337b2ee86814857278a"


new_subs_dir = "new-subs"
#new_subs_dir = "new-subs-repo"
#new_subs_dir = "new-subs-temp-debug"

# TODO instead of 1000, get actual system user id. bash: id -u
# use tmpfs in RAM to avoid disk writes
tempdir = "/run/user/1000"

global_remove_files_when_done = []

# https://www.opensubtitles.org/en/search/subs
# https://www.opensubtitles.org/ # New subtitles
#options.last_num = 9520468 # 2023-04-25
#options.last_num = 9521948 # 2023-04-26
#options.last_num = 9523112 # 2023-04-27
#options.last_num = 9530994 # 2023-05-01
#options.last_num = 9531985 # 2023-05-01
#options.last_num = 9533109 # 2023-05-02


parser = argparse.ArgumentParser(
    prog='fetch-subs',
    description='Fetch subtitles',
    #epilog='Text at the bottom of help',
)

default_jobs = 1
default_num_downloads = 25
default_sample_size = 1000
proxy_provider_values = [
  #"pyppeteer",
  "chromium",
  "zenrows.com",
]
default_proxy_provider = None

#parser.add_argument('filename')

parser.add_argument(
    '--proxy-provider',
    dest="proxy_provider", # options.proxy_provider
    default=default_proxy_provider,
    #choices=proxy_provider_values,
    type=str,
    metavar="S",
    help=(
        f"proxy provider. "
        f"default: {default_proxy_provider}. "
        f"values: {', '.join(proxy_provider_values)}"
    ),
)
parser.add_argument(
    '--start-vnc-client',
    dest="start_vnc_client", # options.start_vnc_client
    action='store_true',
    help=(
        f"start a local vnc client. "
        f"useful for running the scraper on a local machine. "
    ),
)
parser.add_argument(
    '--reverse-vnc-servers',
    dest="vnc_client_list", # options.vnc_client_list
    default=[],
    type=str,
    metavar="S",
    nargs="*",
    help=(
        f"reverse vnc servers. "
        f'only used with proxy provider "chromium". '
        f"this will try to connect to one of the ssh servers, "
        f"to create a TCP tunnel between the VNC server and vnc_port on the ssh server. "
        f"The default vnc_port is 5901. "
        f'alternative: pass a space-delimited list to the environment variable "REVERSE_VNC_SERVERS". '
        f"format: [user@]host[:ssh_port[:vnc_port]]. "
        f"example: --reverse-vnc-servers example.com someuser@example2.com:22:1234"
    ),
)
parser.add_argument(
    '--ssh-id-file',
    dest="ssh_id_file_path", # options.ssh_id_file_path
    default=None,
    type=str,
    metavar="S",
    help=(
        f"ssh id file path. "
        f'used for "ssh -i path/to/ssh-id-file" to connect to a vnc client. '
        f"example: ~/.ssh/id_rsa"
    ),
)
parser.add_argument(
    '--jobs',
    default=default_jobs,
    type=int,
    metavar="N",
    help=f"how many jobs to run in parallel. default: {default_jobs}",
)
parser.add_argument(
    '--num-downloads',
    dest="num_downloads",
    default=default_num_downloads,
    #type=int,
    metavar="N",
    help=(
        f"limit the number of downloads. "
        f"default: {default_num_downloads}. "
        f"can be a range like 10-20, then value is random."
    ),
)
parser.add_argument(
    '--sample-size',
    dest="sample_size",
    default=default_sample_size,
    type=int,
    metavar="N",
    help=f"size of random sample. default: {default_sample_size}",
)
parser.add_argument(
    '--first-num',
    dest="first_num",
    default=None,
    type=int,
    metavar="N",
    help="first subtitle number. default: get from store",
)
parser.add_argument(
    '--last-num',
    dest="last_num",
    default=None,
    type=int,
    metavar="N",
    help="last subtitle number. default: get from remote",
)
parser.add_argument(
    "--show-ip-address",
    dest="show_ip_address",
    default=False,
    action="store_true",
    help="show IP address. default: false. note: this is slow",
)
parser.add_argument(
    "--debug",
    default=False,
    action="store_true",
    help="show debug messages",
)
parser.add_argument(
    "--force-download",
    dest="force_download",
    default=False,
    action="store_true",
    help="also download when files exist",
)
#options = parser.parse_args(sys.argv)
options = parser.parse_args()

options.vnc_client_list += re.split(r"\s+", os.environ.get("REVERSE_VNC_SERVERS", ""))

logging_level = "INFO"
if options.debug:
    logging_level = "DEBUG"

logging.basicConfig(
    format='%(asctime)s %(levelname)s %(message)s',
    level=logging_level,
)

logger = logging.getLogger("fetch-subs")

def logger_print(*args):
    logging.info(" ".join(map(str, args)))


if type(options.num_downloads) == str:
    logger_print("options.num_downloads", repr(options.num_downloads))
    if re.match(r"^\d+$", options.num_downloads):
        options.num_downloads = int(options.num_downloads)
    elif re.match(r"^(\d+)-(\d+)$", options.num_downloads):
        m = re.match(r"^(\d+)-(\d+)$", options.num_downloads)
        options.num_downloads = random.randint(int(m.group(1)), int(m.group(2)))
        logging.info(f"options.num_downloads: {options.num_downloads}")


# postprocess: fetch missing subs
# example: https://www.opensubtitles.org/en/subtitles/9205951
# this is a bug in opensubtitles.org
# the server returns infinite cyclic redirect via
# https://www.opensubtitles.org/en/msg-dmca
# and zenrows says: error: need javascript
# ... so these files were deleted because of dcma takedown requests (by copyright trolls)
missing_numbers = None
missing_numbers_txt_path = "missing_numbers.txt"
if os.path.exists(missing_numbers_txt_path):
    logger_print(f"loading missing_numbers from {missing_numbers_txt_path}")
    with open(missing_numbers_txt_path, "r") as f:
        missing_numbers = list(map(int, f.read().strip().split("\n")))
if missing_numbers:
    logger_print(f"fetching {len(missing_numbers)} missing numbers:", missing_numbers)

    # postprocess: create empty dcma files
    # TODO detect these files while scraping
    # in the future, zenrows may return a different error than
    # RESP001 (Could not get content. try enabling javascript rendering)
    # zenrows support:
    # > The error might be misleading, but apart from changing that, we can't do anything else.
    # > BTW, if they return a status code according to the error, you might get it back with original_status=true
    #for num in missing_numbers:
    #    # create empty file
    #    filename_dcma = f"{new_subs_dir}/{num}.dcma"
    #    open(filename_dcma, 'a').close() # create empty file
    #raise Exception("done postprocessing")

# sleep X seconds after each download
sleep_each_min, sleep_each_max = 0, 3

# sleep X seconds after blocked by server
sleep_blocked = 24*60*60

# sleep X seconds after changing IP address
sleep_change_ipaddr = 10

is_greedy = False
is_greedy = True



if is_greedy:
    sleep_each_min, sleep_each_max = 0, 0
    sleep_change_ipaddr = 0


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
        #logger_print("proc.stdout", repr(proc.stdout))
        match = re.search(r"inet addr:(\d+\.\d+\.\d+\.\d+) ", proc.stdout)
        #logger_print("match", repr(match))
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
        logger_print(f"killing ssh client")
        proc.kill()

    new_ipaddr = get_ipaddr()
    logger_print(f"changed IP address from {old_ipaddr} to {new_ipaddr}")
    return old_ipaddr, new_ipaddr


if False:
    logger_print("changing IP address")
    change_ipaddr()


def change_ipsubnet():
    def get_subnet(ipaddr):
        return ".".join(ipaddr.split(".")[0:3])
    first_ipaddr = None
    while True:
        old_ipaddr, new_ipaddr = change_ipaddr()
        if not first_ipaddr:
            first_ipaddr = old_ipaddr
        old_subnet = get_subnet(old_ipaddr)
        new_subnet = get_subnet(new_ipaddr)
        if old_subnet != new_subnet:
            logger_print(f"changed IP subnet from {first_ipaddr} to {new_ipaddr}")
            return first_ipaddr, new_ipaddr


def new_requests_session():
    global user_agents
    requests_session = requests.Session()
    #return requests_session
    # https://httpbin.org/headers
    # chromium headers:
    user_agent = random.choice(user_agents)
    requests_session.headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "en-US,en;q=0.9",
        "Sec-Ch-Ua": '"Not A(Brand";v="24", "Chromium";v="110"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Linux"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": user_agent,
    }
    return requests_session


async def fetch_num(num, aiohttp_session, semaphore, dt_download_list, t2_download_list, html_errors, config):

    async with semaphore: # limit parallel downloads

        t1_download = time.time()

        # handled by nums_done
        """
        filename_glob = f"{new_subs_dir}/{num}.*"
        filename_zip = f"{new_subs_dir}/{num}.zip"
        filename_notfound = f"{new_subs_dir}/{num}.not-found"

        # handled by nums_done?
        # check again to make sure:
        existing_output_files = glob.glob(filename_glob)
        if len(existing_output_files) > 0:
            logger_print(f"{num} output file exists: {existing_output_files}")
            #continue
            return
        """

        # note: later use actual filename from content_disposition
        filename_zip = f"{new_subs_dir}/{num}.zip"
        filename_notfound = f"{new_subs_dir}/{num}.not-found"

        filename = filename_zip

        # https://dl.opensubtitles.org/en/download/sub/{IDSubtitle}
        # these urls return zip files, which can contain multiple subtitle files
        # either because of multipart (2cd, 3cd, 4cd, ...)
        # or for additional hearing-impaired subtitles.
        # individual files can be downloaded from
        # https://dl.opensubtitles.org/en/download/file/{IDSubtitleFile}

        # there is no export for the relation
        # between IDSubtitle and IDSubtitleFile.
        # also the nfo files do not contain IDSubtitleFile.
        # for each IDSubtitle, we can parse the info page
        # https://www.opensubtitles.org/en/subtitles/{IDSubtitle}
        # grep for "/download/file/" or "subtitlefileids"

        #url = f"https://www.opensubtitles.org/en/subtitleserve/sub/{num}"
        # redirect location:
        #url = f"https://dl.opensubtitles.org/en/download/sub/{num}"
        # use http protocol to fix: aiohttp.client_exceptions.ClientConnectorCertificateError: Cannot connect to host dl.opensubtitles.org:443 ssl:True [SSLCertVerificationError: (1, '[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self-signed certificate in certificate chain (_ssl.c:997)')]
        url = f"http://dl.opensubtitles.org/en/download/sub/{num}"
        proxies = {}
        requests_get_kwargs = {}
        content_type = None
        response_status = None
        content_disposition = None
        response_headers = None
        response_content = None

        if options.proxy_provider == "scrapingant.com":
            query = urllib.parse.urlencode({
                "url": url,
                "x-api-key": api_key_scrapingant_com,
                "browser": "false",
            })
            url = f"https://api.scrapingant.com/v2/general?{query}"
            # TODO aiohttp
            response = requests.get(url, **requests_get_kwargs)
            response_status = response.response_status

        elif options.proxy_provider == "zenrows.com":
            #proxy = f"http://{api_key_zenrows_com}:@proxy.zenrows.com:8001"
            zenrows_com_query_parts = []
            if config.zenrows_com_antibot:
                logger_print(f"{num} antibot=true")
                zenrows_com_query_parts += ["antibot=true"]
                # reset config for next request
                config.zenrows_com_antibot = False
            if config.zenrows_com_js:
                logger_print(f"{num} js_render=true")
                zenrows_com_query_parts += ["js_render=true"]
                # reset config for next request
                config.zenrows_com_js = False
            zenrows_com_query = "&".join(zenrows_com_query_parts)
            proxy = f"http://{api_key_zenrows_com}:{zenrows_com_query}@proxy.zenrows.com:8001"
            proxies = {"http": proxy, "https": proxy}
            #requests_get_kwargs["proxies"] = proxies # requests
            requests_get_kwargs["proxy"] = proxy # aiohttp
            #requests_get_kwargs["verify"] = False # requests
            try:
                #response = requests.get(url, **requests_get_kwargs)
                response = await aiohttp_session.get(url, **requests_get_kwargs)
            except (
                #requests.exceptions.ProxyError,
                asyncio.exceptions.TimeoutError,
            ) as err:
                # requests.exceptions.ProxyError: HTTPSConnectionPool(host='dl.opensubtitles.org', port=443): Max retries exceeded with url: /en/download/sub/9188285 (Caused by ProxyError('Cannot connect to proxy.', NewConnectionError('<urllib3.connection.HTTPSConnection object at 0x7fa473cadcf0>: Failed to establish a new connection: [Errno -3] Temporary failure in name resolution')))
                logger_print(f"{num} retry. error: {err}")
                return num # retry
            #logger_print("response", dir(response))
            #response_status = response.response_status # requests
            response_status = response.status # aiohttp
            content_type = response.headers.get("Zr-Content-Type")
            content_disposition = response.headers.get("Zr-Content-Disposition")

        elif options.proxy_provider == "scrapingdog.com":
            query = urllib.parse.urlencode({
                "url": url,
                "api_key": api_key_scrapingdog_com,
                "dynamic": "false", # dont eval javascript
            })
            url = f"https://api.scrapingdog.com/scrape?{query}"

            # TODO aiohttp
            response = requests.get(url, **requests_get_kwargs)

            response_status = response.response_status
            logger_print(f"{num} response_status: {response_status}")

            logger_print(f"{num} headers: {response.headers}")

            if response_status != 200:
                # 404 -> always JSON?
                logger_print(f"{num} content: {response_content}")

            # original headers are missing: Content-Type, Content-Disposition, ...
            magic_result = magic.detect_from_content(response_content)
            logger_print(f"{num} libmagic result: type: {magic_result.mime_type}, encoding: {magic_result.encoding}, name: {magic_result.name}")
            # examples: text/html, application/zip
            content_type = magic_result.mime_type
            if content_type == "application/octet-stream":
                # response_content is broken?
                # $ unzip -l 9185494.zip
                # error [9185494.zip]:  missing 985487216 bytes in zipfile
                logger_print(f"{num} libmagic failed to detect zip file. fixing content_type")
                content_type = "application/zip"
            if magic_result.encoding != "binary":
                content_type += f"; charset={magic_result.encoding}"
                # example: text/html; charset=utf-8
                # example: text/html; charset=us-ascii

        elif options.proxy_provider == "webscraping.ai":
            # https://docs.webscraping.ai/reference/gethtml
            query = urllib.parse.urlencode({
                "url": url,
                "api_key": api_key_webscraping_ai,
                "proxy": webscraping_ai_option_proxy,
                "js": "false", # dont eval javascript
            })
            url = f"https://api.webscraping.ai/html?{query}"

            # TODO aiohttp
            response = requests.get(url, **requests_get_kwargs)

            response_status = response.response_status
            logger_print(f"{num} response_status: {response_status}")

            logger_print(f"{num} headers: {response.headers}")

        elif options.proxy_provider == "scrapfly.io":
            # https://scrapfly.io/dashboard
            # https://scrapfly.io/docs/scrape-api
            query = urllib.parse.urlencode({
                "url": url,
                "key": proxy_scrapfly_io_api_key,
                "asp": "true", # anti scraping protection. variable cost of API Credits
                #"tags": "project:default",
                #"proxy_pool": "public_datacenter_pool", # 1 API Credits will be counted
                #"proxy_pool": "public_residential_pool", # 25 API Credits will be counted
                #"proxy": webscraping_ai_option_proxy,
                #"js": "false", # dont eval javascript
            })
            url = f"https://api.scrapfly.io/scrape?{query}"

            # TODO aiohttp
            response = requests.get(url, **requests_get_kwargs)

            response_data = json.loads(response.content)

            #response_status = response.response_status
            response_status = response_data["result"]["response_status"]

            if (
                response_data["result"]["success"] == False and
                response_status != 404
            ):
                logger_print(f"""{num} success: False. reason: {response_data["result"]["reason"]}""")

            if True:
                response_data_file = f"{new_subs_dir}/{num}.scrapfly.json"
                logger_print(f"""{num} writing json response to file: {response_data_file}""")
                with open(response_data_file, "wb") as f:
                    f.write(response.content)

            # TODO type error: response.result.response_headers must be array
            response_headers = requests.structures.CaseInsensitiveDict(response_data["result"]["response_headers"])

            if response_data["result"]["format"] == "text":
                response_content = response_data["result"]["content"]
            elif response_data["result"]["format"] == "binary":
                response_content = base64.b64decode(response_data["result"]["content"])
            else:
                raise Exception(f"""unknown result format: {response_data["result"]["format"]}""")

            #logger_print(f"{num} response_status: {response_status}")

            #logger_print(f"{num} headers: {response_headers}")

            #logger_print(f"{num} proxy pool: {response_data['context']['proxy']['pool']}")
            #logger_print(f"{num} cost total: {response_data['context']['cost']['total']}")
            #logger_print(f"{num} cost details: {response_data['context']['cost']['details']}")
            logger.debug(f"{num} cost: {response_data['context']['cost']['total']} = {response_data['context']['cost']['details']}")

        elif options.proxy_provider == "scraperbox.com":
            # https://scraperbox.com/dashboard
            query = urllib.parse.urlencode({
                "url": url,
                "token": proxy_scraperbox_com_api_key,
                #"javascript_enabled": "true",
                #"proxy_location": "all",
                #"residential_proxy": "true",
            })
            url = f"https://scraperbox.com/api/scrape?{query}"

            # TODO aiohttp
            response = requests.get(url, **requests_get_kwargs)

            response_status = response.response_status
            logger_print(f"{num} response_status: {response_status}")

            logger_print(f"{num} headers: {response.headers}")

        elif options.proxy_provider == "chromium":

            # FIXME handle file download. where is the file saved?
            # the last html page is the cloudflare portal saying "Proceeding..."

            # TODO handle captchas by cloudflare.
            # effectively, implement a semiautomatic web scraper
            # which asks for help from the user to solve captchas

            response = await chromium_headful_scraper.get_response(url, return_har_path=True)
            logger_print(f"TODO debug har file: {response.har_path}")
            response_status = response.status
            response_headers = response.headers
            response_type = response.headers.get("Content-Type")

            # TODO handle binary response
            #response_text = await response.text()

            response_content = response.content

            logger_print("response_status", response_status)
            logger_print("response_type", response_type)
            logger_print("response_text", repr(response_text)[0:100] + " ...")

            time.sleep(10)

            downloaded_files = glob.glob(chromium_headful_scraper.downloads_path + f"/*.({num}).zip")
            logger_print("downloaded_files", downloaded_files)

            raise NotImplementedError

            if len(downloaded_files) != 1:
                logger_print(f"error: found multiple downloaded files for num={num}:", downloaded_files)
                raise NotImplementedError

            # len(downloaded_files) == 1
            filepath = downloaded_files[0]
            filename = os.path.basename(filepath)
            output_path = f"{new_subs_dir}/{num}.{filename}"
            os.rename(filepath, output_path)

            #logger.debug("headers: " + repr(dict(headers)))
            sleep_each = random.randint(sleep_each_min, sleep_each_max)
            if sleep_each > 0:
                logger_print(f"{num} 200 dt={dt_download:.3f} dt_avg={dt_download_avg:.3f}{dt_par_str} -> waiting {sleep_each} seconds")
            else:
                logger_print(f"{num} 200 dt={dt_download:.3f} dt_avg={dt_download_avg:.3f}{dt_par_str}")
            #if dt_download_avg_parallel > 1:
            #    logger_print(f"460: {num} 200 dt_download_avg_parallel > 1: dt_download_list_parallel = {dt_download_list_parallel}")
            time.sleep(sleep_each)
            #continue
            return

        elif options.proxy_provider == "pyppeteer":
            logger_print("pyppeteer_page.goto", url)
            await pyppeteer_page.goto(url)
            raise NotImplementedError

        else:
            # no proxy
            # requests
            #response = requests.get(url, **requests_get_kwargs)
            #response_status = response.response_status
            # aiohttp
            response = await aiohttp_session.get(url, **requests_get_kwargs)
            response_status = response.status
            logger.debug(f"{num} response_status: {response_status}")
            logger.debug(f"{num} headers: {response.headers}")

        response_content = response_content or response.content
        response_headers = response_headers or response.headers

        # https://scrapingant.com/free-proxies/
        #proxy = "socks5://54.254.52.187:8118"

        if options.proxy_provider == "scrapingant.com":
            try:
                response_status = int(response_headers["Ant-Page-Status-Code"])
            except KeyError as err:
                logger_print(f"{num} response_status={response_status} KeyError: no Ant-Page-Status-Code. headers: {response_headers}. content: {response_content[0:100]}...")

        #logger_print(f"{num} response_status={response_status} headers:", response_headers)

        # debug rate-limiting
        # X-RateLimit-Remaining is constant at 40
        # Download-Quota is between 200 and 0
        debug_headers_str = ""
        debug_headers_str += f" type={response.headers.get('Content-Type')}"
        debug_headers_str += f" quota={response.headers.get('Download-Quota')}"

        if response_status == 404:
            open(filename_notfound, 'a').close() # create empty file
            debug_404_pages = False
            if debug_404_pages:
                response_text = (await response_content.read()).decode("utf8")
                with open(f"{filename_notfound}.html", 'w') as f:
                    f.write('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">\n')
                    f.write("<!-- response headers:\n")
                    for key in response_headers:
                        f.write(f"{key}: {response_headers[key]}\n")
                    f.write("-->\n")
                    f.write(response_text)
            t2_download = time.time()
            dt_download = t2_download - t1_download
            dt_download_list.append(dt_download)
            t2_download_list.append(t2_download)
            t2_download_list_sorted = sorted(t2_download_list)
            dt_download_avg = sum(dt_download_list) / len(dt_download_list)
            # FIXME use options.jobs to get dt_download_avg_parallel
            dt_download_list_parallel = []
            for i in range(0, len(t2_download_list_sorted) - 1):
                t2 = t2_download_list_sorted[i]
                t2_next = t2_download_list_sorted[i + 1]
                dt = t2_next - t2
                dt_download_list_parallel.append(dt)
            if len(dt_download_list_parallel) > 0:
                dt_download_avg_parallel = sum(dt_download_list_parallel) / len(dt_download_list_parallel)
            else:
                dt_download_avg_parallel = 0

            dt_par_str = ""
            if options.jobs > 1:
                dt_par_str = f" dt_par={dt_download_avg_parallel:.3f}"

            logger_print(f"{num} {response_status} dt={dt_download:.3f} dt_avg={dt_download_avg:.3f}{dt_par_str}{debug_headers_str}")
            #if dt_download_avg_parallel > 1:
            #    logger_print(f"499: {num} 200 dt_download_avg_parallel > 1: dt_download_list_parallel = {dt_download_list_parallel}")
            #num += 1
            #continue
            return # success

        # debug
        #logger_print(f"options.proxy_provider: {repr(options.proxy_provider)}")

        if options.proxy_provider == None and response_status == 429:
            # rate limiting
            # this happens after 30 sequential requests
            # only successful requests are counted (http 404 is not counted)
            # blocking is done by cloudflare?
            #logger_print(f"{num} {response_status} Too Many Requests -> waiting {sleep_blocked} seconds")
            #await asyncio.sleep(sleep_blocked)
            logger_print(f"{num} {response_status} response_headers", response_headers)
            logger_print(f"{num} {response_status} Too Many Requests -> stopping scraper")
            # stop scraper. retry would cause infinite loop
            raise SystemExit

            user_agent = random.choice(user_agents)

            if downloads_since_change_ipaddr == 0:
                # after too many change_ipaddr, they are blocking our subnet
                logger_print(f"{num} {response_status} Too Many Requests + no downloads -> changing IP subnet")
                # no. this takes too long and does not work,
                # because our user-agent is blocked
                #change_ipsubnet()
            else:
                logger_print(f"{num} {response_status} Too Many Requests -> changing IP address")
                change_ipaddr()
            downloads_since_change_ipaddr = 0
            # fix: http.client.RemoteDisconnected: Remote end closed connection without response
            # TODO aiohttp
            requests_session = new_requests_session()
            time.sleep(sleep_change_ipaddr)
            #continue
            return # success

        if response_status == 500:
            logger_print(f"{num} {response_status} Internal Server Error -> retry")
            return num # retry

        if response_status == 429:
            if False and content_type == "text/html; charset=UTF-8":
                # captcha page
                # bug in proxy provider
                logger_print(f"{num} {response_status} captcha -> retry")
                return num # retry
            response_text = (await response_content.read()).decode("utf8")
            content_type = content_type or response_headers.get("Content-Type")
            error_filename = f"http-429-at-num-{num}.html"
            logger_print(f"{num} {response_status} response_headers", response_headers)
            logger_print(f"{num} {response_status} content_type={repr(content_type)} + response_text in {error_filename} -> retry")
            with open(error_filename, "w") as f:
                f.write(response_text)
            return num # retry

        if response_status in {422, 403, 503}:
            response_text = (await response_content.read()).decode("utf8")
            logger_print(f"{num} {response_status} response_text: {repr(response_text)}")
            if response_text == "":
                # json.loads -> json.decoder.JSONDecodeError Expecting value
                logger_print(f"{num} {response_status} got empty response_text -> retry")
                return num
            response_data = json.loads(response_text)
            if response_data["code"] == "RESP001":
                # Could not get content. try enabling javascript rendering for a higher success rate (RESP001)
                #config.zenrows_com_js = True
                #config.zenrows_com_antibot = True
                #logger_print(f"{num} retry. error: need javascript")
                logger_print(f"{num} 404 dcma")
                # create empty file
                filename_dcma = f"{new_subs_dir}/{num}.dcma"
                open(filename_dcma, 'a').close() # create empty file
                return # success
                #return num # retry
                #return {"retry_num": num, "pause": True} # pause scraper, retry
            if response_data["code"] == "AUTH006":
                # The concurrency limit was reached. Please upgrade to a higher plan or ...
                logger_print(f"{num} {response_status} retry. error: concurrency limit was reached @ {response_text}")
                return {"retry_num": num, "pause": True} # pause scraper, retry
            if response_data["code"] == "BLK0001":
                # Your IP address has been blocked for exceeding the maximum error rate ...
                logger_print(f"{num} {response_status} retry. error: IP address was blocked @ {response_text}")
                return {"retry_num": num, "pause": True, "change_ipaddr": True} # pause scraper, change IP address, retry
            if response_data["code"] == "CTX0002":
                # Operation timeout exceeded (CTX0002)
                return {"retry_num": num, "pause": True} # pause scraper, retry
            logger_print(f"{num} {response_status} retry. headers: {response_headers}. content: {await response_content.read()}")
            return num # retry

        # requests
        #assert response_status == 200, f"{num} unexpected response_status {response_status}. headers: {response_headers}. content: {response_content[0:100]}..."
        # aiohttp
        assert response_status == 200, f"{num} unexpected response_status {response_status}. headers: {response_headers}. content: {await response_content.read()}"

        content_type = content_type or response_headers.get("Content-Type")

        if content_type != "application/zip":
            # blocked
            # TODO retry download
            #logger_print(f"{num} response_status={response_status} content_type={content_type}. headers: {response_headers}. content: {response_content[0:100]}...")
            if content_type in {"text/html", "text/html; charset=UTF-8", "text/html; charset=utf-8"}:
                # can be "not found" or "blocked":
                # not found: [CRITICAL ERROR] Subtitle id {num} was not found in database
                # blocked: CAPTCHA robot test
                #   see also: https://forum.opensubtitles.org/viewtopic.php?f=1&t=14559
                #    Q: All users are affected ?
                #    A: Nope, not at all. There are just couple of thousands IPs affected,
                #       usually known proxies, TOR, spammers, harvesters and so on.
                # blocked shows after about 30 requests
                # can also be alert:
                # alert: Turn off adblocker, otherwise site will not work properly. You can use different browser or browser in incognito/private mode
                if response_headers.get("Zr-Final-Url") == "https://www.opensubtitles.org/en/login/vrf-on":
                    logger_print(f"""{num} FIXME Zr-Final-Url: {response_headers.get("Zr-Final-Url")}""")
                else:
                    logger_print(f"{num} response_status={response_status} content_type={content_type}. headers: {response_headers}")
                filename = f"{new_subs_dir}/{num}.html"
                i = 1
                while os.path.exists(filename):
                    i += 1
                    filename = f"{new_subs_dir}/{num}.{i}.html"
            else:
                filename=f"{new_subs_dir}/{num}.unknown"
                logger_print(f"{num} saving response_content to file: {filename}")
                with open(filename, "wb") as dst:
                    dst.write(response_content)
                #logger_print(f"{num} response_status={response_status} content_type={content_type}. headers: {response_headers}. content: {response_content[0:100]}...")
                raise NotImplementedError(f"{num}: unknown Content-Type: {content_type}")

        #logger_print(f"{num} response", dir(response))
        #logger_print(f"{num} response_headers", response_headers)
        # 'Zr-Content-Disposition': 'attachment; filename="nana.s01.e14.family.restaurant.of.shambles.(2006).ita.1cd.(9181475).zip"'
        content_disposition = content_disposition or response_headers.get("Content-Disposition")

        if content_disposition:
            # use filename from response_headers
            content_filename = content_disposition[22:-1]
            filename = f"{new_subs_dir}/{num}.{content_filename}"
            # remove the f".({num})" part from filename
            # adding f"{num}." to start of filename makes the filename too long
            # fix: OSError: [Errno 36] File name too long
            # 258 == len("9371758.zombieland.saga.s01.e09.though.my.life.may.have.ended.once.by.some.twist.of.fate.i.have.risen.and.if.song.and.dance.are.to.be.my.fate.then.carrying.the.memories.of.my.comrades.in.my.heart.as.i.sally.forth.shall.be.my.saga.(2018).spa.1cd.(9371758).zip")
            # 250 == len("zombieland.saga.s01.e09.though.my.life.may.have.ended.once.by.some.twist.of.fate.i.have.risen.and.if.song.and.dance.are.to.be.my.fate.then.carrying.the.memories.of.my.comrades.in.my.heart.as.i.sally.forth.shall.be.my.saga.(2018).spa.1cd.(9371758).zip")
            # 248 == len("9371758.zombieland.saga.s01.e09.though.my.life.may.have.ended.once.by.some.twist.of.fate.i.have.risen.and.if.song.and.dance.are.to.be.my.fate.then.carrying.the.memories.of.my.comrades.in.my.heart.as.i.sally.forth.shall.be.my.saga.(2018).spa.1cd.zip")
            # a: new-subs/1.alien.3.(1992).eng.2cd.(1).zip
            # b: new-subs/1.alien.3.(1992).eng.2cd.zip
            suffix = f".({num}).zip"
            assert filename.endswith(suffix)
            filename = filename[0:(-1 * len(suffix))] + ".zip"
        else:
            # file basename is f"{num}.zip"
            #logger_print(f"{num} FIXME missing filename? response_headers", response_headers)
            pass

        # all filenames should be ascii
        try:
            filename.encode("ascii")
        except UnicodeEncodeError as err:
            logger.error(f"{num} FIXME found non-ascii filename {repr(filename)}")

        # atomic write
        # limit filename length to 255 bytes
        # fix: OSError: [Errno 36] File name too long
        filename_tmp_base = filename
        while len(filename_tmp_base.encode("utf8")) > (255 - 4):
            # remove last char
            filename_tmp_base = filename_tmp_base[0:-1]
        filename_tmp = filename_tmp_base + ".tmp"

        file_open_mode = "wb"
        if type(response_content) == str:
            file_open_mode = "w"

        if type(response_content) in {str, bytes}:
            # requests
            with open(filename_tmp, file_open_mode) as f:
                f.write(response_content)
        elif hasattr(response_content, "read"):
            # aiohttp
            with open(filename_tmp, file_open_mode) as f:
                f.write(await response_content.read())
        else:
            raise NotImplementedError(f"read response_content object of type {type(response_content)}")

        os.rename(filename_tmp, filename)

        if filename.endswith(".html"):
            html_errors.append(True)
            html_error_probability = sum(map(lambda _: 1, filter(lambda x: x == True, html_errors))) / len(html_errors)
            logger_print(f"{num} retry. error: html p={html_error_probability * 100:.2f}%")
            return num # retry
        else:
           html_errors.append(False)

        # check file
        if filename.endswith(".zip"):
            logger.debug(f"checking zipfile {filename}")
            try:
                with zipfile.ZipFile(filename, "r") as z:
                    logger.debug(f"files in zipfile {filename}:")
                    for name in z.namelist():
                        logger.debug(f"  {name}")
            except zipfile.BadZipFile as err:
                logger_print(f"{num} broken zipfile: {filename} - moving to {filename}.broken - error: {err}")
                os.rename(filename, filename + ".broken")

        t2_download = time.time()
        dt_download = t2_download - t1_download
        dt_download_list.append(dt_download)
        t2_download_list.append(t2_download)
        t2_download_list_sorted = sorted(t2_download_list)
        dt_download_avg = sum(dt_download_list) / len(dt_download_list)
        # FIXME use options.jobs to get dt_download_avg_parallel
        dt_download_list_parallel = []
        for i in range(0, len(t2_download_list_sorted) - 1):
            t2 = t2_download_list_sorted[i]
            t2_next = t2_download_list_sorted[i + 1]
            dt = t2_next - t2
            dt_download_list_parallel.append(dt)
        if len(dt_download_list_parallel) > 0:
            dt_download_avg_parallel = sum(dt_download_list_parallel) / len(dt_download_list_parallel)
        else:
            dt_download_avg_parallel = 0

        dt_par_str = ""
        if options.jobs > 1:
            dt_par_str = f" dt_par={dt_download_avg_parallel:.3f}"

        #logger_print("t2_download_list", t2_download_list)
        #logger_print("dt_download_list_parallel", dt_download_list_parallel)

        #logger.debug("headers: " + repr(dict(headers)))
        sleep_each = random.randint(sleep_each_min, sleep_each_max)
        if sleep_each > 0:
            logger_print(f"{num} 200 dt={dt_download:.3f} dt_avg={dt_download_avg:.3f}{dt_par_str}{debug_headers_str} -> waiting {sleep_each} seconds")
        else:
            logger_print(f"{num} 200 dt={dt_download:.3f} dt_avg={dt_download_avg:.3f}{dt_par_str}{debug_headers_str}")
        #if dt_download_avg_parallel > 1:
        #    logger_print(f"635: {num} 200 dt_download_avg_parallel > 1: dt_download_list_parallel = {dt_download_list_parallel}")
        #await asyncio.sleep(sleep_each)
        #break
        #num += 1
        return # success



# global state, shared between functions
user_agents = None
chromium_headful_scraper = None



def random_hash():
    return hex(random.getrandbits(128))[2:]

def datetime_str():
    # https://stackoverflow.com/questions/2150739/iso-time-iso-8601-in-python#28147286
    return datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%S.%fZ")

def sha1sum(file_path):
    # https://stackoverflow.com/questions/22058048/hashing-a-file-in-python
    # BUF_SIZE is totally arbitrary, change for your app!
    BUF_SIZE = 65536  # lets read stuff in 64kb chunks!
    #md5 = hashlib.md5()
    sha1 = hashlib.sha1()
    with open(file_path, 'rb') as f:
        while data := f.read(BUF_SIZE):
            #md5.update(data)
            sha1.update(data)
    return sha1.digest()
    #print("SHA1: {0}".format(sha1.hexdigest()))



from collections import namedtuple



VNCClient = namedtuple("VNCClient", "user host ssh_port vnc_port")



class ChromiumHeadfulScraper():

    """
    a headful chromium web scraper, written in python
    """

    chromium_window_id = None
    vnc_client_list = []
    vnc_client_port = 43022
    connected_vnc_client = None
    xvnc_process = None
    xvnc_port = None
    xvnc_display = None
    xvnc_env = None
    #window_manager_name = "icewm"
    window_manager_name = "picom" # needed to invert colors on the xvnc server
    xvnc_invert_colors = True
    is_multi_window = False # "picom" is not a window manager
    window_manager_process = None
    vnc_client_process = None
    ssh_process = None
    ssh_id_file_path = None

    temp_home = None
    downloads_path = None

    chromium_process = None
    chromium_user_data_dir = None
    chromium_config = None
    chromium_config_path = None

    request_number = 0

    # TODO more + dynamic learning of screenshot hashes
    screenshot_hashes = {
        # "X" = loading, click to stop loading
        "loading": set([
            bytes.fromhex("52912e087f65890ff39ca19064e3a63b5209d521"),
        ]),
        # "O" = done loading, click to reload
        "done_loading": set([
            bytes.fromhex("0258982600b873d822665e520de4573ac62d4f08"),
        ]),
        "done_saving_har_file": set([
            # this is just black (background in darkmode)
            # when the har file is being saved
            # then there is a red square "stop" symbol, next to a progress bar
            # this is only visible for large har files
            bytes.fromhex("8ea5cf7fbe847958705fc069903e8889806adbf2"),
        ]),
        "show_notifications_popup_block_allow": set([
            bytes.fromhex("107cdc4400f0e53cc5b70de7b11d9fcb128767ac"),
        ]),
        "chromium_address_bar_icon_has_popup": set([
            #bytes.fromhex("cc9d2009ad00574cfc7c7885e4dc99a6153f1b5f"), # TODO remove?
            bytes.fromhex("60dc87cda1947c632d4d1634bbeff953738d059e"),
        ]),
        "chromium_devtools_sources_breakpoints_on": set([
            #bytes.fromhex("f25ccb7db0f786dd69cbe6fcb0338847eda3866c"), # TODO remove?
            #bytes.fromhex("41bbbc18a3c90e34bc51dfb8761aeaaed487d63f"), # TODO remove?
            bytes.fromhex("671a42024e4774a7e043506c0c6d257ed3fc8fbb"),
        ]),
        "chromium_devtools_sources_breakpoints_off": set([
            #bytes.fromhex("adbfb14d3993ccbd48b1334e5aac6a6afff85a20"), # TODO remove?
            #bytes.fromhex("b2a289dde8618a46814c44b3be52b9c2d391069a"), # TODO remove?
            bytes.fromhex("9d6b983460965ad2773c6754adbb39fbf698bd58"),
        ]),
    }

    def set_vnc_client_list(self, server_list):
        # parse list of strings
        # example string: someuser@somehost.com:22:5901
        for server_str in server_list:
            user, host, ssh_port, vnc_port = re.match(r"(?:([a-zA-Z0-9._-]+)@)?([a-zA-Z0-9._-]+)(?::([0-9]+)(?::([0-9]+))?)?", "me@asdf.com:123:456").groups()
            user = user or "fetch-subs"
            ssh_port = int(ssh_port) if ssh_port else 22
            vnc_port = int(vnc_port) if vnc_port else 5901
            vnc_client = VNCClient(user, host, ssh_port, vnc_port)
            self.vnc_client_list.append(vnc_client)

    async def start_xvnc_server(self):
        # Xvnc is provided by the tigervnc package

        # FIXME the script hangs when Xvnc stops
        # [ 11/21/23 15:19:07.725 handle_queued_x_events FATAL ERROR ] X11 server connection broke (error 1)
        # X connection to :2 broken (explicit kill or server shutdown).

        # TODO install tigervnc in github CI
        # TODO find a free display number on this machine
        xvnc_display = 2
        # TODO quiet, only print fatal errors
        # level is between 0 and 100, 100 meaning most verbose output.
        log_level = 0
        args = [
            "Xvnc",
            "-Log", f"*:stderr:{log_level}",
            # dont require a password
            "-SecurityTypes", "none",
            # TODO allow to change these options via the fetch-subs.py CLI
            "-geometry", "1024x768", # default: 1024x768
            "-depth", "16", # default: 24
            "-FrameRate", "10", # maximum frame rate. default: 60
            "-localhost", # accept connections only from localhost
        ]

        if False:
            # run this server for 5 minutes = 300 seconds
            args += [
                "-MaxDisconnectionTime", "300",
                "-MaxConnectionTime", "300",
                "-MaxIdleTime", "300",
            ]

        args += [
            f":{xvnc_display}",
        ]

        print("xvnc server args:", shlex.join(args))
        proc = subprocess.Popen(args)
        time.sleep(5) # TODO dynamic
        # TODO check if the process is running
        self.xvnc_process = proc
        self.xvnc_display = xvnc_display
        self.xvnc_port = 5900 + xvnc_display
        self.xvnc_env["DISPLAY"] = f":{self.xvnc_display}"

        # not working. instead, use "picom"
        # TODO install xcalib on github CI
        # invert colors: xcalib -i -a
        # https://github.com/zoltanp/xrandr-invert-colors#alternatives
        #self.subprocess_getoutput(["xcalib", "-i", "-a"])

    async def start_window_manager(self):
        # https://en.wikipedia.org/wiki/Comparison_of_X_window_managers
        # https://wiki.archlinux.org/title/Window_manager#List_of_window_managers
        # https://wiki.archlinux.org/title/List_of_applications/Other#Taskbars
        args = None
        local_remove_files = []
        # nice, looks like a "normal" desktop, similar to xfce, pseudo-tiling
        if self.window_manager_name == "icewm": # dynamic window manager
            # https://ice-wm.org/man/icewm-preferences.html
            icewm_preferences_list = [
                'TaskBarShowCPUStatus=0',
                'CPUStatusShowRamUsage=0',
                'CPUStatusShowSwapUsage=0',
                'CPUStatusShowAcpiTemp=0',
                'CPUStatusShowCpuFreq=0',
                'TaskBarShowMEMStatus=0',
                'TaskBarShowNetStatus=0',
                'TaskBarShowAPMStatus=0',
                'TaskBarShowAPMAuto=0',
                'TaskBarShowAPMGraph=0',
                'TaskBarShowAPMTime=0',
                'TaskBarShowMailboxStatus=0',
                'TimeFormat="%F %T"',
                'WorkspaceNames="1","2","3","4"',
                'ColorClock = "rgb:C0/C0/C0"',
                'ColorClockText="rgb:00/00/00"',
            ]
            icewm_preferences_path = tempfile.mktemp(suffix="-icewm-preferences.txt")
            with open(icewm_preferences_path, "w") as f:
                f.write("\n".join(icewm_preferences_list) + "\n")
            # the preferences file is needed only to start icewm
            local_remove_files.append(icewm_preferences_path)
            args = [
                "icewm",
                f"--config={icewm_preferences_path}",
                #f"--theme=FILE",
            ]
        # lightweight compositor, not a window manager
        # needed to invert colors on the xvnc server
        elif self.window_manager_name == "picom":
            args = [
                "picom",
            ]
            if self.xvnc_invert_colors:
                args += [
                    # FIXME this fails with "only copy the PATH env"
                    # https://askubuntu.com/questions/134668/how-to-trigger-a-color-inversion-effect-for-one-window
                    #"--invert-color-include", 'class_g="Chromium-browser"',
                    # invert colors of all windows
                    # also "save file" dialogs
                    "--invert-color-include", 'name ~= "."',
                ]
        # menu on desktop, but too much by default, no tiling?
        elif self.window_manager_name == "fvwm": # dynamic window manager
            args = [
                "fvwm",
                #"--config=FILE",
            ]
        # taskbar, menu on desktop, no tiling
        elif self.window_manager_name == "fluxbox": # stacking window manager
            args = [
                "fluxbox",
                "-rc", "rcfile",
            ]
        # okay... menu shows only some apps, no tiling
        elif self.window_manager_name == "jwm": # stacking window manager
            args = [
                "jwm",
            ]
        # ugly by default, no tiling, no taskbar, no menu, hard to kill
        elif self.window_manager_name == "sawfish": # stacking window manager
            args = [
                "sawfish",
            ]
        # no mouse menu
        elif self.window_manager_name == "i3": # dynamic window manager
            args = [
                "i3",
                #"-c", "configfile",
            ]
        # no mouse menu
        elif self.window_manager_name == "openbox": # stacking window manager
            raise NotImplementedError
        # no mouse menu
        elif self.window_manager_name == "spectrwm": # dynamic window manager
            raise NotImplementedError
        # no mouse menu
        elif self.window_manager_name == "qtile": # dynamic window manager
            raise NotImplementedError
        # no mouse menu
        elif self.window_manager_name == "dwm": # dynamic window manager
            raise NotImplementedError
        else:
            raise ValueError(f"unknown window manager: {repr(self.window_manager_name)}")
        print("window manager args:", shlex.join(args))
        proc = subprocess.Popen(
            args,
            env=self.xvnc_env,
        )
        time.sleep(5) # TODO dynamic
        # TODO check if the process is running
        self.window_manager_process = proc
        for temp_path in local_remove_files:
            try:
                shutil.rmtree(temp_path)
            except NotADirectoryError:
                os.unlink(temp_path)
            except FileNotFoundError:
                pass

    async def try_connect_vnc_client(self):
        """
        try to connect to a vnc client
        """
        if self.connected_vnc_client:
            return True
        if len(self.vnc_client_list) == 0:
            return False
        # VNCClient(user, host, ssh_port, vnc_port)
        vnc_client_id_list = list(range(len(self.vnc_client_list)))
        random.shuffle(vnc_client_id_list)
        for vnc_client_id in vnc_client_id_list:
            vnc_client = self.vnc_client_list[vnc_client_id]
            ssh_server = f"{vnc_client.user}@{vnc_client.host}:{vnc_client.port}"
            ssh_r_arg = f"{vnc_client.vnc_port}:localhost:{self.xvnc_port}"
            # ssh -R 1234:localhost:5901 example.com
            # ssh_server is secret, dont print it
            print(f"trying to connect to VNC client {vnc_client_id}")
            # TODO quiet, only print fatal errors
            args = [
                "ssh",
                "-R", ssh_r_arg,
            ]
            if self.ssh_id_file_path:
                args += [
                    "-i", self.ssh_id_file_path,
                ]
            args += [
                ssh_server,
            ]
            print("ssh client args:", shlex.join(args))
            proc = subprocess.Popen(args)
            time.sleep(5) # TODO dynamic
            raise NotImplementedError("TODO check ssh connection")
            # TODO wait 5 seconds for connection
            # if connection is working, set self.ssh_process and "return True"
            # else continue and try next vnc client
            #self.ssh_process = proc
            return True

    # TODO skip ssh, use "reverse vnc"
    # https://tigervnc.org/doc/vncviewer.html
    # vncviewer −listen 5500
    # Causes vncviewer to listen on the given port (default 5500) for reverse connections from a VNC server
    # https://help.ubuntu.com/community/VNC/Reverse
    # x11vnc -quiet -safer -rfbport 0 -xkb -connect_or_exit mymachine.dyndns.org:5505 -display :0

    async def do_start_vnc_client(self):
        # vncviewer is provided by the tigervnc package
        # level is between 0 and 100, 100 meaning most verbose output.
        # TODO invert colors for darkmode
        # http://ssb22.user.srcf.net/setup/vnc-invert.html
        log_level = 0
        args = [
            "vncviewer",
            "-Log", f"*:stderr:{log_level}",
            # disable automatic selection of encoding and pixel format
            # force vncviewer to use reduced color level
            #"-AutoSelect=0",
            # Selects the reduced color level to use on slow links
            # 0 meaning 8 colors, 1 meaning 64 colors (the default), 2 meaning 256 colors
            #"-LowColourLevel", "0",
            #"-PreferredEncoding", "tight",
            f"::{self.xvnc_port}",
        ]
        print("vnc client args:", shlex.join(args))
        self.vnc_client_process = subprocess.Popen(args)
        time.sleep(5) # TODO dynamic

    class Response():
        status = 0
        content_type = None
        content = None
        headers = None
        #_text = None
        def __init__(self, status, headers, content_type, encoding, content, har, har_path):
            self.status = status
            self.headers = headers
            self.content_type = content_type
            #self._text = text
            self.encoding = encoding
            self.content = content
            self.har = har
            self.har_path = har_path
        async def text(self):
            # await response.text()
            return self.content.decode(self.encoding)

    class Headers():
        def __init__(self, headers):
            # headers from the HAR file is list of objects:
            # [ { "name": "x", "value": "y" } ]
            # transform it to a list of tuples, to save memory
            # note: all header names in HAR files are lowercase
            self.headers = list(map(lambda h: (h["name"], h["value"]), headers))
        def get(self, key):
            # return the first matching header
            # TODO better? how to handle duplicate keys in self.headers
            try:
                return next(h for h in self.headers if h[0] == key.lower())[1]
            except StopIteration: # not found
                raise KeyError

    def __init__(
            self,
            start_vnc_client=False,
            vnc_client_list=[],
            ssh_id_file_path=None,
        ):

        """
        initialize the scraper

        open a new tab, the "scraper tab"
        open chromium in the scraper tab
        (todo: get positions of buttons and icons)
        """

        self.start_vnc_client = start_vnc_client
        self.set_vnc_client_list(vnc_client_list)
        self.ssh_id_file_path = ssh_id_file_path

        if False:
            # copy all envs
            self.xvnc_env = dict(os.environ)
        else:
            # only copy the PATH env, to make env consistent
            self.temp_home = tempfile.mkdtemp(suffix="-fetch-subs-home")
            if False:
                global_remove_files_when_done.append(self.temp_home)
            else:
                # debug: keep home
                logger_print("keeping tempfiles after exti: temp home:", self.temp_home)
                # delete some cache files we dont need
                global_remove_files_when_done.append(self.temp_home + "/.cache")
                global_remove_files_when_done.append(self.temp_home + "/.config")
                global_remove_files_when_done.append(self.temp_home + "/.local")
                global_remove_files_when_done.append(self.temp_home + "/.pki")

            self.xvnc_env = {
                "PATH": os.environ["PATH"],
                # fix "invert-color-include" of picom
                "HOME": self.temp_home,
            }
            if False:
                # debug: copy some random envs
                all_envs = os.environ
                if True:
                    # use a reduced dict of envs which is known to work
                    # to further reduce the dict of envs
                    with open("env.json.lightmode-inverted.5", "r") as f:
                        all_envs = json.load(f)
                if False:
                    # add some envs
                    for key in random.sample(all_envs.keys(), int(len(all_envs.keys()) / 2)):
                        self.xvnc_env[key] = all_envs[key]
                    print("debug: writing /tmp/env.json")
                    with open("/tmp/env.json", "w") as f:
                        json.dump(self.xvnc_env, f, indent=2)
                else:
                    # add all envs
                    for key in all_envs.keys():
                        self.xvnc_env[key] = all_envs[key]

        # async init is done in async def async_init(self)
        # to create a class instance, simply do
        # chromium_headful_scraper = ChromiumHeadfulScraper()
        pass

    def __await__(self):

        return self.async_init().__await__()

    # TODO use this as a "status bar" widget
    #def set_address_bar_text(text):
    #    TODO

    async def async_init(self):

        # async init function. note: this must "return self"
        # https://stackoverflow.com/questions/33128325/how-to-set-class-attribute-with-await-in-init

        #from XDoToolWrapper import XDoToolWrapper
        #xdotool = XDoToolWrapper()
        #xdotool.get_monitors()

        def search_chromium_window_id():
            window_id_list = []
            desktop_id_list = []
            for window_id in self.xdotool("search", "--classname", "Chromium").strip().split("\n"):
                if window_id == "":
                    # this should be prevented by strip()
                    continue
                desktop_id = self.xdotool("get_desktop_for_window", window_id).strip()
                if desktop_id.endswith("-1"): # invalid window_id
                    continue
                logger_print(f"found chromium window {window_id} on desktop {desktop_id}")
                window_id_list.append(int(window_id))
                desktop_id_list.append(int(desktop_id))
            if len(window_id_list) > 0:
                idx = 0 # use the first window
                window_id = window_id_list[idx]
                desktop_id = desktop_id_list[idx]
                logger_print(f"using chromium window {window_id} on desktop {desktop_id}")
                return window_id
            return None # not found

        logger_print("starting Xvnc server")
        await self.start_xvnc_server()
        logger_print("starting Xvnc server done (TODO verify)")

        # TODO init xsession
        # see also: man i3
        """
        # Disable DPMS turning off the screen
        xset -dpms
        xset s off

        # Disable bell
        xset -b

        # Enable zapping (C-A-<Bksp> kills X)
        setxkbmap -option terminate:ctrl_alt_bksp

        # Enforce correct locales from the beginning:
        # LC_ALL is unset since it overwrites everything
        # LANG=de_DE.UTF-8 is used, except for:
        # LC_MESSAGES=C never translates program output
        # LC_TIME=en_DK leads to yyyy-mm-dd hh:mm date/time output
        unset LC_ALL
        export LANG=de_DE.UTF-8
        export LC_MESSAGES=C
        export LC_TIME=en_DK.UTF-8

        # Use XToolkit in java applications
        export AWT_TOOLKIT=XToolkit

        # Set background color
        xsetroot -solid "#333333"

        # Enable core dumps in case something goes wrong
        ulimit -c unlimited
        """

        # Set desktop background color to white
        # to make it consistent with the lightmode theme
        if False:
            logger_print("setting desktop background color")
            self.subprocess_getoutput(["xsetroot", "-solid", "#ffffff"])

        logger_print("starting window manager")
        await self.start_window_manager()
        logger_print("starting window manager done (TODO verify)")

        if self.start_vnc_client:
            logger_print("starting vnc client")
            await self.do_start_vnc_client()
            logger_print("starting vnc client done (TODO verify)")
        else:
            logger_print("trying to connect to a VNC client")
            await self.try_connect_vnc_client()
            # TODO print status. are we connected to a VNC client?
            logger_print("trying to connect to a VNC client done (TODO verify)")

        self.chromium_user_data_dir = tempfile.mkdtemp(suffix="-fetch-subs-chromium-user-data")
        #if False: # debug: keep tempdir
        if True:
            global_remove_files_when_done.append(self.chromium_user_data_dir)
        else:
            # debug: keep chromium user-data-dir
            logger_print("keeping tempfiles after exit: chromium user-data-dir:", self.chromium_user_data_dir)

        self.downloads_path = self.temp_home + "/Downloads"

        # set some config here
        # so later, we need less clicks and commands
        self.chromium_config = {
            "devtools": {
                "preferences": {
                    # devtools: default position is "dock to right"
                    # change position to "dock to bottom"
                    "currentDockState": '"bottom"',
                    # disable async debugger in devtools sources tab
                    "disableAsyncStackTraces": "true",
                    # disable network cache while devtools is open
                    "cacheDisabled": "true",
                },
            },
            "download": {
                # ask where to save each file before downloading
                "prompt_for_download": False,
            },
            "download_bubble": {
                # Show downloads when they're done
                "partial_view_enabled": False,
            },
            "selectfile": {
                # default download location
                "last_directory": self.downloads_path,
            },
        }

        # write chromium config file
        self.chromium_config_path = self.chromium_user_data_dir + "/Default/Preferences"
        logger_print(f"writing chromium config file:", self.chromium_config_path)
        os.makedirs(self.chromium_user_data_dir + "/Default")
        with open(self.chromium_config_path, "w") as f:
            json.dump(self.chromium_config, f, indent=2)

        self.notify_send_message("searching for an existing chromium window")
        # FIXME this is blocking with picom
        self.chromium_window_id = search_chromium_window_id()

        if self.chromium_window_id != None:
            # this should never happen...
            # we have just started a fresh Xvnc server
            # so there should be no apps running inside it
            raise Exception(f"FIXME chromium is already running on display {self.xvnc_display} with window id {self.chromium_window_id}")

        #self.chromium_window_id = None # test

        #if self.chromium_window_id == None:
        #    logger_print(f"no existing chromium window was found. creating a new chromium window")

        self.notify_send_message("creating a new chromium window")

        self.scraper_tab_html = (
            "<html>\n"
            "<head>\n"
            "<title>scraper tab</title>\n"
            "<style>\n"
            # darkreader fails on data urls, so we enable darkmode here
            #"@media (prefers-color-scheme: dark) {\n"
            #"body { background: black; color: white; }\n"
            #"}\n"
            "</style>\n"
            "</head>\n"
            "<body>\n"
            "<h1>scraper tab</h1>\n"
            "<p>this is an empty tab for web scraping</p>\n"
            "<p>please do nothing here while the scraper is running</p>\n"
            "<p>close this tab when the scraper is done</p>\n"
            "</body>\n"
            "</html>\n"
        )

        # create a new chromium window
        # https://developer.mozilla.org/en-US/docs/web/http/basics_of_http/data_urls
        url = "data:text/html;charset=utf-8," + urllib.parse.quote(self.scraper_tab_html)
        args = ["chromium", f"--user-data-dir={self.chromium_user_data_dir}", url]
        # note: when we call chromium for the first time
        # it will create the main process
        # further calls to chromium will create a new tab in the existing window
        # and the process ends immediately
        # TODO keep the logfile small
        chromium_logfile_handle = subprocess.DEVNULL
        # TODO enable for debug
        if False:
            chromium_logfile_path = tempfile.mktemp(suffix="-chromium-logfile.txt")
            chromium_logfile_handle = open(chromium_logfile_path, "w")
            global_remove_files_when_done.append(chromium_logfile_path)
            logger_print(f"writing chromium logfile: {chromium_logfile_path}")
        self.chromium_process = subprocess.Popen(
            args,
            stdout=chromium_logfile_handle,
            stderr=subprocess.STDOUT, # merge with stdout
            #check=True,
            env=self.xvnc_env,
        )
        time.sleep(5) # TODO dynamic
        logger_print("creating a new chromium window: waiting done")

        # TODO xprop | grep WM_CLASS
        # WM_CLASS(STRING) = "chromium-browser (/run/user/1000/tmp3er0bm23)", "Chromium-browser"
        if False:
            logger_print("TODO click on the chromium window")
            xprop_output = self.subprocess_getoutput(["xprop"])
            logger_print("xprop_output:", xprop_output)

        # TODO maximize the chromium window
        logger_print("TODO maximize the chromium window")

        if self.chromium_window_id == None:
            # search for the created chromium window
            logger_print("searching for the created chromium window")
            self.chromium_window_id = search_chromium_window_id()

        if self.chromium_window_id == None:
            raise Exception("failed to create a new chromium window")

        logger_print("chromium_window_id", self.chromium_window_id)

        logger_print("chromium_window_geometry", repr(self.xdotool("getwindowgeometry", self.chromium_window_id).strip()))
        # Window 52428803
        #   Position: 0,0 (screen: 0)
        #   Geometry: 1920x1040
        # -> already maximized
        chromium_window_size = tuple(map(int, self.xdotool("getwindowgeometry", self.chromium_window_id).strip().split("\n")[-1].split(" ")[3].split("x")))

        logger_print("focussing the chromium window")
        # TODO is "windowfocus" enough?
        #xdotool(f"windowfocus --sync {self.chromium_window_id}")
        if self.is_multi_window:
            self.xdotool("windowactivate", "--sync", self.chromium_window_id)
        time.sleep(3) # TODO dynamic

        #maximized_window_size = (1920, 1040) # kde plasma desktop
        #maximized_window_size = (1024, 768)
        maximized_window_size = (1024, 740) # Xvnc + picom # TODO height

        if chromium_window_size != maximized_window_size:
            logger_print("maximizing the chromium window")
            # https://askubuntu.com/questions/703628/how-to-close-minimize-and-maximize-a-specified-window-from-terminal
            #xdotool("windowsize", self.chromium_window_id, "100%", "100%") # not working
            self.wmctrl("-ir", self.chromium_window_id, "-b", "add,maximized_vert,maximized_horz")
            time.sleep(3) # TODO dynamic

        # TODO use this to update maximized_window_size
        logger_print("chromium_window_geometry", repr(self.xdotool("getwindowgeometry", self.chromium_window_id).strip()))

        logger_print("opening chromium devtools")
        if self.is_multi_window:
            self.xdotool("windowactivate", "--sync", self.chromium_window_id)
        self.xdotool("key", "Control+I")
        # this can take some seconds, better wait longer
        time.sleep(6) # TODO dynamic

        # calibration should not be needed
        # as long as the Xvnc display resolution stays at 1024x768
        self.calibrate_positions = False

        def verbose_sleep(wait_seconds):
            logger_print(f"verbose sleep: waiting {wait_seconds} seconds")
            for loop_idx in range(wait_seconds + 1):
                time_left = wait_seconds - loop_idx
                logger_print(f"verbose sleep: {time_left} seconds left")
                time.sleep(1)

        logger_print("opening chromium devtools command shell for the first time")
        # open the command shell for the first time
        # so later, it opens faster in chromium_command
        self.xdotool("key", "Control+P")
        time.sleep(1)
        # close the command shell
        self.xdotool("key", "Escape")
        time.sleep(0.5)

        if False:
            # done in chromium_config currentDockState
            # devtools: default position is "dock to right"
            # change position to "dock to bottom"
            self.chromium_command("Dock to bottom")
            time.sleep(3) # TODO dynamic

        # TODO automatically find the positions from a screenshot
        self.chromium_devtools_top_y = 460

        if self.calibrate_positions:
            self.chromium_devtools_top_y = self.calibrate_pos("chromium_devtools_top_y")

        # TODO automatically find the positions from a screenshot
        self.chromium_devtools_network_tab_pos = (325, 475)

        if self.calibrate_positions:
            self.chromium_devtools_network_tab_pos = self.calibrate_pos("chromium_devtools_network_tab_pos")

        # disable the javascript debugger
        # avoid "debugger paused" blocking the page
        self.chromium_command("Deactivate breakpoints")
        self.chromium_command("Disable JavaScript")
        # done in chromium_config disableAsyncStackTraces
        #self.chromium_command("Do not capture async stack traces")

        logger_print("opening network tab of chromium devtools")
        self.xdotool("mousemove", *self.chromium_devtools_network_tab_pos)
        self.xdotool("click", "1") # left click
        time.sleep(3) # TODO dynamic

        # TODO automatically find the positions from a screenshot
        self.chromium_devtools_toolbar_y = 500

        if self.calibrate_positions:
            self.chromium_devtools_toolbar_y = self.calibrate_pos("chromium_devtools_toolbar_y")

        # TODO automatically find the positions from a screenshot
        self.chromium_devtools_network_tab_start_stop_log_pos = (30, self.chromium_devtools_toolbar_y)

        if self.calibrate_positions:
            self.chromium_devtools_network_tab_start_stop_log_pos = self.calibrate_pos("chromium_devtools_network_tab_start_stop_log_pos")

        # these positions are calibrated to a 1024x768 Xvnc desktop
        # running picom and chromium
        # on the display-bottom, there is a black bar
        # under the chromium window. TODO remove?
        # TODO automatically find the positions from a screenshot
        # manually find position:
        # while true; do xdotool getmouselocation; sleep 0.5; done
        address_bar_pos_y = 65
        self.chromium_address_bar_pos = (480, address_bar_pos_y)
        self.chromium_reload_page_pos = (95, address_bar_pos_y)

        self.chromium_devtools_network_tab_export_har_pos = (530, self.chromium_devtools_toolbar_y)
        self.chromium_devtools_network_tab_clear_log_pos = (55, self.chromium_devtools_toolbar_y)

        self.chromium_saving_har_file_pos = (965, self.chromium_devtools_toolbar_y)

        self.chromium_show_notifications_popup_block_button_pos = (320, 190)

        if self.calibrate_positions:
            self.chromium_address_bar_pos = self.calibrate_pos("chromium_address_bar_pos")
            self.chromium_reload_page_pos = self.calibrate_pos("chromium_reload_page_pos")
            self.chromium_devtools_network_tab_export_har_pos = self.calibrate_pos("chromium_devtools_network_tab_export_har_pos")
            self.chromium_devtools_network_tab_clear_log_pos = self.calibrate_pos("chromium_devtools_network_tab_clear_log_pos")
            self.chromium_saving_har_file_pos = self.calibrate_pos("chromium_saving_har_file_pos")

        self.chromium_command("Stop recording network log")
        self.chromium_command("Clear network log")

        return self

    def calibrate_pos(self, name):
        logger_print(f"calibrate_pos {name}: move your mouse to this position for the next 5 seconds")
        wait_seconds = 8
        for loop_idx in range(wait_seconds + 1):
            time_left = wait_seconds - loop_idx
            # x:534 y:793 screen:0 window:1035
            pos = tuple(map(lambda s: int(s.split(":")[1]), self.xdotool("getmouselocation").strip().split(" ")[0:2]))
            if time_left > 0:
                logger_print(f"calibrate_pos {name}: position {pos} - {time_left} seconds left to move your mouse")
                time.sleep(1)
            else:
                logger_print(f"calibrate_pos {name}: position {pos} - done")
                return pos

    def chromium_command(self, command_str):
        # funny: missing command: "Export HAR file"
        # so we still need to click the "export HAR" icon
        # debug
        #logger_print("chromium command:", command_str)
        self.clipboard_set_text(command_str)
        # TODO activate the chromium window if window manager != "picom"
        # open the command shell of devtools
        # note: when devtools is closed, this will open a "print" dialog
        # TODO detect this case from screenshot
        self.xdotool("key", "Control+P")
        time.sleep(0.2)
        # paste the command and hit enter
        # note: we must wait between "Control+v" and "return"
        # otherwise chromium will ignore the command
        #self.xdotool("key", "Control+v", "return")
        self.xdotool("key", "Control+v")
        time.sleep(0.2)
        self.xdotool("key", "return")
        # wait for the command to finish
        time.sleep(0.5)

    async def get_response(
            self,
            url,
            return_har=False,
            return_har_path=False,
            keep_page_open=False,
        ):

        self.request_number += 1

        # create a local copy
        request_number = self.request_number

        """
        send request and get response

        focus the chromium window
        (todo: stop loading the previous request)
        clear the network log
        load the url
        take screenshots of the reload/stop icon
        wait until the page is loaded
        export the network traffic as HAR file
        parse the HAR file to extract response_status and response_text

        TODO handle file downloads saved to ~/Downloads/
        also parse the HAR file? seems a waste of memory, at least on success
        on error, we also want response_status and response_headers
        """

        # global: get_screenshot
        # global: sha1sum
        # global: datetime_str
        # global: random_hash
        # global: tempdir
        # global: logger
        # global: xdotool
        # global: logger_print

        # TODO implement POST requests. probably via the javascript console

        # TODO make this return a "response" object?
        # similar to other http client libraries: requests, aiohttp, ...

        logger_print(f"req{request_number}: focussing the chromium window")
        if self.is_multi_window:
            self.xdotool("windowactivate", "--sync", self.chromium_window_id)
        self.notify_send_message(f"opening url: {url}", t=10)

        # TODO stop previous request if it is still loading. check screenshot of self.chromium_reload_page_pos

        self.chromium_command("Clear network log")
        self.chromium_command("Record network log")

        # open the url
        if False:
            # no. this creates a new tab
            # but we want to re-use one tab with chromium devtools
            args = ["chromium", f"--user-data-dir={self.chromium_user_data_dir}", url]
            subprocess.run(
                args,
                capture_output=True,
                check=True,
            )

        self.clipboard_set_text(url)
        if self.is_multi_window:
            self.xdotool("windowactivate", "--sync", self.chromium_window_id)
        # focus the address bar
        # control+l is not enough. when devtools/network is open
        # this would focus the network log filter input element
        self.xdotool("mousemove", *self.chromium_address_bar_pos)
        self.xdotool("click", "1") # left click
        # paste the url
        self.xdotool("key", "Control+l", "Control+v", "return")
        # TODO copy-paste via clipboard?
        # TODO escape url or better: use subprocess.run(["xdotool", "type", "..."])
        #await asyncio.sleep(sleep_seconds) # TODO dynamic

        # bbox: x, y, width, height
        self.chromium_address_bar_icon_bbox = (120, 50, 32, 30)
        self.chromium_show_notifications_popup_block_allow_bbox = (280, 172, 144, 37)

        # wait for page load
        logger_print(f"req{request_number}: waiting for page load ...")
        # TODO handle timeout
        # debug
        logger_print(f"req{request_number}: expected screenshot hashes:")
        for screenshot_hash in self.screenshot_hashes["done_loading"]:
            logger_print(f"  {screenshot_hash.hex()}")
        time.sleep(1)

        for i in range(30):

            delete_screenshot_files = True
            #delete_screenshot_files = False # debug: keep screenshot files

            # check for popup: "show notifications? block | allow"
            screenshot_path = self.get_screenshot(bbox=self.chromium_address_bar_icon_bbox, name="chromium_address_bar_icon")
            screenshot_hash = sha1sum(screenshot_path)
            logger_print(f"req{request_number}: chromium_address_bar_icon: screenshot_hash", screenshot_hash.hex())
            if delete_screenshot_files:
                os.unlink(screenshot_path)
            else:
                logger_print(f"req{request_number}: chromium_address_bar_icon: screenshot_path", screenshot_path)

            if screenshot_hash in self.screenshot_hashes["chromium_address_bar_icon_has_popup"]:
                # has popup
                screenshot_path = self.get_screenshot(bbox=self.chromium_show_notifications_popup_block_allow_bbox, name="chromium_show_notifications_popup_block_allow")
                screenshot_hash = sha1sum(screenshot_path)
                logger_print(f"req{request_number}: chromium_show_notifications_popup_block_allow: screenshot_hash", screenshot_hash.hex())
                if delete_screenshot_files:
                    os.unlink(screenshot_path)
                else:
                    logger_print(f"req{request_number}: chromium_show_notifications_popup_block_allow: screenshot_path", screenshot_path)
                if screenshot_hash in self.screenshot_hashes["show_notifications_popup_block_allow"]:
                    # has "show notifications" popup
                    # click the "block" button

                    if self.calibrate_positions:
                        self.chromium_show_notifications_popup_block_button_pos = self.calibrate_pos("chromium_show_notifications_popup_block_button_pos")

                    logger_print(f"req{request_number}: clicking the block button")
                    self.xdotool("mousemove", *self.chromium_show_notifications_popup_block_button_pos)
                    self.xdotool("click", "1") # left click
                    time.sleep(1) # TODO dynamic

            screenshot_path = self.get_screenshot(center_pos=self.chromium_reload_page_pos, name="chromium_reload_page")
            screenshot_hash = sha1sum(screenshot_path)
            logger_print(f"req{request_number}: chromium_reload_page: screenshot_hash", screenshot_hash.hex())
            if delete_screenshot_files:
                os.unlink(screenshot_path)
            else:
                logger_print(f"req{request_number}: chromium_reload_page: screenshot_path", screenshot_path)

            if True:
                # debug: write full screen shot
                # useful for manually calibrating positions
                full_screenshot_path = self.get_full_screenshot()
                logger_print(f"req{request_number}: debug: full screenshot:", full_screenshot_path)

            if screenshot_hash in self.screenshot_hashes["done_loading"]:
                break
                #pass # debug: keep looping to get screenshots

            time.sleep(1)

        logger_print(f"req{request_number}: waiting for page load done")

        # save output file
        if False:
            # save html file
            # use a random path to avoid the "file exists" dialog
            html_file_path = f"{tempdir}/fetch-subs-{datetime_str()}-{random_hash()}.html"
            self.notify_send_message(f"req{request_number}: saving html to {html_file_path}")
            self.clipboard_set_text(html_file_path)
            if self.is_multi_window:
                self.xdotool("windowactivate", "--sync", self.chromium_window_id)
            self.xdotool("key", "Control+s")
            time.sleep(5) # TODO dynamic
            self.xdotool("key", "Control+a", "Control+v", "return")

        # TODO click "block notifications" on the first time we visit opensubtiles.org

        # save har file
        # note: file extension must be ".har" otherwise chromium will add ".har"
        har_file_path = f"{tempdir}/fetch-subs-{datetime_str()}-{random_hash()}.har"
        logger_print(f"req{request_number}: exporting har file to {har_file_path}")
        self.clipboard_set_text(har_file_path)
        if self.is_multi_window:
            self.xdotool("windowactivate", "--sync", self.chromium_window_id)

        logger_print(f"req{request_number}: opening network tab of chromium devtools")
        self.xdotool("mousemove", *self.chromium_devtools_network_tab_pos)
        self.xdotool("click", "1") # left click
        ##await asyncio.sleep(2) # TODO dynamic
        time.sleep(1) # TODO dynamic

        # FIXME why is this printed twice
        # blame asyncio.sleep?
        logger_print(f'req{request_number}: clicking the "export har" icon')
        # FIXME this position is wrong
        #self.chromium_devtools_network_tab_export_har_pos = self.calibrate_pos("self.chromium_devtools_network_tab_export_har_pos")
        self.xdotool("mousemove", *self.chromium_devtools_network_tab_export_har_pos)
        self.xdotool("click", "1") # left click
        #await asyncio.sleep(5) # TODO dynamic
        time.sleep(5) # TODO dynamic
        self.xdotool("key", "Control+a", "Control+v", "return")
        # wait for the har file
        if False:
            # old code
            # chromium needs some time before it starts saving the har file
            #await asyncio.sleep(5)
            time.sleep(5)
            # TODO handle timeout
            # debug
            logger_print(f"req{request_number}: expected screenshot hashes:")
            for screenshot_hash in self.screenshot_hashes["done_saving_har_file"]:
                logger_print(f"  {screenshot_hash.hex()}")
            #await asyncio.sleep(1)
            time.sleep(1)
            for i in range(30):
                screenshot_path = self.get_screenshot(center_pos=self.chromium_saving_har_file_pos, name="chromium_saving_har_file")
                screenshot_hash = sha1sum(screenshot_path)
                logger_print(f"req{request_number}: screenshot_hash", screenshot_hash.hex())
                os.unlink(screenshot_path)
                if screenshot_hash in self.screenshot_hashes["done_saving_har_file"]:
                    logger_print(f"req{request_number}: done saving the har file")
                    break
                #await asyncio.sleep(1)
                time.sleep(1)
        # wait for chromium to start writing the har file
        while True:
            if os.path.exists(har_file_path):
                break
            #await asyncio.sleep(1)
            time.sleep(1)
        # wait for chromium to finish writing the har file
        previous_size = 0
        har = None
        # TODO check screenshots? "saving HAR file icon" in devtools
        while True:
            #await asyncio.sleep(1)
            time.sleep(1)
            size = os.path.getsize(har_file_path)
            logger_print(f"req{request_number}: har file size:", size)
            if size != previous_size:
                previous_size = size
                continue
            # constant size is not enough. also try to parse it
            with open(har_file_path, "r") as har_file:
                try:
                    har = json.load(har_file)
                    break
                except json.decoder.JSONDecodeError:
                    logger_print(f"req{request_number}: failed to parse json in har file:", har_file_path)
                    continue
        # parse the HAR file
        # see also chrome-example-har-file.json
        # see also docs/example-empty-har-file.json
        # FIXME every second har file is empty = has 155 bytes
        # 5 of 10 requests return an empty har file
        # maybe we need more time.sleep?
        # or less "clear network log" commands?
        response_har = None
        response_har_path = None
        if return_har_path:
            response_har_path = har_file_path
        #with open(har_file_path, "r") as har_file:
        #    har = json.load(har_file)
        if return_har:
            response_har = har
        if not "log" in har:
            raise NotImplementedError(f"failed to parse har file: {har_file_path}")
        if not "entries" in har["log"] or len(har["log"]["entries"]) == 0:
            raise NotImplementedError(f"no entries in har file: {har_file_path}")
            #raise NotImplementedError(f"not found response in har file: {har_file_path}")
        har_entry = har["log"]["entries"][0]
        if har_entry["request"]["url"] != url:
            logger_print(f"req{request_number}: url =", repr(url))
            logger_print(f"req{request_number}: har_entry request url =", repr(har_entry["request"]["url"]))
            logger_print(f"req{request_number}: har_entry request queryString =", repr(har_entry["request"]["queryString"]))
            raise NotImplementedError(f"unexpected url in har file: {har_file_path}")
        # validate
        if not "response" in har_entry:
            raise NotImplementedError(f"missing response in har file: {har_file_path}")
        if not "content" in har_entry["response"]:
            raise NotImplementedError(f"missing response content in har file: {har_file_path}")
        if not "text" in har_entry["response"]["content"]:
            # TODO when the response is binary only
            # then the response content is written only to disk
            # and is not stored in the HAR file
            # TODO for binary response
            # add a file handle response.content to the downloaded file
            # the file name should be in response_headers.get("Content-Disposition")
            # example content_disposition: 'attachment; filename="some-file.zip"'
            raise NotImplementedError(f"missing response text in har file: {har_file_path}")
        # finally: set status and response_text
        response_status = har_entry["response"]["status"]
        response_type = har_entry["response"]["content"]["mimeType"]
        response_headers = har_entry["response"]["headers"]
        # TODO handle binary response
        #response_text = har_entry["response"]["content"]["text"]
        response_encoding = "utf8" # TODO
        response_content = har_entry["response"]["content"]["text"].encode(response_encoding)
        # validate
        # note: size is the byte size == len(response_text.encode("utf8"))
        # not the number of characters == len(response_text)
        #if har_entry["response"]["content"]["size"] != len(response_text.encode(response_encoding)):
        if har_entry["response"]["content"]["size"] != len(response_content):
            #logger_print(f"req{request_number}: len(response_text) =", len(response_text.encode("utf8")))
            logger_print(f"req{request_number}: len(response_content) =", len(response_content))
            logger_print(f"req{request_number}: har_entry request content size =", repr(har_entry["response"]["content"]["size"]))
            raise NotImplementedError(f"unexpected response text size in har file: {har_file_path}")

        # delete har file
        # TODO allow to keep the har file for debugging
        if return_har_path == False:
            os.unlink(har_file_path)

        #raise NotImplementedError

        #await asyncio.sleep(5) # TODO dynamic

        self.chromium_command("Stop recording network log")
        self.chromium_command("Clear network log")

        # done. close the page
        if keep_page_open == False:
            url = "data:text/html;charset=utf-8," + urllib.parse.quote(self.scraper_tab_html)
            self.clipboard_set_text(url)
            if self.is_multi_window:
                self.xdotool("windowactivate", "--sync", self.chromium_window_id)
            self.xdotool("mousemove", *self.chromium_address_bar_pos)
            self.xdotool("click", "1") # left click
            # paste the url with control+v
            self.xdotool("key", "Control+l", "Control+v", "return")

        response = self.Response(
            response_status,
            self.Headers(response_headers),
            response_type,
            response_encoding,
            #response_text,
            response_content,
            response_har,
            response_har_path,
        )

        return response

    def subprocess_getoutput(self, args, kwargs={}):
        debug = False
        args = list(map(str, args))
        if debug:
            logger_print("cmd:", shlex.join(args))
        proc = subprocess.run(
            args,
            capture_output=True,
            encoding="utf8",
            env=self.xvnc_env,
            **kwargs,
        )
        output = proc.stdout
        if debug:
            logger_print("cmd:", shlex.join(args), "-> output:", output)
        return output

    def xdotool(self, *args):
        return self.subprocess_getoutput(["xdotool"] + list(args))

    def wmctrl(self, *args):
        return self.subprocess_getoutput(["wmctrl"] + list(args))

    def notify_send(self, *args):
        return self.subprocess_getoutput(["notify-send"] + list(args))

    def notify_send_message(self, notify_message, t=5):
        logger_print(notify_message)
        # FIXME notify-send is not working with icewm
        #if self.window_manager_name == "icewm":
        if True:
            return
        return self.notify_send("-t", f"{t}000", "-u", "normal", "-e", "fetch-subs.py", notify_message)

    def clipboard_set_text(self, text):
        logger_print("clipboard_set_text:", repr(text))
        subprocess.run(
            ["xclip", "-i", "-sel", "c"],
            input=text,
            encoding="utf8",
            env=self.xvnc_env,
        )
        #await asyncio.sleep(1) # TODO remove? or more?

    def crop_of_center_pos(self, center_pos, delta=15):
        if type(center_pos) == str:
            center_pos = list(map(int, center_pos.split(" ")))
        return "%sx%s+%s+%s" % (
            2 * delta,
            2 * delta,
            center_pos[0] - delta,
            center_pos[1] - delta,
        )

    def crop_of_bbox(self, bbox):
        x, y, width, height = bbox
        return "%sx%s+%s+%s" % (
            width,
            height,
            x,
            y,
        )

    def get_screenshot(self, center_pos=None, bbox=None, name=None, delta=15):
        # tiff is 2x faster than png, but 20x larger, so only good in tmpfs
        # use png for storage. the conversion between png and tiff is lossless:
        # for tiff in *.tiff; do convert $tiff $tiff.png; done
        # for tiff in *.tiff; do echo $(convert $tiff png:- | convert png:- tiff:- | sha1sum - | cut -d' ' -f1) $tiff; done
        basename = f"fetch-subs-{name}" if name else "fetch-subs"
        screenshot_path = f"{tempdir}/{basename}-{datetime_str()}-{random_hash()}.tiff"
        if center_pos:
            crop = self.crop_of_center_pos(center_pos, delta)
            # import -window root -crop $crop -colorspace Gray $screenshot_path
            args = ["import", "-window", "root", "-crop", crop, "-colorspace", "Gray", screenshot_path]
            subprocess.run(
                args,
                capture_output=True,
                check=True,
                env=self.xvnc_env,
            )
            return screenshot_path

        if bbox:
            crop = self.crop_of_bbox(bbox)
            args = ["import", "-window", "root", "-crop", crop, "-colorspace", "Gray", screenshot_path]
            subprocess.run(
                args,
                capture_output=True,
                check=True,
                env=self.xvnc_env,
            )
            return screenshot_path

        raise NotImplementedError("get_screenshot: center_pos == None")

    def get_full_screenshot(self):
        screenshot_path = f"{tempdir}/fetch-subs-{datetime_str()}-{random_hash()}.tiff"
        args = ["import", "-window", "root", "-colorspace", "Gray", screenshot_path]
        subprocess.run(
            args,
            capture_output=True,
            check=True,
            env=self.xvnc_env,
        )
        return screenshot_path

    def show_image(self, image_path):
        args = ["feh", image_path]
        # start the process but dont wait. let it run in the background
        proc = subprocess.Popen(
            args,
            #capture_output=True,
            #check=True,
            env=self.xvnc_env,
        )
        return proc



# kill all child processes when this script ends
# https://stackoverflow.com/a/51240825/10440128

class ExitHooks(object):
    def __init__(self):
        self.exit_code = None
        self.exception_type = None
        self.exception = None
        self.exception_args = None
        self.hook()

    def hook(self):
        self._orig_exit = sys.exit
        sys.exit = self.exit
        sys.excepthook = self.handle_exception

    def exit(self, code=0):
        self.exit_code = code
        self._orig_exit(code)

    def handle_exception(self, exc_type, exc, *exc_args):
        self.exception = (exc_type, exc, exc_args)
        cleanup_main()

hooks = ExitHooks()

@atexit.register
def cleanup_main():
    print("cleanup_main ...")
    if hooks.exit_code is not None:
        print("cleanup_main: death by sys.exit(%d)" % hooks.exit_code)
    elif hooks.exception is not None:
        (exc_type, exc, exc_args) = hooks.exception
        print(f"cleanup_main: death by exception: {exc_type.__name__}: {exc}")
        traceback.print_exception(exc)
    else:
        print("cleanup_main: natural death")
    current_process = psutil.Process()
    children = current_process.children(recursive=True)
    for child in children:
        print(f'cleanup_main: killing child process {child.name()} pid {child.pid}')
        try:
            child.terminate()
            # TODO wait max 30sec and then child.kill()?
        except Exception as e:
            print(f'cleanup_main: killing child process failed: {e}')
    # remove tempfiles
    for temp_path in global_remove_files_when_done:
        print(f'cleanup_main: removing temp path: {temp_path}')
        try:
            shutil.rmtree(temp_path)
        except NotADirectoryError:
            os.unlink(temp_path)
        except FileNotFoundError:
            pass
    print("cleanup_main done")



async def main():

    global user_agents
    global chromium_headful_scraper

    if options.proxy_provider == "zenrows.com":

        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    elif options.proxy_provider == "chromium":

        chromium_headful_scraper = await ChromiumHeadfulScraper(
            start_vnc_client=options.start_vnc_client,
            vnc_client_list=options.vnc_client_list,
            ssh_id_file_path=options.ssh_id_file_path,
        )

    elif options.proxy_provider == "pyppeteer":

        #sys.path.append("pyppeteer") # local version https://github.com/pyppeteer/pyppeteer/pull/16
        logger_print("import pyppeteer")
        import pyppeteer
        logger_print("pyppeteer", pyppeteer)

        # https://github.com/towry/n/issues/148
        # https://pypi.org/project/pyppeteer-stealth/
        # https://github.com/MeiK2333/pyppeteer_stealth
        sys.path.append("pyppeteer_stealth") # local version
        logger_print("import pyppeteer_stealth")
        import pyppeteer_stealth
        logger_print("pyppeteer_stealth", pyppeteer_stealth)

        logger_print("pyppeteer.launch")
        pyppeteer_browser = await pyppeteer.launch(
            # https://pptr.dev/api/puppeteer.puppeteerlaunchoptions
            headless=pyppeteer_headless,
            # path to /bin/chromium
            # chrome binaries from ~/.cache/puppeteer/chrome are not working on nixos linux
            # ldd ~/.cache/puppeteer/chrome/linux-*/chrome-linux/chrome | grep "not found"
            executablePath=os.environ["PUPPETEER_EXECUTABLE_PATH"],
            args=[
                # no effect
                #"--disable-blink-features=AutomationControlled",
            ],
        )

        logger_print("pyppeteer_browser.newPage")
        pyppeteer_page = await pyppeteer_browser.newPage()

        # TODO why is this not working?
        # selenium-detector still says "detected"
        # opensubtitles.org hangs at the cloudflare portal
        # only bot.sannysoft.com says "ok"
        logger_print("pyppeteer_stealth.stealth")
        await pyppeteer_stealth.stealth(pyppeteer_page)

        for url, path, sleep in [
            ('https://hmaker.github.io/selenium-detector/', 'chrome_headless_stealth.selenium-detector.png', 0), # wrong result?
            ('https://bot.sannysoft.com/', 'chrome_headless_stealth.bot.sannysoft.com.png', 0), # outdated?
            ('https://abrahamjuliot.github.io/creepjs/', 'chrome_headless_stealth.creepjs.png', 10),
            ('http://f.vision/', 'chrome_headless_stealth.fake-vision.png', 0),
            #('https://www.opensubtitles.org/en/search/subs', 'chrome_headless_stealth.opensubtitles-search-subs.png', 60),
        ][-1:]:
            logger_print("pyppeteer_page.goto", url)
            await pyppeteer_page.goto(url)
            time.sleep(sleep)
            logger_print("pyppeteer_page.screenshot", path)
            await pyppeteer_page.screenshot(path=path, fullPage=True)

        #await pyppeteer_browser.close()

        raise NotImplementedError

    #elif options.proxy_provider == "playwright":

    #first_num_file = last_num_db
    #last_num_file = 1

    os.makedirs(new_subs_dir, exist_ok=True)
    nums_done = []

    filenames = os.listdir(new_subs_dir)
    if os.path.exists(f"{new_subs_dir}/files.txt"):
        with open(f"{new_subs_dir}/files.txt") as f:
            for line in f:
                filenames.append(line.strip())

    for filename in filenames:
        #match = re.fullmatch(r"([0-9]+)\.(.+\.)?zip", filename)
        # retry .html files
        match = re.fullmatch(r"([0-9]+)\.(zip|not-found|.*\.zip)", filename)
        if not match:
            continue
        num = int(match.group(1))
        nums_done.append(num)

    nums_done = sorted(nums_done)

    if options.force_download:
        # quickfix
        nums_done = []

    logger.debug(f"nums_done {nums_done}")

    #num_stack_last = None
    num_stack_first = None

    if options.first_num:
        len_before = len(nums_done)
        nums_done = list(filter(lambda num: num >= options.first_num, nums_done))
        logger_print(f"using options.first_num {options.first_num} as lower limit for nums_done. len(nums_done): {len_before} -> {len(nums_done)}")

    nums_done_set = set(nums_done)

    # find first missing num
    # use options.first_num as lower limit to find num_stack_first
    first_num = options.first_num or 1
    num = first_num
    while True:
        if num not in nums_done_set:
            # first missing num
            num_stack_first = num
            break
        num += 1

    logger_print("num_stack_first", num_stack_first)

    # options.first_num allows to skip not-yet downloaded nums
    # options.first_num not allows to re-download already downloaded nums
    #if options.first_num and num_stack_last < (options.first_num - 1):
    #    num_stack_last = options.first_num - 1
    if options.first_num and num_stack_first < options.first_num:
        logger_print(f"raising num_stack_first {num_stack_first} to options.first_num {options.first_num}")
        num_stack_first = options.first_num
    #else:
    #    num_stack_first = num_stack_last
    #logger_print("num_stack_first", num_stack_first)

    downloads_since_change_ipaddr = 0

    # json file from https://www.useragents.me/
    with open("user_agents.json") as f:
        user_agents = json.load(f)
        # there is also x["pct"] = frequency of user agent in percent
        # but we dont need that value
        user_agents = list(map(lambda x: x["ua"], user_agents))

    user_agent = random.choice(user_agents)

    num_stack = []
    dt_download_list = collections.deque(maxlen=100) # last 100 dt
    t2_download_list = collections.deque(maxlen=100) # last 100 t2
    html_errors = collections.deque(maxlen=1000)

    # loop subtitle numbers

    num_downloads_done = 0

    while True:

        semaphore = asyncio.Semaphore(max_concurrency)
        aiohttp_kwargs = dict()
        # fix: aiohttp.client_exceptions.ClientConnectorCertificateError: Cannot connect to host dl.opensubtitles.org:443 ssl:True [SSLCertVerificationError: (1, '[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self-signed certificate in certificate chain (_ssl.c:997)')]
        #aiohttp_kwargs["verify_ssl"] = False
        aiohttp_kwargs["headers"] = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en-US,en;q=0.9",
            #"Sec-Ch-Ua": '"Not A(Brand";v="24", "Chromium";v="110"',
            #"Sec-Ch-Ua-Mobile": "?0",
            #"Sec-Ch-Ua-Platform": '"Linux"',
            #"Sec-Fetch-Dest": "document",
            #"Sec-Fetch-Mode": "navigate",
            #"Sec-Fetch-Site": "none",
            #"Sec-Fetch-User": "?1",
            #"Upgrade-Insecure-Requests": "1",
            "User-Agent": user_agent,
        }

        async with aiohttp.ClientSession(**aiohttp_kwargs) as aiohttp_session:

            if options.last_num == None:
                logger_print(f"getting options.last_num from remote")
                url = "https://www.opensubtitles.org/en/search/subs"

                response_status = None
                response_text = None

                if options.proxy_provider == None:
                    response = await aiohttp_session.get(url)
                    response_status = response.status
                    response_type = response.headers.get("Content-Type")
                    # TODO response_headers?
                    # TODO handle binary response
                    response_text = await response.text()

                elif options.proxy_provider == "chromium":
                    response = await chromium_headful_scraper.get_response(url)
                    response_status = response.status
                    response_type = response.headers.get("Content-Type")
                    # TODO handle binary response
                    response_text = await response.text()

                else:
                    raise NotImplementedError(f"options.proxy_provider {options.proxy_provider}")

                # response_status can be 429 Too Many Requests -> fatal error
                if response_status == 403:
                    if response_text.startswith("""<!DOCTYPE html><html lang="en-US"><head><title>Just a moment...</title><meta http-equiv="Content-Type" content="text/html; charset=UTF-8"><meta http-equiv="X-UA-Compatible" content="IE=Edge"><meta name="robots" content="noindex,nofollow"><meta name="viewport" content="width=device-width,initial-scale=1"><link href="/cdn-cgi/styles/challenges.css" rel="stylesheet"></head><body class="no-js"><div class="main-wrapper" role="main"><div class="main-content"><noscript><div id="challenge-error-title"><div class="h2"><span class="icon-wrapper"><div class="heading-icon warning-icon"></div></span><span id="challenge-error-text">Enable JavaScript and cookies to continue</span></div></div></noscript></div></div><script>(function(){window._cf_chl_opt="""):
                        logger_print(f"/en/search/subs 403 Access Denied [blocked by cloudflare] -> fatal error")
                        sys.exit(1)
                    logger_print(f"/en/search/subs 403 Access Denied -> fatal error")
                    sys.exit(1)
                if response_status == 429:
                    logger_print(f"/en/search/subs 429 Too Many Requests -> fatal error")
                    sys.exit(1)
                if response_status == 503:
                    logger_print(f"/en/search/subs 503 Service Unavailable -> fatal error")
                    sys.exit(1)
                assert response_status == 200, f"unexpected response_status {response_status}"
                assert response_type == "text/html; charset=UTF-8", f"unexpected content_type {repr(content_type)}"
                remote_nums = re.findall(r'href="/en/subtitles/(\d+)/', await response.text())
                logger.debug(f"remote_nums {repr(remote_nums)}")
                options.last_num = max(map(int, remote_nums))
                logger_print("options.last_num", options.last_num)

            if options.show_ip_address:
                url = "https://httpbin.org/ip"
                # TODO use proxy
                # no? no need to use proxy?
                response = None
                response_status = None
                for retry_step in range(20):
                    response = await aiohttp_session.get(url)
                    response_status = response.status
                    if response_status == 200:
                        break
                    # response_status example: 504
                    logger_print(f"unexpected response_status {response_status} -> retry")
                    time.sleep(5)
                response_type = response.headers.get("Content-Type")
                assert response_type == "application/json", f"unexpected content_type {repr(content_type)}"
                response_data = json.loads(await response.text())
                logger_print(f"IP address: {response_data.get('origin')}")

            #while not num_stack: # while stack is empty
            retry_counter = 0
            while len(num_stack) < options.sample_size: # while stack is empty
                if missing_numbers:
                    num_stack = missing_numbers
                    # slow but rare
                    for filename in os.listdir(new_subs_dir):
                        for num in missing_numbers:
                            if (
                                filename == f"{num}.not-found" or (
                                    filename.startswith(f"{num}.") and
                                    filename.endswith(".zip")
                                )
                            ):
                                missing_numbers.remove(num)
                    if len(missing_numbers) == 0:
                        raise Exception("done all missing_numbers")
                    break

                # add numbers to the stack
                #num_stack_first = num_stack_last + 1
                num_stack_last = num_stack_first + options.sample_size
                # next iteration
                #num_stack_first = num_stack_last + 1

                if options.last_num and num_stack_last > options.last_num:
                    logger_print(f"lowering num_stack_last {num_stack_last} to options.last_num {options.last_num}")
                    num_stack_last = options.last_num
                logger_print(f"stack range: ({num_stack_first}, {num_stack_last})")
                if num_stack_last < num_stack_first:
                    logger_print(f"stack range is empty")
                    break
                def filter_num(num):
                    return (
                        num not in nums_done_set
                        # already handled by num_stack_last
                        #and num <= options.last_num
                    )
                num_stack_expand = list(
                    filter(filter_num,
                        range(num_stack_first, num_stack_last + 1),
                        #random.sample(range(num_stack_first, options.last_num + 1), options.sample_size)
                    )
                )
                logger_print(f"num_stack_expand: {repr(num_stack_expand)}")
                #if len(num_stack_expand) == 0:
                #    logger_print(f"num_stack_expand is empty at num_stack size {len(num_stack)}")
                #    break
                num_stack += num_stack_expand

                # next iteration
                num_stack_first = num_stack_last + 1

                # TODO better
                retry_counter += 1
                if retry_counter > 1000:
                    break

            if len(num_stack) == 0:
                logger_print(f"done all nums until {options.last_num}")
                raise SystemExit

            logger.debug(f"num_stack: {num_stack}")
            random.shuffle(num_stack)

            if options.num_downloads:
                num_remain = options.num_downloads - num_downloads_done
                if num_remain <= 0:
                    logger_print(f"done {options.num_downloads} nums")
                    raise SystemExit
                logger_print(f"done: {num_downloads_done}. remain: {num_remain}")
                num_stack = num_stack[0:num_remain]
                logger.debug(f"num_stack: {num_stack}")

            logger_print(f"batch size: {len(num_stack)}")
            logger_print(f"batch: {num_stack}")

            tasks = []
            while num_stack:
                num = num_stack.pop()
                task = asyncio.create_task(fetch_num(num, aiohttp_session, semaphore, dt_download_list, t2_download_list, html_errors, config))
                tasks.append(task)
            return_values = await asyncio.gather(*tasks)
            # TODO show progress
            #logger_print("return_values", return_values)
            pause_scraper = False
            do_change_ipaddr = False
            for return_value in return_values:
                if return_value == None:
                    # success
                    num_downloads_done += 1
                    continue
                if type(return_value) == int:
                    # retry
                    num_stack.append(return_value)
                elif type(return_value) == dict:
                    if "done_num" in return_value:
                        # success
                        num_downloads_done += 1
                    if "retry_num" in return_value:
                        # retry
                        num_stack.append(return_value["retry_num"])
                    if "pause" in return_value:
                        pause_scraper = True
                    if "change_ipaddr" in return_value:
                        do_change_ipaddr = True

            if do_change_ipaddr:
                logger_print("changing IP address")
                change_ipaddr()

            if pause_scraper:
                t_sleep = random.randrange(20, 60)
                logger_print(f"pausing scraper for {t_sleep} seconds")
                time.sleep(t_sleep)
                # reset t2 values
                while t2_download_list:
                    t2_download_list.pop()

asyncio.get_event_loop().run_until_complete(main())
