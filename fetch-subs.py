#!/usr/bin/env python3

# watch "ls -lt new-subs/ | head"

# expected time: 1E6 * 0.1 / 3600 = 28 hours
# no. i over-estimated the number of requests
# it was only 300K requests, and it was done in about 1.5 days
# not bad, zenrows.com! :)

# TODO fe-fetch recent downloads
# give opensubtitles.org some time for moderation
# some time = some days = 3 days?

import sys
import os
import re
import urllib.request
import logging
import time
import random
import subprocess
import json
import glob
import collections
import zipfile
import base64
import asyncio
import argparse

import aiohttp
import requests
import magic # libmagic


# https://www.zenrows.com/ # Startup plan
#max_concurrency = 25 # concurrency limit was reached
max_concurrency = 10
# unexpected status_code 403. content: b'{"code":"BLK0001","detail":"Your IP address has been blocked for exceeding the maximum error rate al'...
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
    from secrets import api_key_zenrows_com
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
#new_subs_dir = "new-subs-temp-debug"

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
proxy_provider_values = ["zenrows.com"]
default_proxy_provider = None

#parser.add_argument('filename')
parser.add_argument(
    '--proxy-provider',
    dest="proxy_provider",
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
    print("options.num_downloads", repr(options.num_downloads))
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
        logger.info(f"killing ssh client")
        proc.kill()

    new_ipaddr = get_ipaddr()
    logger.info(f"changed IP address from {old_ipaddr} to {new_ipaddr}")
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
            logger.info(f"changed IP subnet from {first_ipaddr} to {new_ipaddr}")
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
        "Sec-Ch-Ua": "\"Not A(Brand\";v=\"24\", \"Chromium\";v=\"110\"",
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": "\"Linux\"",
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
            logger.info(f"{num} output file exists: {existing_output_files}")
            #continue
            return
        """

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
        status_code = None
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
            status_code = response.status_code

        elif options.proxy_provider == "zenrows.com":
            #proxy = f"http://{api_key_zenrows_com}:@proxy.zenrows.com:8001"
            zenrows_com_query_parts = []
            if config.zenrows_com_antibot:
                logger.info(f"{num} antibot=true")
                zenrows_com_query_parts += ["antibot=true"]
                # reset config for next request
                config.zenrows_com_antibot = False
            if config.zenrows_com_js:
                logger.info(f"{num} js_render=true")
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
                logger.info(f"{num} retry. error: {err}")
                return num # retry
            #logger_print("response", dir(response))
            #status_code = response.status_code # requests
            status_code = response.status # aiohttp
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

            status_code = response.status_code
            logger.info(f"{num} status_code: {status_code}")

            logger.info(f"{num} headers: {response.headers}")

            if status_code != 200:
                # 404 -> always JSON?
                logger.info(f"{num} content: {response_content}")

            # original headers are missing: Content-Type, Content-Disposition, ...
            magic_result = magic.detect_from_content(response_content)
            logger.info(f"{num} libmagic result: type: {magic_result.mime_type}, encoding: {magic_result.encoding}, name: {magic_result.name}")
            # examples: text/html, application/zip
            content_type = magic_result.mime_type
            if content_type == "application/octet-stream":
                # response_content is broken?
                # $ unzip -l 9185494.zip
                # error [9185494.zip]:  missing 985487216 bytes in zipfile
                logger.info(f"{num} libmagic failed to detect zip file. fixing content_type")
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

            status_code = response.status_code
            logger.info(f"{num} status_code: {status_code}")

            logger.info(f"{num} headers: {response.headers}")

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

            #status_code = response.status_code
            status_code = response_data["result"]["status_code"]

            if (
                response_data["result"]["success"] == False and
                status_code != 404
            ):
                logger.info(f"""{num} success: False. reason: {response_data["result"]["reason"]}""")

            if True:
                response_data_file = f"{new_subs_dir}/{num}.scrapfly.json"
                logger.info(f"""{num} writing json response to file: {response_data_file}""")
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

            #logger.info(f"{num} status_code: {status_code}")

            #logger.info(f"{num} headers: {response_headers}")

            #logger.info(f"{num} proxy pool: {response_data['context']['proxy']['pool']}")
            #logger.info(f"{num} cost total: {response_data['context']['cost']['total']}")
            #logger.info(f"{num} cost details: {response_data['context']['cost']['details']}")
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

            status_code = response.status_code
            logger.info(f"{num} status_code: {status_code}")

            logger.info(f"{num} headers: {response.headers}")

        elif options.proxy_provider == "chromium":
            args = ["chromium", url]
            subprocess.run(
                args,
                capture_output=True,
                check=True,
            )
            time.sleep(2)
            downloaded_files = glob.glob(f"/home/user/Downloads/*.({num}).zip")
            if len(downloaded_files) == 0:
                status_code = 404
            elif len(downloaded_files) == 1:
                filepath = downloaded_files[0]
                filename = os.path.basename(filepath)
                os.rename(filepath, f"{new_subs_dir}/{num}.{filename}")

                t2_download = time.time()
                dt_download = t2_download - t1_download
                dt_download_list.append(dt_download)
                t2_download_list.append(t2_download)
                dt_download_avg = sum(dt_download_list) / len(dt_download_list)
                dt_download_list_parallel = []
                t2_download_list_sorted = sorted(t2_download_list)
                for i in range(0, len(t2_download_list_sorted) - 1):
                    t2 = t2_download_list_sorted[i]
                    t2_next = t2_download_list_sorted[i + 1]
                    dt = t2_next - t2
                    dt_download_list_parallel.append(dt)
                if len(dt_download_list_parallel) > 0:
                    dt_download_avg_parallel = sum(dt_download_list_parallel) / len(dt_download_list_parallel)
                else:
                    dt_download_avg_parallel = 0

                logger.info("t2_download_list", t2_download_list)
                logger.info("dt_download_list_parallel", dt_download_list_parallel)

                #logger.debug("headers: " + repr(dict(headers)))
                sleep_each = random.randint(sleep_each_min, sleep_each_max)
                if sleep_each > 0:
                    logger.info(f"{num} 200 dt={dt_download:.3f} dt_avg={dt_download_avg:.3f} dt_par={dt_download_avg_parallel:.3f} -> waiting {sleep_each} seconds")
                else:
                    logger.info(f"{num} 200 dt={dt_download:.3f} dt_avg={dt_download_avg:.3f} dt_par={dt_download_avg_parallel:.3f}")
                #if dt_download_avg_parallel > 1:
                #    logger.info(f"460: {num} 200 dt_download_avg_parallel > 1: dt_download_list_parallel = {dt_download_list_parallel}")
                time.sleep(sleep_each)
                #continue
                return
            else:
                logger_print(f"error: found multiple downloaded files for num={num}:", downloaded_files)
                raise NotImplementedError

        elif options.proxy_provider == "pyppeteer":
            await pyppeteer_page.goto(url)
            raise NotImplementedError

        else:
            # no proxy
            # requests
            #response = requests.get(url, **requests_get_kwargs)
            #status_code = response.status_code
            # aiohttp
            response = await aiohttp_session.get(url, **requests_get_kwargs)
            status_code = response.status
            logger.debug(f"{num} status_code: {status_code}")
            logger.debug(f"{num} headers: {response.headers}")

        response_content = response_content or response.content
        response_headers = response_headers or response.headers

        # https://scrapingant.com/free-proxies/
        #proxy = "socks5://54.254.52.187:8118"

        if options.proxy_provider == "scrapingant.com":
            try:
                status_code = int(response_headers["Ant-Page-Status-Code"])
            except KeyError as err:
                logger_print(f"{num} status_code={status_code} KeyError: no Ant-Page-Status-Code. headers: {response_headers}. content: {response_content[0:100]}...")

        #logger_print(f"{num} status_code={status_code} headers:", response_headers)

        if status_code == 404:
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

            logger.info(f"{num} {status_code} dt={dt_download:.3f} dt_avg={dt_download_avg:.3f} dt_par={dt_download_avg_parallel:.3f}")
            #if dt_download_avg_parallel > 1:
            #    logger.info(f"499: {num} 200 dt_download_avg_parallel > 1: dt_download_list_parallel = {dt_download_list_parallel}")
            #num += 1
            #continue
            return # success

        if False and status_code == 429:
            # rate limiting
            # this happens after 30 sequential requests
            # only successful requests are counted (http 404 is not counted)
            # blocking is done by cloudflare?
            #logger.info(f"{num} {status_code} Too Many Requests -> waiting {sleep_blocked} seconds")
            #time.sleep(sleep_blocked)
            logger_print(f"{num} response_headers", response_headers)
            raise NotImplementedError(f"{num} {status_code} Too Many Requests -> TODO change VPN server")

            user_agent = random.choice(user_agents)

            if downloads_since_change_ipaddr == 0:
                # after too many change_ipaddr, they are blocking our subnet
                logger.info(f"{num} {status_code} Too Many Requests + no downloads -> changing IP subnet")
                # no. this takes too long and does not work,
                # because our user-agent is blocked
                #change_ipsubnet()
            else:
                logger.info(f"{num} {status_code} Too Many Requests -> changing IP address")
                change_ipaddr()
            downloads_since_change_ipaddr = 0
            # fix: http.client.RemoteDisconnected: Remote end closed connection without response
            # TODO aiohttp
            requests_session = new_requests_session()
            time.sleep(sleep_change_ipaddr)
            #continue
            return # success

        if status_code == 500:
            logger.info(f"{num} {status_code} Internal Server Error -> retry")
            return num # retry

        if status_code == 429:
            if False and content_type == "text/html; charset=UTF-8":
                # captcha page
                # bug in proxy provider
                logger.info(f"{num} {status_code} captcha -> retry")
                return num # retry
            response_text = (await response_content.read()).decode("utf8")
            content_type = content_type or response_headers.get("Content-Type")
            error_filename = f"http-429-at-num-{num}.html"
            logger_print(f"{num} {status_code} response_headers", response_headers)
            logger.info(f"{num} {status_code} content_type={repr(content_type)} + response_text in {error_filename} -> retry")
            with open(error_filename, "w") as f:
                f.write(response_text)
            return num # retry

        if status_code in {422, 403, 503}:
            response_text = (await response_content.read()).decode("utf8")
            logger.info(f"{num} {status_code} response_text: {repr(response_text)}")
            if response_text == "":
                # json.loads -> json.decoder.JSONDecodeError Expecting value
                logger.info(f"{num} {status_code} got empty response_text -> retry")
                return num
            response_data = json.loads(response_text)
            if response_data["code"] == "RESP001":
                # Could not get content. try enabling javascript rendering for a higher success rate (RESP001)
                #config.zenrows_com_js = True
                #config.zenrows_com_antibot = True
                #logger.info(f"{num} retry. error: need javascript")
                logger.info(f"{num} 404 dcma")
                # create empty file
                filename_dcma = f"{new_subs_dir}/{num}.dcma"
                open(filename_dcma, 'a').close() # create empty file
                return # success
                #return num # retry
                #return {"retry_num": num, "pause": True} # pause scraper, retry
            if response_data["code"] == "AUTH006":
                # The concurrency limit was reached. Please upgrade to a higher plan or ...
                logger.info(f"{num} {status_code} retry. error: concurrency limit was reached @ {response_text}")
                return {"retry_num": num, "pause": True} # pause scraper, retry
            if response_data["code"] == "BLK0001":
                # Your IP address has been blocked for exceeding the maximum error rate ...
                logger.info(f"{num} {status_code} retry. error: IP address was blocked @ {response_text}")
                return {"retry_num": num, "pause": True, "change_ipaddr": True} # pause scraper, change IP address, retry
            if response_data["code"] == "CTX0002":
                # Operation timeout exceeded (CTX0002)
                return {"retry_num": num, "pause": True} # pause scraper, retry
            logger.info(f"{num} {status_code} retry. headers: {response_headers}. content: {await response_content.read()}")
            return num # retry

        # requests
        #assert status_code == 200, f"{num} unexpected status_code {status_code}. headers: {response_headers}. content: {response_content[0:100]}..."
        # aiohttp
        assert status_code == 200, f"{num} unexpected status_code {status_code}. headers: {response_headers}. content: {await response_content.read()}"

        content_type = content_type or response_headers.get("Content-Type")

        if content_type != "application/zip":
            # blocked
            # TODO retry download
            #logger_print(f"{num} status_code={status_code} content_type={content_type}. headers: {response_headers}. content: {response_content[0:100]}...")
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
                    logger.info(f"""{num} FIXME Zr-Final-Url: {response_headers.get("Zr-Final-Url")}""")
                else:
                    logger.info(f"{num} status_code={status_code} content_type={content_type}. headers: {response_headers}")
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
                #logger_print(f"{num} status_code={status_code} content_type={content_type}. headers: {response_headers}. content: {response_content[0:100]}...")
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
        if fetcher_lib == "aiohttp":
            with open(filename_tmp, file_open_mode) as f:
                f.write(await response_content.read())
        #else:
        #    # requests
        #    with open(filename_tmp, file_open_mode) as f:
        #        f.write(response_content)
        os.rename(filename_tmp, filename)

        if filename.endswith(".html"):
            html_errors.append(True)
            html_error_probability = sum(map(lambda _: 1, filter(lambda x: x == True, html_errors))) / len(html_errors)
            logger.info(f"{num} retry. error: html p={html_error_probability * 100:.2f}%")
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
                logger.info(f"{num} broken zipfile: {filename} - moving to {filename}.broken - error: {err}")
                os.rename(filename, filename + ".broken")

        t2_download = time.time()
        dt_download = t2_download - t1_download
        dt_download_list.append(dt_download)
        t2_download_list.append(t2_download)
        t2_download_list_sorted = sorted(t2_download_list)
        dt_download_avg = sum(dt_download_list) / len(dt_download_list)
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

        #logger.info("t2_download_list", t2_download_list)
        #logger.info("dt_download_list_parallel", dt_download_list_parallel)

        #logger.debug("headers: " + repr(dict(headers)))
        sleep_each = random.randint(sleep_each_min, sleep_each_max)
        if sleep_each > 0:
            logger.info(f"{num} 200 dt={dt_download:.3f} dt_avg={dt_download_avg:.3f} dt_par={dt_download_avg_parallel:.3f} -> waiting {sleep_each} seconds")
        else:
            logger.info(f"{num} 200 dt={dt_download:.3f} dt_avg={dt_download_avg:.3f} dt_par={dt_download_avg_parallel:.3f}")
        #if dt_download_avg_parallel > 1:
        #    logger.info(f"635: {num} 200 dt_download_avg_parallel > 1: dt_download_list_parallel = {dt_download_list_parallel}")
        #time.sleep(sleep_each)
        #break
        #num += 1
        return # success


user_agents = None


async def main():

    global user_agents

    if options.proxy_provider == "zenrows.com":
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    elif options.proxy_provider == "pyppeteer":
        # puppeteer is old, chrome only, but stealth plugin works?
        import pyppeteer
        # https://github.com/towry/n/issues/148
        # https://pypi.org/project/pyppeteer-stealth/
        # https://github.com/MeiK2333/pyppeteer_stealth
        sys.path.append("pyppeteer_stealth") # local version
        import pyppeteer_stealth
        logger_print("pyppeteer_stealth", pyppeteer_stealth)
        # TODO test sites:
        # https://abrahamjuliot.github.io/creepjs/
        # http://f.vision/
        # via https://github.com/QIN2DIM/undetected-playwright/issues/2

        logger_print("pyppeteer.launch")
        pyppeteer_browser = await pyppeteer.launch(
            # https://pptr.dev/api/puppeteer.puppeteerlaunchoptions
            headless=pyppeteer_headless,
            executablePath=os.environ["PUPPETEER_EXECUTABLE_PATH"],
            args=[
                # no effect
                #"--disable-blink-features=AutomationControlled",
            ],
        )

        logger_print("pyppeteer_browser.newPage")
        pyppeteer_page = await pyppeteer_browser.newPage()

        # TODO why is this not working?
        logger_print("pyppeteer_stealth.stealth")
        await pyppeteer_stealth.stealth(pyppeteer_page)

        for url, path in [
            ('https://hmaker.github.io/selenium-detector/', 'chrome_headless_stealth.selenium-detector.png'),
            ('https://bot.sannysoft.com/', 'chrome_headless_stealth.bot.sannysoft.com.png'), # outdated
            #('https://whatsmyuseragent.org/', 'chrome_headless_stealth.whatsmyuseragent.org.png'),
            #("https://dl.opensubtitles.org/en/download/sub/9184234", 'chrome_headless_stealth.dl.opensubtitles.org.png'),
            ('https://abrahamjuliot.github.io/creepjs/', 'chrome_headless_stealth.creepjs.png'),
            ('http://f.vision/', 'chrome_headless_stealth.fake-vision.png'),
        ]:
            await pyppeteer_page.goto(url)
            if url == 'https://abrahamjuliot.github.io/creepjs/':
                #for i in range(3):
                #    await asyncio.sleep(10)
                #    await pyppeteer_page.screenshot(path=path + f".{(i + 1) * 10}.png", fullPage=True)
                await asyncio.sleep(10)
            await pyppeteer_page.screenshot(path=path, fullPage=True)
            logger_print(f"done: {path}")

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

    first_num_file = None
    last_num_file = 0

    if nums_done:
        first_num_file = nums_done[0]
        last_num_file = nums_done[-1]

    logger_print("first_num_file", first_num_file)
    logger_print("last_num_file", last_num_file)

    #requests_session = new_requests_session()

    num_stack_last = None

    # find first missing file
    for idx in range(0, len(nums_done) - 1):
        if nums_done[idx] + 1 != nums_done[idx + 1]:
            num_stack_last = nums_done[idx]
            break

    if num_stack_last == None:
        # no missing files, continue with last file
        #num_stack_last = first_num_file
        num_stack_last = last_num_file


    if options.first_num:
        #num_stack_first = options.first_num
        num_stack_last = options.first_num - 1
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

    nums_done_set = set(nums_done)
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
            #"Sec-Ch-Ua": "\"Not A(Brand\";v=\"24\", \"Chromium\";v=\"110\"",
            #"Sec-Ch-Ua-Mobile": "?0",
            #"Sec-Ch-Ua-Platform": "\"Linux\"",
            #"Sec-Fetch-Dest": "document",
            #"Sec-Fetch-Mode": "navigate",
            #"Sec-Fetch-Site": "none",
            #"Sec-Fetch-User": "?1",
            #"Upgrade-Insecure-Requests": "1",
            "User-Agent": user_agent,
        }

        async with aiohttp.ClientSession(**aiohttp_kwargs) as aiohttp_session:

            if options.last_num == None:
                logger.info(f"getting options.last_num from remote")
                url = "https://www.opensubtitles.org/en/search/subs"
                # TODO use proxy
                response = await aiohttp_session.get(url)
                status_code = response.status
                assert status_code == 200, f"unexpected status_code {status_code}"
                content_type = response.headers.get("Content-Type")
                assert content_type == "text/html; charset=UTF-8", f"unexpected content_type {repr(content_type)}"
                remote_nums = re.findall(r'href="/en/subtitles/(\d+)/', await response.text())
                logger.debug(f"remote_nums {repr(remote_nums)}")
                options.last_num = max(map(int, remote_nums))
                logger_print("options.last_num", options.last_num)

            if options.show_ip_address:
                url = "https://httpbin.org/ip"
                # TODO use proxy
                response = None
                status_code = None
                for retry_step in range(20):
                    response = await aiohttp_session.get(url)
                    status_code = response.status
                    if status_code == 200:
                        break
                    # status_code example: 504
                    logger_print(f"unexpected status_code {status_code} -> retry")
                    time.sleep(5)
                content_type = response.headers.get("Content-Type")
                assert content_type == "application/json", f"unexpected content_type {repr(content_type)}"
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
                num_stack_first = num_stack_last + 1
                num_stack_last = num_stack_first + options.sample_size
                if options.last_num and num_stack_last > options.last_num:
                    num_stack_last = options.last_num
                #logger.debug(f"stack range: ({num_stack_first}, {num_stack_last})")
                def filter_num(num):
                    return (
                        num not in nums_done_set and
                        num <= options.last_num
                    )
                num_stack_expand = list(
                    filter(filter_num,
                        range(num_stack_first, num_stack_last + 1),
                        #random.sample(range(num_stack_first, options.last_num + 1), options.sample_size)
                    )
                )
                if len(num_stack_expand) == 0:
                    logger.info(f"num_stack_expand is empty at num_stack size {len(num_stack)}")
                    break
                num_stack += num_stack_expand
                retry_counter += 1
                if retry_counter > 20:
                    break

            if len(num_stack) == 0:
                logger.info(f"done all nums until {options.last_num}")
                raise SystemExit

            logger.debug(f"num_stack: {num_stack}")
            random.shuffle(num_stack)

            if options.num_downloads:
                num_remain = options.num_downloads - num_downloads_done
                if num_remain <= 0:
                    logger.info(f"done {options.num_downloads} nums")
                    raise SystemExit
                logger.info(f"done: {num_downloads_done}. remain: {num_remain}")
                num_stack = num_stack[0:num_remain]
                logger.debug(f"num_stack: {num_stack}")

            logger.info(f"batch size: {len(num_stack)}")
            #logger.info(f"batch: {num_stack}")

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
                logger.info("changing IP address")
                change_ipaddr()

            if pause_scraper:
                t_sleep = random.randrange(20, 60)
                logger.info(f"pausing scraper for {t_sleep} seconds")
                time.sleep(t_sleep)
                # reset t2 values
                while t2_download_list:
                    t2_download_list.pop()

asyncio.get_event_loop().run_until_complete(main())
