#!/usr/bin/env python3

# TODO check internet connection = check DNS
# ping 1.1.1.1 + resolveip opensubtitles.org

# TODO visualize missing nums versus complete shards

# TODO scrape ratings + download counts of all subs
# intercept requests to only fetch the html code
# dont fetch images, styles, scripts

# TODO keep track of download count / quota
# when is the quota reset to zero?

# FIXME error: Site will be online soon. We are doing some necessary backups and upgrades. Thanks for understanding.
# <pre>Site will be online soon. We are doing some necessary backups and upgrades. Thanks for understanding.

# FIXME psutil.NoSuchProcess @ psutil
#     logger_print(f'cleanup_main: killing child process {child.name()} pid {child.pid}')

# TODO check download_quota versus daily_quota
# also remove daily_quota_is_exceeded

# FIXME also create empty files for missing subs
# when scraping the latest 1000 subs in descending order

# FIXME integrate fetch-subs-add-zipfiles.sh into this script
# adding one file to new-subs-repo takes about 2 seconds
# and we can use this delay as "sleep time" for the scraper

# FIXME CDPError: DOM Error while querying

# NOTE lots of dead code and bad coding style here...
# but it kind-of works :P

# FIXME chromium is rendering pages much slower
# when the chromium window is not visible on the desktop
# = if the chromium window is "hidden" in the background

# TODO headful scraper with captcha solver
# fix: blocked -> start a new session

# TODO fetch missing subs of first release
# between sub ID 1 and 9180518

# watch "ls -lt new-subs/ | head"

# TODO wait between requests -> fix semaphore

# TODO fix ublock extension -> options.add_argument

# TODO set name of root logger -> def logger_print

# FIXME asyncio ERROR Task exception was never retrieved
# handle errors from aiohttp_chromium_session.get

# FIXME postprocess: fix wrong dmca entries
# examples:
# these files were not processed by new-subs-migrate.py
# because dmca entries exist in new-subs-repo/files.txt
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
9540304.dmca
9540451.dmca
9540221.dmca
9540240.dmca
9540353.dmca
9540310.dmca
9540476.dmca



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

# python stdlib modules
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
import _io
import string
import itertools
import http.cookiejar
import math
import sqlite3

# pypi modules
import aiohttp
import requests
import magic # libmagic
import psutil
import nest_asyncio

import cryptography.hazmat.primitives.asymmetric.rsa
import cryptography.hazmat.primitives.serialization
import cryptography.x509
import cryptography.hazmat.primitives.hashes

# allow nesting multiple asyncio event loops
# fix: RuntimeError: This event loop is already running
nest_asyncio.apply()

sys.path.append("lib/thirdparty/aiohttp_chromium/src")
import aiohttp_chromium
print("imported aiohttp_chromium", aiohttp_chromium)

# TODO copy to aiohttp_chromium
from selenium_driverless.types.by import By
# selenium_webdriver.__package__ == "selenium_driverless"
from selenium_driverless.types.webelement import NoSuchElementException
from selenium_driverless.types.deserialize import StaleJSRemoteObjReference



# used by FlareSolverr
# https://github.com/FlareSolverr/FlareSolverr
# FlareSolverr/src/undetected_chromedriver/
# TODO why not use undetected_chromedriver directly
# FIXME undetected_chromedriver fails to bypass cloudflare. wtf? works in FlareSolverr
# TODO why exactly? what would FlareSolverr do?
# https://github.com/ultrafunkamsterdam/undetected-chromedriver
# NOTE my patched version of undetected_chromedriver
# also accepts these kwargs in chrome_args
#   driver_executable_path
#   driver_executable_is_patched
#   browser_executable_path
# FIXME driver.get does not support the "timeout" kwarg
#   await asyncify(driver.get("https://nowsecure.nl/#relax", timeout=20))
#import undetected_chromedriver as selenium_webdriver
# selenium_webdriver.__package__ == "undetected_chromedriver"



# TODO seleniumwire with socks5 proxy https://github.com/wkeeling/selenium-wire/issues/656

"""
# TODO go back to flaresolverr + requests/aiohttp
# no. seleniumwire is not working to bypass cloudflare
# no, this does not use undetected_chromedriver
#import seleniumwire.webdriver as selenium_webdriver
# make sure that undetected_chromedriver is installed
import undetected_chromedriver as _undetected_chromedriver
# https://github.com/wkeeling/selenium-wire#bot-detection
# FIXME selenium-wire's certificate (ca.crt) is not added to chromium
# https://github.com/wkeeling/selenium-wire/tree/master#certificates
# FIXME import of ca.crt fails:
# Certificate Import Error
# The Private Key for this Client Certificate is missing or invalid
# TODO create ca.pem file
# https://github.com/wkeeling/selenium-wire
import seleniumwire.undetected_chromedriver as undetected_chromedriver
"""

# TODO make seleniumwire work with latest mitmproxy
# ImportError: cannot import name 'connections' from 'mitmproxy'
#import seleniumwire.undetected_chromedriver as selenium_webdriver

# debug FlareSolverr
# https://github.com/FlareSolverr/FlareSolverr/discussions/806
# LOG_LEVEL=debug LOG_HTML=true HEADLESS=false
# flaresolverr module
# https://github.com/milahu/nur-packages/blob/master/pkgs/python3/pkgs/flaresolverr/flaresolverr.nix
#import flaresolverr.flaresolverr
# this would work like flaresolverr.flaresolverr.main()
# but we must set envs:
# CHROME_EXE_PATH
# PATCHED_DRIVER_PATH
# PATCHED_DRIVER_IS_PATCHED
# so instead, we use subprocess.Popen to run flaresolverr

# FIXME the default selenium api does not return the response status
# https://stackoverflow.com/questions/6509628/how-to-get-http-response-code-using-selenium-webdriver
# TODO? https://github.com/kaliiiiiiiiii/Selenium-Driverless#use-events

# local modules
import pyrfc6266
#import nssdb
from AiohttpMozillaCookieJar import AiohttpMozillaCookieJar

# https://www.zenrows.com/ # Startup plan
#max_concurrency = 25 # concurrency limit was reached
max_concurrency = 10
# unexpected response_status 403. content: b'{"code":"BLK0001","detail":"Your IP address has been blocked for exceeding the maximum error rate al'...
# -> change_ipaddr()
max_concurrency = 1 # debug
#max_concurrency = 2



# no. scraping nums in random order is required to bypass blocking
# when scraping nums in linear order, the scraper hangs after: ClientResponse.content: done
# ... probably hangs at (await response.content.read())
#fetch_nums_in_random_order = False
fetch_nums_in_random_order = True



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
try:
    from fetch_subs_secrets import proxy_scrapfly_io_api_key
except ImportError:
    proxy_scrapfly_io_api_key = None
proxy_scrapfly_io_cache_response = True

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



# opensubtitles.org

try:
    from fetch_subs_secrets import opensubtitles_org_logins
except ImportError:
    opensubtitles_org_logins = None

opensubtitles_org_login_cookies_txt_path = None
opensubtitles_org_login_cookie_jar = None



# opensubtitles.com
# https://opensubtitles.stoplight.io/docs/opensubtitles-api/e3750fd63a100-getting-started
# Your consumer can query the API on its own, and download 5 subtitles per IP's per 24 hours,
# but a user must be authenticated to download more.
# Users will then be able to download as many subtitles as their ranks allows,
# from 10 as simple signed up user, to 1000 for VIP user.
# Download counters resets at midnight UTC time

try:
    from fetch_subs_secrets import opensubtitles_com_logins
except ImportError:
    opensubtitles_com_logins = None

opensubtitles_com_login_headers = {}




class Config:
    zenrows_com_antibot = False
    zenrows_com_js = False
config = Config()

#options.proxy_provider = "scraperbox.com"
proxy_scraperbox_com_api_key = "56B1354FD63EB435CA1A9096B706BD55"

#options.proxy_provider = "scrapingant.com"
api_key_scrapingant_com = "6ae0de59fad34337b2ee86814857278a"


new_subs_dir = "new-subs"
"""
new_subs_repo_dir = "new-subs-repo"
#new_subs_dir = "new-subs-temp-debug"
"""
new_subs_repo_shards_dir = "new-subs-repo-shards"

def datetime_str():
    # https://stackoverflow.com/questions/2150739/iso-time-iso-8601-in-python#28147286
    return datetime.datetime.now(datetime.UTC).strftime("%Y%m%dT%H%M%S.%fZ")



global_remove_files_when_done = []



def make_x509_cert_pem_bytes() -> bytes:
    # generate a self-signed x509 certificate in python
    # https://cryptography.io/en/latest/x509/tutorial/#creating-a-self-signed-certificate
    # rename imports
    rsa = cryptography.hazmat.primitives.asymmetric.rsa
    serialization = cryptography.hazmat.primitives.serialization
    x509 = cryptography.x509
    NameOID = cryptography.x509.oid.NameOID
    hashes = cryptography.hazmat.primitives.hashes
    # Generate our key
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    # Various details about who we are. For a self-signed certificate the
    # subject and issuer are always the same.
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Some Province"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "Some Locality"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Some Organization"),
        x509.NameAttribute(NameOID.COMMON_NAME, "some-common-name.com"),
    ])

    # FIXME chromium dont like our cert
    """
    Certification Authority Import Error
    The file contained one certificate, which was not imported:
    some-common-name.com: Not a Certification Authority
    """

    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.now(datetime.timezone.utc)
    ).not_valid_after(
        # Our certificate will be valid for about 100 years
        datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(weeks=100*52)
    ).add_extension(
        x509.SubjectAlternativeName([x509.DNSName("localhost")]),
        critical=False,
    # Sign our certificate with our private key
    ).sign(key, hashes.SHA256())

    return cert.public_bytes(serialization.Encoding.PEM)



# https://stackoverflow.com/a/20372465/10440128
from inspect import currentframe
def __line__():
    cf = currentframe()
    return cf.f_back.f_lineno



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

default_jobs = 1 # see also: max_concurrency
default_num_downloads = 25

# with larger samples, produce more incomplete shards
# see also fetch_nums_in_random_order
default_sample_size = 1000
#default_sample_size = 200 # too low? blocked after some requests

"""
proxy_provider_values = [
  #"pyppeteer",
  "chromium",
  "zenrows.com",
]
"""
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
        #f"values: {', '.join(proxy_provider_values)}"
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
# see also: max_concurrency
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
    "--username",
    dest="username",
    default=None,
    type=str,
    metavar="S",
    help="username for login",
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
parser.add_argument(
    "--tempdir",
    dest="tempdir",
    default=None,
    type=str,
    metavar="path",
    help="path to tempdir",
)
parser.add_argument(
    "--metadata-db",
    dest="metadata_db",
    default=None,
    type=str,
    metavar="path",
    help="path to subtitles_all.db - parsed from subtitles_all.txt.gz",
)
parser.add_argument(
    "--only-update-metadata-db",
    dest="only_update_metadata_db",
    action='store_true',
    help="update subtitles_all.db and exit",
)

#options = parser.parse_args(sys.argv)
options = parser.parse_args()

options.vnc_client_list += re.split(r"\s+", os.environ.get("REVERSE_VNC_SERVERS", ""))

logging_level = "INFO"
if options.debug:
    # TODO disable debug log from selenium (too verbose)
    logging_level = "DEBUG"

logging.basicConfig(
    #format='%(asctime)s %(levelname)s %(message)s',
    # also log the logger %(name)s, so we can filter by logger name
    format='%(asctime)s %(name)s %(levelname)s %(message)s',
    level=logging_level,
)

logger = logging.getLogger("fetch-subs")

def logger_print(*args):
    logger.info(" ".join(map(str, args)))


if type(options.num_downloads) == str:
    logger_print("options.num_downloads", repr(options.num_downloads))
    if re.match(r"^\d+$", options.num_downloads):
        options.num_downloads = int(options.num_downloads)
    elif re.match(r"^(\d+)-(\d+)$", options.num_downloads):
        m = re.match(r"^(\d+)-(\d+)$", options.num_downloads)
        options.num_downloads = random.randint(int(m.group(1)), int(m.group(2)))
        logging.info(f"options.num_downloads: {options.num_downloads}")

# global state
metadata_db_con = None
metadata_db_cur = None

async def update_metadata_db():

    # FIXME subtitles_all.txt.gz-parse.py
    #return # dont update

    if not options.metadata_db:
        return

    max_age = 10*24*60*60 # 10 days
    age = time.time() - os.path.getmtime(options.metadata_db)

    if age <= max_age:
        return

    # https://stackoverflow.com/questions/538666/format-timedelta-to-string
    def format_age(age):
        age = datetime.timedelta(seconds=age)
        return str(age)

    logger_print(f"updating metadata db {repr(options.metadata_db)}. age {format_age(age)} > max_age {format_age(max_age)}")

    # debug: use an existing .txt.gz file to avoid re-downloading
    existing_txt_gz_path = None
    #existing_txt_gz_path = "subtitles_all.txt.gz.20240714T173551Z"

    if existing_txt_gz_path:
        txt_gz_path = existing_txt_gz_path
        logger_print(f"updating metadata db: using existing {txt_gz_path} - FIXME disable existing_txt_gz_path")

    else:
        # download the .txt.gz file
        # file size 400 MByte @ 2024-07-15
        # so this should fit into RAM
        # but ideally, aiohttp_chromium_session.get should write directly to disk
        url = "https://dl.opensubtitles.org/addons/export/subtitles_all.txt.gz"
        txt_gz_path = f"subtitles_all.txt.gz.{datetime_str()}"

        logger_print(f"updating metadata db: fetching {txt_gz_path} from {url}")

        # FIXME?

        aiohttp_chromium_session = await aiohttp_chromium.ClientSession(
            #cookie_jar=cookie_jar,
            #tempdir=tempdir,
            _headless=True,
        )

        async def response_cleanup_chromium():
            await response.__aexit__(None, None, None)

        response_cleanup = response_cleanup_chromium

        try:
            response = await aiohttp_chromium_session.get(url)
            logger_print(f"updating metadata db: mv {response._filepath} {txt_gz_path}")
            #os.rename(response._filepath, txt_gz_path) # why not?
            logger_print(f"response._filepath = {repr(response._filepath)}")
            # wait until response is complete
            # FIXME this can hang. TODO timeout + retry
            # TODO open url to monitor download progress: chrome://downloads/
            # TODO log download-progress every 30 seconds to debug log
            logger_print("response._wait_complete ...")
            t1 = time.time()
            try:
                # the download takes between 4 minutes and 4 hours
                # -> timeout: 10 hours
                await response._wait_complete(timeout=10*60*60)
            except TimeoutError:
                await response_cleanup()
                raise Exception(f"{num} download failed")
            t2 = time.time()
            logger_print("response._wait_complete done after {(t2 - t1):.3f} seconds")
            shutil.move(response._filepath, txt_gz_path)
        #except asyncio.exceptions.TimeoutError as e:
        except Exception as e:
            logger_print(f"updating metadata db failed: {e}")
            await aiohttp_chromium_session.close()
            return
        await aiohttp_chromium_session.close()

        #### response_cleanup

    # TODO keep only one old file, delete all older versions
    keep_old_file = False
    keep_old_file = True # debug

    logger_print(f"updating metadata db: parsing tsv to sqlite ...")
    # parser fails if db_path exists so use a tempfile
    #db_path_temp = f"{txt_gz_path}.db.temp.{datetime_str()}"
    db_path = f"{txt_gz_path}.db"
    error_path = f"{db_path}.error"
    debug_path = f"{db_path}.debug"
    table_name = "subz_metadata"

    if os.path.exists(db_path):
        # parser fails if db_path exists
        #logger_print(f"updating metadata db: error: output file exists: {db_path}")
        #return
        logger_print(f"updating metadata db: deleting old output file: {db_path}")
        os.unlink(db_path)

    logger_print(f"updating metadata db: writing {db_path}")

    args = [
        sys.executable, # python
        "-u", # unbuffer output
        "subtitles_all.txt.gz-parse.py",
        db_path,
        table_name,
        txt_gz_path,
        error_path,
        debug_path,
    ]

    logger_print(f"updating metadata db: running: {shlex.join(args)}")

    proc = subprocess.run(args)

    if proc.returncode != 0:
        logger_print(f"updating metadata db: parsing tsv to sqlite failed")
        return

    logger_print(f"updating metadata db: parsing tsv to sqlite done")

    if os.path.islink(options.metadata_db):
        if not keep_old_file:
            # note: this will not follow symlinks
            link_target = os.readlink(options.metadata_db)
            logger_print(f"updating metadata db: rm {link_target}")
            os.unlink(link_target)
        logger_print(f"updating metadata db: rm {options.metadata_db}")
        os.unlink(options.metadata_db)
    else:
        if keep_old_file:
            bak_path = options.metadata_db + f".bak.{datetime_str()}"
            logger_print(f"updating metadata db: mv {options.metadata_db} {bak_path}")
            os.rename(options.metadata_db, bak_path)
        else:
            logger_print(f"updating metadata db: rm {options.metadata_db}")
            os.unlink(options.metadata_db)

    logger_print(f"updating metadata db: ln -s {db_path} {options.metadata_db}")
    os.symlink(db_path, options.metadata_db)

"""
await update_metadata_db()



if options.metadata_db:
    logger_print(f"using metadata db {repr(options.metadata_db)}")
    metadata_db_con = sqlite3.connect(options.metadata_db)
    metadata_db_cur = metadata_db_con.cursor()
"""



# postprocess: fetch missing subs
# example: https://www.opensubtitles.org/en/subtitles/9205951
# this is a bug in opensubtitles.org
# the server returns infinite cyclic redirect via
# https://www.opensubtitles.org/en/msg-dmca
# and zenrows says: error: need javascript
# ... so these files were deleted because of dmca takedown requests (by copyright trolls)
missing_numbers = []

missing_numbers_txt_path = "missing_numbers.txt"
if os.path.exists(missing_numbers_txt_path):
    logger_print(f"loading missing_numbers from {missing_numbers_txt_path}")
    with open(missing_numbers_txt_path, "r") as f:
        try:
            nums = list(map(int, f.read().strip().split("\n")))
        except ValueError:
            # ValueError: invalid literal for int() with base 10: ''
            nums = []
        logger_print(f"loaded missing_numbers from {missing_numbers_txt_path}: {nums}")
        missing_numbers += nums

logger.debug(f"{__line__()} missing_numbers = {missing_numbers}")

if missing_numbers:

    # filter
    # os.path.exists
    # glob.glob
    # os.listdir

    logger_print(f"fetching {len(missing_numbers)} missing numbers:", missing_numbers)

    # postprocess: create empty dmca files
    # TODO detect these files while scraping
    # in the future, zenrows may return a different error than
    # RESP001 (Could not get content. try enabling javascript rendering)
    # zenrows support:
    # > The error might be misleading, but apart from changing that, we can't do anything else.
    # > BTW, if they return a status code according to the error, you might get it back with original_status=true
    #for num in missing_numbers:
    #    # create empty file
    #    filename_dcma = f"{new_subs_dir}/{num}.dmca"
    #    open(filename_dcma, 'a').close() # create empty file
    #raise Exception("done postprocessing")

# sleep X seconds after each download
# to avoid http status "429 Too Many Requests"
#sleep_each_min, sleep_each_max = 0, 3
#sleep_each_min, sleep_each_max = 0, 20
#sleep_each_min, sleep_each_max = 0, 200

max_downloads_per_day = 1000 # vip account
#sleep_each_avg = (24 * 60 * 60) / max_downloads_per_day



new_session_sleep_min, new_session_sleep_max = 5*60, 10*60

# sleep X seconds after getting blocked for too many requests
blocked_sleep_min, blocked_sleep_max = 2.2*60*60, 2.6*60*60
# quota: 200 requests per day in chunks of 20 requests
# = 20 requests every 2.4 hours

# sleep X seconds after blocked by server
sleep_blocked = 24*60*60

# sleep X seconds after changing IP address
sleep_change_ipaddr = 10
sleep_change_ipaddr_min, sleep_change_ipaddr_max = 5*60, 15*60 # 5...10 minutes
sleep_change_ipaddr_min, sleep_change_ipaddr_max = 15*60, 45*60 # 15...45 minutes
#sleep_change_ipaddr_min, sleep_change_ipaddr_max = 5*60, 15*60 # 5...15 minutes
#sleep_change_ipaddr_min, sleep_change_ipaddr_max = 5*60, 45*60 # 5...45 minutes
#sleep_change_ipaddr_min, sleep_change_ipaddr_max = 3*60, 15*60 # 3...15 minutes
# sleep 5 minutes = 30*24*60/5 = 8640 downloads per day
# sleep 10 minutes = 30*24*60/10 = 4320 downloads per day
# sleep 15 minutes = 30*24*60/15 = 2880 downloads per day
# sleep 30 minutes = 30*24*60/30 = 1440 downloads per day
# sleep 45 minutes = 30*24*60/45 = 960 downloads per day

is_greedy = False
#is_greedy = True



if is_greedy:
    sleep_each_min, sleep_each_max = 0, 0
    sleep_change_ipaddr = 0



def random_numbers_with_sum(numbers_len, numbers_sum, numbers_dev=0.25, sum_error_max=0.005):
    """
    generate a list of N random integers
    where the sum of all integers is about S
    plusminus a small error
    """
    numbers_avg = numbers_sum / numbers_len
    numbers_min = round((1 - numbers_dev) * numbers_avg)
    numbers_max = round((1 + numbers_dev) * numbers_avg)
    while True:
        numbers = []
        for i in range(numbers_len):
            numbers.append(random.randint(numbers_min, numbers_max))
        sum_error = abs(1 - (sum(numbers) / numbers_sum))
        if sum_error < sum_error_max:
            return numbers



sleep_each_times = None

def get_sleep_each_time():
    # rate-limiting by cloudflare after 33...35 requests is not appeased by waiting
    return 0
    # no effect on rate-limiting
    return random.randint(0, 5)
    #return random.randint(0, 10) # debug
    global sleep_each_times
    if not sleep_each_times:
        # 24 hours
        #sleep_each_times = random_numbers_with_sum(max_downloads_per_day, (24 * 60 * 60))
        # 6 hours: use less memory for sleep_each_times
        sleep_each_times = random_numbers_with_sum(round(max_downloads_per_day / 4), (6 * 60 * 60))
    return sleep_each_times.pop()



try:
    from fetch_subs_secrets import fritzbox_login
except ImportError:
    fritzbox_login = None



# too complex
# seems to require config on fritzbox to "permit access for applications"
#from change_ipaddr_fritzbox import change_ipaddr_fritzbox
# -> just use selenium



async def change_ipaddr():
    raise ValueError("missing config for change_ipaddr. hint: fritzbox_login")
    #return change_ipaddr_fritzbox()



def change_ipaddr_openwrt():
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



async def change_ipsubnet():
    def get_subnet(ipaddr):
        return ".".join(ipaddr.split(".")[0:3])
    first_ipaddr = None
    while True:
        old_ipaddr, new_ipaddr = await change_ipaddr()
        if not first_ipaddr:
            first_ipaddr = old_ipaddr
        old_subnet = get_subnet(old_ipaddr)
        new_subnet = get_subnet(new_ipaddr)
        if old_subnet != new_subnet:
            logger_print(f"changed IP subnet from {first_ipaddr} to {new_ipaddr}")
            return first_ipaddr, new_ipaddr



# https://httpbin.org/headers
default_request_headers = {
    # no. this causes 403 Forbidden
    #"Host": "httpbin.org", 
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7", 
    "Accept-Encoding": "gzip, deflate, br", 
    "Accept-Language": "en-US,en;q=0.9", 
    "Sec-Ch-Ua": "\"Chromium\";v=\"117\", \"Not;A=Brand\";v=\"8\"", 
    "Sec-Ch-Ua-Mobile": "?0", 
    "Sec-Ch-Ua-Platform": "\"Linux\"", 
    "Sec-Fetch-Dest": "document", 
    "Sec-Fetch-Mode": "navigate", 
    "Sec-Fetch-Site": "none", 
    "Sec-Fetch-User": "?1", 
    "Upgrade-Insecure-Requests": "1", 
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36", 
    "X-Amzn-Trace-Id": "Root=1-658de9bb-6238dcc34a49bbcf6ac4cd58",
}



def random_request_headers():
    global user_agents
    user_agent = random.choice(user_agents)
    return {
        **default_request_headers,
        "User-Agent": user_agent,
    }



def new_requests_session():
    requests_session = requests.Session()
    requests_session.headers = random_request_headers()
    return requests_session



# based on https://stackoverflow.com/a/36077430/10440128
import inspect
async def asyncify(res):
    """
        mix sync and async code.
        f can be sync or async:
        res = await asyncify(f())
    """
    if inspect.isawaitable(res):
        res = await res
    return res



async def fetch_num(num, aiohttp_session, semaphore, dt_download_list, t2_download_list, html_errors, config):

    global remote_socks5_proxy_data_list
    #global num_requests_done
    #global num_requests_done_ok
    global downloads_since_change_ipaddr
    global first_download_quota
    global last_download_quota
    global last_download_quota_bak

    result_dict = {
        "num": num
    }

    logger.debug(f"{num} semaphore value: {semaphore._value}")
    logger.debug(f"{num} semaphore locked: {semaphore.locked()}")

    logger.debug(f"{num} semaphore acquire ...")
    async with semaphore: # limit parallel downloads

        logger.debug(f"{num} semaphore acquire done")

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
        # TODO why was i using http? to make it work with proxies?
        # for the "chromium" scraper, we want https to make our requests look normal
        #url = f"http://dl.opensubtitles.org/en/download/sub/{num}"
        # NOTE we also need a cookie for dl.opensubtitles.org
        url = f"https://dl.opensubtitles.org/en/download/sub/{num}"

        proxies = {}
        requests_get_kwargs = {}
        content_type = None
        response_status = None
        content_disposition = None
        response_headers = None
        response_content = None # string or bytes or StringIO or BytesIO
        response_text = None # string

        async def response_cleanup_noop():
            return
        response_cleanup = response_cleanup_noop

        # fetch sub

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
                response = await aiohttp_session.get(url)
            except (
                #requests.exceptions.ProxyError,
                asyncio.exceptions.TimeoutError,
            ) as err:
                # requests.exceptions.ProxyError: HTTPSConnectionPool(host='dl.opensubtitles.org', port=443): Max retries exceeded with url: /en/download/sub/9188285 (Caused by ProxyError('Cannot connect to proxy.', NewConnectionError('<urllib3.connection.HTTPSConnection object at 0x7fa473cadcf0>: Failed to establish a new connection: [Errno -3] Temporary failure in name resolution')))
                logger_print(f"{num} retry. error: {err}")
                result_dict["retry"] = True
                return result_dict
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

            response_data_file = f"{new_subs_dir}/{num}.scrapfly.json"
            if os.path.exists(response_data_file):
                # read cache to resume after error
                logger.debug(f"{num} reading response from cache {response_data_file}")
                with open(response_data_file) as f:
                    response_content = f.read()
                response_data = json.loads(response_content)
                response = None
            else:
                # fetch
                # TODO aiohttp
                response = requests.get(url, **requests_get_kwargs)
                response_data = json.loads(response.content)
                if proxy_scrapfly_io_cache_response:
                    # write cache to resume after error
                    response_data_file = f"{new_subs_dir}/{num}.scrapfly.json"
                    logger.debug(f"{num} writing response to cache {response_data_file}")
                    with open(response_data_file, "wb") as f:
                        f.write(response.content)

            async def response_cleanup_scrapfly():
                # delete cache after success
                #logger.debug(f"{num} response_cleanup_scrapfly")
                if os.path.exists(response_data_file):
                    logger.debug(f"{num} response_cleanup_scrapfly: deleting cache {response_data_file}")
                    os.unlink(response_data_file)
            #logger.debug(f"{num} response_cleanup = response_cleanup_scrapfly")
            response_cleanup = response_cleanup_scrapfly

            response_status = response_data["result"]["status_code"]

            if (
                response_data["result"]["success"] == False and
                response_status != 404
            ):
                logger_print(f"""{num} success: False. reason: {response_data["result"]["reason"]}""")

            # TODO type error: response.result.response_headers must be array
            response_headers = requests.structures.CaseInsensitiveDict(response_data["result"]["response_headers"])

            content_type = response_data["result"]["content_type"]

            if response_data["result"]["format"] == "text":
                response_content = response_data["result"]["content"]
                response_text = response_content
            elif response_data["result"]["format"] == "binary":
                response_content = base64.b64decode(response_data["result"]["content"])
            else:
                raise Exception(f"""unknown result format: {response_data["result"]["format"]}""")

            #logger_print(f"{num} response_status: {response_status}")
            #logger_print(f"{num} headers: {response_headers}")
            #logger_print(f"{num} proxy pool: {response_data['context']['proxy']['pool']}")

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

            # same interface as aiohttp
            #response = await aiohttp_chromium_session.get(url)
            # TODO retry loop
            try:
                response = await aiohttp_chromium_session.get(url)
            except asyncio.exceptions.TimeoutError as e:
                logger_print(f"main_scraper: aiohttp_chromium_session.get({url}) -> TimeoutError {e}")
                #raise # TODO why?
                # FIXME session.get hangs at aiohttp_chromium.client DEBUG _request: response_queue.get
                # https://dl.opensubtitles.org/en/download/sub/5159833
                # redirect to error page
                # https://www.opensubtitles.org/en/msg-dmca
                # Requested page was blocked in response to a complaint we received under the DMCA, you can read more at ChillingEffects.org
                # FIXME the scraper tab is not marked as "old" and reused
                # FIXME visit some html page before starting downloads, and then every 40 downloads
                # fix? requests just hang forever, always timeout. blame server? busy with backup?
                logger_print(f"main_scraper: aiohttp_chromium_session.get -> TimeoutError {e} -> retrying")
                # FIXME close old tab on TimeoutError
                result_dict["retry"] = True
                return result_dict
                #await asyncio.sleep(retry_sleep_seconds)
                #continue

            async def response_cleanup_chromium():
                await response.__aexit__(None, None, None)
            response_cleanup = response_cleanup_chromium
            # TODO session_cleanup

            """
            response_status = response.status
            response_type = response.headers.get("Content-Type")
            # TODO response_headers?
            # TODO handle binary response
            response_text = await response.text()
            """

        #elif options.proxy_provider == "chromium":
        elif False:

            # TODO handle captchas by cloudflare.
            # effectively, implement a semiautomatic web scraper
            # which asks for help from the user to solve captchas
            # see also docs/captchas.md

            # FIXME we are not blocked by /en/search/sublanguageid-all
            # but as soon as we start scraping subs, we are blocked
            # TODO send some referrer url in request headers?

            # call get_response___chromium
            logger_print(f"fetch_num: calling aiohttp_chromium_session.get_response({repr(url)})")

            response = await aiohttp_chromium_session.get_response(
                url,
                #timeout=5*60,
                #return_har_path=True, # debug
                # no help?
                #referrer="https://www.opensubtitles.org/en/search/sublanguageid-all",
            )

            # no. handle this later
            if False and response.content_is_file:
                # read the file into memory
                # this works because the files are small
                # (tempfiles are stored in tmpfs anyway...)
                response_content = response.content.read()
                response.delete_content_file() # TODO implement

            # no. all this is already handled by the generic code, see below
            if False:
                #logger_print(f"TODO debug har file: {response.har_path}")
                response_status = response.status
                response_headers = response.headers
                response_type = response.headers.get("Content-Type")
                response_content = response.content

                # TODO handle binary response
                #response_text = await response.text()

                logger_print("response_status", response_status)
                logger_print("response_type", response_type)
                #logger_print("response_text", repr(response_text)[0:100] + " ...")

                # TODO implement response.is_file
                if response.is_file:
                    filename = response.content_filename
                    # only prepend num
                    # risk: this can exceed the maximum filename length of 255 bytes
                    new_filename = f"{num}.{filename}"
                    parsed_filename = re.match(r"(.*)\.\(([0-9]+)\)\.zip", filename)
                    if parsed_filename:
                        # move num from end to start of filename
                        # moving num is needed to stay below the maximum filename length of 255 bytes
                        prefix, num_str = parsed_filename.groups()
                        if num_str == str(num):
                            new_filename = f"{num}.{prefix}.zip"
                        else:
                            logger_print(f"{num}: warning: sub number mismatch between url and filename")
                    output_path = f"{new_subs_dir}/{new_filename}"
                    logger_print(f"{num} writing", output_path)
                    response.move_to(output_path)
                else:
                    logger_print(f"{num} response.content:", response.content)
                    raise NotImplementedError("response is not a file")

                #logger.debug("headers: " + repr(dict(headers)))
                #sleep_each = random.randint(sleep_each_min, sleep_each_max)
                sleep_each = get_sleep_each_time()
                if sleep_each > 0:
                    logger_print(f"{num} 200 dt={dt_download:.3f} dt_avg={dt_download_avg:.3f}{dt_par_str} -> waiting {sleep_each} seconds")
                else:
                    logger_print(f"{num} 200 dt={dt_download:.3f} dt_avg={dt_download_avg:.3f}{dt_par_str}")
                #if dt_download_avg_parallel > 1:
                #    logger_print(f"460: {num} 200 dt_download_avg_parallel > 1: dt_download_list_parallel = {dt_download_list_parallel}")
                logger.debug(f"{num} sleep {sleep_each} ...")
                await asyncio.sleep(sleep_each)
                logger.debug(f"{num} sleep {sleep_each} done")
                #continue
                result_dict["ok"] = True
                return result_dict

        elif options.proxy_provider == "pyppeteer":
            logger_print("pyppeteer_page.goto", url)
            await pyppeteer_page.goto(url)
            raise NotImplementedError

        elif options.proxy_provider == "free-proxies":
            # TODO try many proxies in parallel
            socks5_proxy = random.choice(remote_socks5_proxy_data_list)[0]
            try:
                # https://stackoverflow.com/a/76656557/10440128
                connector = aiohttp_socks.ProxyConnector.from_url(
                    url=f"socks5://{socks5_proxy}",
                    # send DNS requests over proxy. aka "socks5h"
                    rdns=True,
                )
                # create new session for every request to disable connection pooling
                # https://github.com/romis2012/aiohttp-socks/issues/31
                async with aiohttp.ClientSession(connector=connector) as session:
                    # based on "no proxy"
                    response = await session.get(
                        url,
                        timeout=15,
                        headers=random_request_headers(),
                    )
                response_status = response.status
                response_type = response.headers.get("Content-Type")
                logger.info(f"{num} proxy {socks5_proxy} ok? status={response_status} type={response_type}")
                # TODO response_headers?
                # TODO handle binary response
                # NOTE response.text() can raise TimeoutError
                response_text = await response.text()
            except asyncio.exceptions.TimeoutError:
                logger.info(f"{num} proxy timeout")
                result_dict["retry"] = True
                return result_dict
            except Exception as e:
                logger.info(f"{num} proxy {socks5_proxy} error: {e}")
                result_dict["retry"] = True
                return result_dict

        elif False:

            # aiohttp: debug cookies

            logger_print(f"aiohttp_session.cookie_jar._cookies httpbin.dev /cookies:\n" + str(aiohttp_session.cookie_jar._cookies[("httpbin.dev", "/cookies")]))

            # debug: set cookies
            #url = "http://httpbin.dev/cookies/set?foo=bar"
            url = "http://httpbin.dev/cookies/set?foo=bar&a=1&b=2"
            response = await aiohttp_session.get(url)
            logger.debug(f"{num} response.request_info.headers: {dir(response.request_info.headers)}")
            response_text = (await response.content.read()).decode("utf8")
            #logger.info(f"{num} response_text: {response_text}")
            # Set-Cookie headers are not here
            #logger.info(f"{num} response.headers: {response.headers}")

            logger_print(f"aiohttp_session.cookie_jar._cookies httpbin.dev /cookies:\n" + str(aiohttp_session.cookie_jar._cookies[("httpbin.dev", "/cookies")]))

            # debug: get cookies
            """
            #url = "https://httpbin.org/headers"
            url = "https://httpbin.dev/headers"
            response = await aiohttp_session.get(url)
            logger.info(f"{num} response.request_info.headers: {response.request_info.headers}")
            response_status = response.status
            # TODO debug request headers
            #logger.info(f"{num} response dir: {dir(response)}")
            logger.info(f"{num} response_status: {response_status}")
            # Set-Cookie headers are not here
            #logger.info(f"{num} headers: {response.headers}")
            response_content = response.content
            response_text = (await response_content.read()).decode("utf8")
            response_data = json.loads(response_text)
            cookies_header = response_data["headers"].get("Cookie")
            logger.info(f"{num} cookies_header: {cookies_header}")
            """

            url_base = "http://httpbin.dev"
            #url_base = "https://httpbin.dev"

            # NOTE cookies are not returned by /headers
            url = f"{url_base}/headers"
            response = await aiohttp_session.get(url, **get_kwargs)

            logger.debug(f"response.request_info.headers.Cookie: {response.request_info.headers.get('Cookie')}")
            #print(f"response.request_info dir: {dir(response.request_info)}")

            response_status = response.status
            # TODO debug request headers
            #print(f"response dir: {dir(response)}")
            #print(f"response_status: {response_status}")

            # Set-Cookie headers are not here
            #print(f"headers: {response.headers}")

            response_content = response.content
            response_text = (await response_content.read()).decode("utf8")
            logger.debug(f"sent headers: {response_text}")



            # debug: get cookies
            url = f"{url_base}/cookies"
            response = await aiohttp_session.get(url, **get_kwargs)

            logger.debug(f"response.request_info.headers.Cookie: {response.request_info.headers.get('Cookie')}")
            #print(f"response.request_info dir: {dir(response.request_info)}")

            response_status = response.status
            # TODO debug request headers
            #print(f"response dir: {dir(response)}")
            #print(f"response_status: {response_status}")

            # Set-Cookie headers are not here
            #print(f"headers: {response.headers}")

            response_content = response.content
            response_text = (await response_content.read()).decode("utf8")
            print(f"sent cookies: {response_text}")

            logger_print(f"aiohttp_session.cookie_jar._cookies httpbin.dev /cookies:\n" + str(aiohttp_session.cookie_jar._cookies[("httpbin.dev", "/cookies")]))

            logger_print(f"saving cookies to {opensubtitles_org_login_cookies_txt_path}")
            aiohttp_session.cookie_jar.save(opensubtitles_org_login_cookies_txt_path)

            raise NotImplementedError

        elif options.proxy_provider == None:
            # no proxy
            # requests
            #response = requests.get(url, **requests_get_kwargs)
            #response_status = response.response_status

            # aiohttp
            # FIXME aiohttp does not send cookies?!
            # TODO also send a Referer header - no, still blocked
            response = await aiohttp_session.get(url, headers={
                #"Referer": "https://www.opensubtitles.org/en/search/sublanguageid",
            })
            logger.debug(f"{num} response.request_info.headers: {json.dumps(dict(response.request_info.headers), indent=2)}")
            logger.debug(f"{num} response.request_info.headers.Cookie: {response.request_info.headers.get('Cookie')}")
            response_status = response.status
            logger.debug(f"{num} response.status: {response.status}")
            logger.debug(f"{num} response.headers: {json.dumps(dict(response.headers), indent=2)}")

        else:
            raise NotImplementedError(f"options.proxy_provider {options.proxy_provider}")

        #logger_print("dir response", dir(response))

        response_status = response_status or response.status
        response_content = response_content or response.content
        response_headers = response_headers or response.headers

        content_type = content_type or response_headers.get("Content-Type")

        #num_requests_done += 1

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
        #debug_headers_str += f" type={response.headers.get('Content-Type')}"
        debug_headers_str += f" type={response_headers.get('Content-Type')}"
        # dynamic: 200 -> 0
        # but rate-limiting blocks after 30...35 requests -> http 429 Too Many Requests
        download_quota = response_headers.get("download-quota", None)
        if download_quota != None:
            download_quota = int(download_quota)
            if first_download_quota == None:
                first_download_quota = download_quota
            last_download_quota_bak = last_download_quota # backup copy
            last_download_quota = download_quota
        # TODO check download_quota versus daily_quota
        debug_headers_str += f" quota={download_quota}"
        # always 40
        #debug_headers_str += f" ratelimit={response.headers.get('X-RateLimit-Remaining')}"
        #debug_headers_str += f" headers={json.dumps(dict(response.headers), indent=2)}"

        #if response_status == 200 and content_type.startswith("text/html"):
        if response_status != 200 or content_type.startswith("text/html"):

            # TODO handle decode errors
            response_text = response_text or (await asyncify(response_content.read())).decode("utf8")

            found_error = False

            if response_status in {503, 520}:
                # example: Error 503 Backend fetch failed
                # example: Error 520 Web server is returning an unknown error
                # 2024-02-14 14:25:23,771 fetch-subs INFO 9792438 503 dt=0.533 dt_avg=4.339 type=text/html; charset=utf-8 quota=None
                # FIXME close tab / mark tab as "old"
                found_error = True
                result_dict["wait"] = True
                result_dict["retry"] = True
                logger_print(f"status {response_status} -> sleep 30")
                await asyncio.sleep(30)

            if not found_error:
                # These subtitles were disabled, you should not use them
                error_source = "These subtitles were <b>disabled</b>, you should not use them"
                if error_source in response_text:
                    found_error = True
                    #logger_print(f"{num} status={response_status} subtitles were disabled -> not found")
                    result_dict["not_found"] = True
                    logger_print(f"{num} status={response_status} error={repr(error_source)} -> result={result_dict}")
                    response_status = 404

            if not found_error:
                error_source = "<pre>Site will be online soon. We are doing some necessary backups and upgrades. Thanks for understanding."
                if error_source in response_text:
                    found_error = True
                    #logger_print(f"{num} status={response_status} website is doing backups and upgrades -> wait and retry")
                    #await verbose_sleep(10*60, 1*60) # wait 10 minutes
                    result_dict["wait"] = True
                    result_dict["retry"] = True
                    logger_print(f"{num} status={response_status} error={repr(error_source)} -> result={result_dict}")
                    response_status = 500 # internal server error

            if not found_error:
                error_source = "Sorry. We have problem with network connection to database server, try reload page."
                if error_source in response_text:
                    found_error = True
                    result_dict["wait"] = True
                    result_dict["retry"] = True
                    response_status = 500 # internal server error

            if not found_error:
                error_source = " subtitle file doesnt exists, you can contact admin GetSubtitleContents()"
                if error_source in response_text:
                    found_error = True
                    result_dict["not_found"] = True
                    logger_print(f"{num} status={response_status} error={repr(error_source)} -> result={result_dict}")

            # <div class="msg error">[CRITICAL ERROR] <b>Subtitle files for 7269303 was not found in database</b></div>
            if not found_error:
                error_source = '<div class="msg error">[CRITICAL ERROR] <b>Subtitle files for'
                if error_source in response_text:
                    found_error = True
                    result_dict["not_found"] = True
                    logger_print(f"{num} status={response_status} error={repr(error_source)} -> result={result_dict}")

            # <div class="msg error">[CRITICAL ERROR] Subtitle id 9758131 <b>was not found in database</b></div>
            if not found_error:
                error_source = '<div class="msg error">[CRITICAL ERROR] Subtitle id '
                if error_source in response_text:
                    found_error = True
                    result_dict["not_found"] = True
                    logger_print(f"{num} status={response_status} error={repr(error_source)} -> result={result_dict}")

            if not found_error:
                # These subtitles were disabled, you should not use them
                error_source = "These subtitles were <b>disabled</b>, you should not use them"
                if error_source in response_text:
                    found_error = True
                    result_dict["not_found"] = True
                    logger_print(f"{num} status={response_status} error={repr(error_source)} -> result={result_dict}")

            if not found_error:
                error_source = ">Requested page was blocked in response to a complaint we received under the DMCA,"
                if error_source in response_text:
                    found_error = True
                    #filename_notfound = f"{new_subs_dir}/{num}.not-found-dmca" # verbose format
                    filename_notfound = f"{new_subs_dir}/{num}.dmca"
                    result_dict["not_found"] = True
                    result_dict["dmca"] = True
                    logger_print(f"{num} status={response_status} error={repr(error_source)} -> result={result_dict}")

            # FIXME handle error
            if not found_error:
                # Sorry, maximum download count for IP: <b>123.123.123.123</b> exceeded.
                error_source = "Sorry, maximum download count for IP"
                if error_source in response_text:
                    found_error = True
                    logger_print(f"{num} status={response_status} error={repr(error_source)} -> result={result_dict}")
                    logger_print(f"FIXME too many requests. wait and/or change_ipaddr")
                    raise SystemExit
                    # TODO loop accounts: use next account for opensubtitles.org
                    # change_ipaddr?
                    # no. the rate-limiting is linked to my account
                    # so change_ipaddr only helps
                    # if i continue scraping without login = without cookies
                    await asyncio.sleep(99999999)

            # FIXME handle error
            if not found_error:
                error_source = "<b>Please confirm you are not robot.</b>"
                if error_source in response_text:
                    found_error = True
                    logger_print(f"{num} status={response_status} error={repr(error_source)} -> result={result_dict}")
                    logger_print(f"FIXME too many requests. wait and/or change_ipaddr")
                    await asyncio.sleep(99999999)

            # create empty file
            logger.debug(f"{num} creating empty not-found file {filename_notfound}")
            open(filename_notfound, 'a').close()

            #debug_404_pages = True
            #if debug_404_pages:
            if not found_error:
                # FIXME these files are empty
                debug_path = f"{filename_notfound}.html"
                #response_text = (await asyncify(response_content.read())).decode("utf8")
                logger_print(f"{num} writing {debug_path}")
                with open(debug_path, 'w') as f:
                    f.write(response_text)
                if False:
                    f.write('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">\n')
                    f.write("<!-- response headers:\n")
                    # FIXME TypeError: 'ClientResponseHeaders' object is not iterable
                    for key in response_headers:
                        f.write(f"{key}: {response_headers[key]}\n")
                    f.write("-->\n")
                    f.write(response_text)

            if not found_error:
                # FIXME handle error: xxx not found in database
                logger_print(f"{num} status={response_status} error=unknown file={filename_notfound}.html")
                await asyncio.sleep(9999999)

            # finish the "response_status == 404" block
            # TODO refactor this copy-pasta

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
                # par = parallel
                dt_par_str = f" dt_par={dt_download_avg_parallel:.3f}"

            # TODO refactor
            # implement different options.proxy_provider
            # as different subclasses of a BaseScraper class

            logger_print(f"{num} {response_status} dt={dt_download:.3f} dt_avg={dt_download_avg:.3f}{dt_par_str}{debug_headers_str}")
            #if dt_download_avg_parallel > 1:
            #    logger_print(f"499: {num} 200 dt_download_avg_parallel > 1: dt_download_list_parallel = {dt_download_list_parallel}")
            #num += 1

            if response_cleanup != None and response_cleanup != response_cleanup_noop:
                logger.debug(f"{num} calling response_cleanup {response_cleanup.__name__}")
                await response_cleanup()

            return result_dict

        # debug
        #logger_print(f"options.proxy_provider: {repr(options.proxy_provider)}")

        if options.proxy_provider == None and response_status == 429:
            # rate limiting
            # this happens after 35 sequential requests
            # also failed requests are counted = http 404
            # blocking is done by cloudflare who says "ratelimit=40"
            # but actually its "ratelimit=35"
            debug_429_pages = False
            if debug_429_pages:
                response_text = (await response_content.read()).decode("utf8")
                #with open(f"{filename_notfound}.html", 'w') as f:
                debug_path = "debug-response-http-429.html"
                logger_print(f"{num} writing {debug_path}")
                with open(debug_path, "w") as f:
                    f.write('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">\n')
                    f.write("<!-- response headers:\n")
                    for key in response_headers:
                        f.write(f"{key}: {response_headers[key]}\n")
                    f.write("-->\n")
                    f.write(response_text)

            # <b>Please confirm you are not robot.</b> If you don't want to do this, please become <a href="/support#vip">VIP member</a> or log-in.
            # If you are wondering what's going on please read <a href="http://forum.opensubtitles.org/viewtopic.php?f=1&t=14559">CAPTCHA post in forum</a>
            # <h1>CAPTCHA robot test</h1>

            # http://forum.opensubtitles.org/viewtopic.php?f=1&t=14559
            # FAQ:
            # Q: Why do you introduce CAPTCHA on your website?
            # A: Because there are dozens other websites which are copying subtitles

            #logger_print(f"{num} {response_status} Too Many Requests -> waiting {sleep_blocked} seconds")
            #await asyncio.sleep(sleep_blocked)
            #logger_print(f"{num} {response_status} response_headers:\n" + json.dumps(dict(response_headers), indent=2))
            logger_print(f"{num} {response_status} Too Many Requests after {num_requests_done_ok} downloads in {num_requests_done} requests -> stopping scraper")

            # no. change_ipaddr and continue scraping
            # stop scraper. retry would cause infinite loop
            #raise SystemExit

            user_agent = random.choice(user_agents)

            await change_ipaddr()

            """
            if downloads_since_change_ipaddr == 0:
                # after too many change_ipaddr, they are blocking our subnet
                logger_print(f"{num} {response_status} Too Many Requests + no downloads -> changing IP subnet")
                # no. this takes too long and does not work,
                # because our user-agent is blocked
                #await change_ipsubnet()
                raise NotImplementedError("change_ipsubnet")
            else:
                logger_print(f"{num} {response_status} Too Many Requests -> changing IP address")
                await change_ipaddr()
            """

            # FIXME keep these numbers
            """
            logger_print(f"resetting num_requests_done_ok from {num_requests_done_ok} to 0")
            num_requests_done_ok = 0

            logger_print(f"resetting num_requests_done from {num_requests_done} to 0")
            num_requests_done = 0
            """

            downloads_since_change_ipaddr = 0
            # fix: http.client.RemoteDisconnected: Remote end closed connection without response
            # TODO aiohttp
            #aiohttp_session.user_agent = "..."
            #aiohttp_session.cookies = []
            requests_session = new_requests_session()
            t_sleep = random.randrange(sleep_change_ipaddr_min, sleep_change_ipaddr_max)
            logger_print(f"pausing scraper for {t_sleep} seconds")
            #time.sleep(t_sleep)
            await verbose_sleep(t_sleep, 60)

            #logger_print("changing ipaddr again before continuing with scraping")
            #await change_ipaddr()

            await response_cleanup()
            #await session_cleanup() # TODO

            #result_dict["ok"] = True
            result_dict["retry"] = True
            return result_dict

        if response_status == 500:
            logger_print(f"{num} {response_status} Internal Server Error -> retry")
            await response_cleanup()
            #await session_cleanup() # TODO
            result_dict["retry"] = True
            result_dict["pause"] = True
            logger_print(f"{num} {response_status} sleep 30"); await asyncio.sleep(30)
            return result_dict

        if response_status == 520:
            logger_print(f"{num} {response_status} Web server is returning an unknown error -> retry")
            await response_cleanup()
            #await session_cleanup() # TODO
            result_dict["retry"] = True
            result_dict["pause"] = True
            logger_print(f"{num} {response_status} sleep 30"); await asyncio.sleep(30)
            return result_dict

        if response_status == 429:
            # blocked. too many requests
            # FIXME we are not blocked by /en/search/sublanguageid-all
            # but as soon as we start scraping subs, we are blocked
            # TODO send some referrer url in request headers?
            if False and content_type == "text/html; charset=UTF-8":
                # captcha page
                # bug in proxy provider
                logger_print(f"{num} {response_status} captcha -> retry")
                await response_cleanup()
                #await session_cleanup() # TODO
                result_dict["retry"] = True
                return result_dict
            if options.proxy_provider == "chromium":
                if aiohttp_chromium_session.backend_type == "flaresolverr":
                    logger_print(f"{num} {response_status} blocked -> start a new session")
                    aiohttp_chromium_session.flaresolverr_requests_remain = 0

            """
            # write the error page to disk
            response_text = (await response_content.read()).decode("utf8")
            content_type = content_type or response_headers.get("Content-Type")
            error_filename = f"http-429-at-num-{num}.html"
            logger_print(f"{num} {response_status} response_headers", response_headers)
            logger_print(f"{num} {response_status} content_type={repr(content_type)} + response_text in {error_filename} -> retry")
            with open(error_filename, "w") as f:
                f.write(response_text)
            """
            #sleep_each = random.randint(sleep_each_min, sleep_each_max)
            sleep_each = get_sleep_each_time()
            logger.debug(f"{num} sleep {sleep_each} ...")
            await asyncio.sleep(sleep_each)
            logger.debug(f"{num} sleep {sleep_each} done")
            await response_cleanup()
            #await session_cleanup() # TODO
            result_dict["retry"] = True
            return result_dict

        if response_status in {422, 403, 503}:
            response_text = (await response_content.read()).decode("utf8")
            logger_print(f"{num} {response_status} response_text: {repr(response_text)}")
            if response_text == "":
                # json.loads -> json.decoder.JSONDecodeError Expecting value
                logger_print(f"{num} {response_status} got empty response_text -> retry")
                await response_cleanup()
                #await session_cleanup() # TODO
                result_dict["retry"] = True
                return result_dict
            error_source = "<pre>Site will be online soon. We are doing some necessary backups and upgrades. Thanks for understanding."
            if error_source in response_text:
                logger_print(f"{num} {response_status} website is doing backups and upgrades -> wait and retry")
                await verbose_sleep(10*60, 1*60) # wait 10 minutes
                await response_cleanup()
                #await session_cleanup() # TODO
                result_dict["retry"] = True
                return result_dict
            error_source = "Sorry. We have problem with network connection to database server, try reload page."
            if error_source in response_text:
                logger_print(f"{num} {response_status} problem with network connection to database server -> wait and retry")
                await verbose_sleep(60, 10) # wait 1 minute
                await response_cleanup()
                #await session_cleanup() # TODO
                result_dict["retry"] = True
                return result_dict
            # 2023-12-28 22:37:03,711 fetch-subs INFO 9756769 403 response_text: '<html>\r\n<head><title>403 Forbidden</title></head>\r\n<body>\r\n<center><h1>403 Forbidden</h1></center>\r\n<hr><center>cloudflare</center>\r\n</body>\r\n</html>\r\n<!-- a padding to disable MSIE and Chrome friendly error page -->\r\n<!-- a padding to disable MSIE and Chrome friendly error page -->\r\n<!-- a padding to disable MSIE and Chrome friendly error page -->\r\n<!-- a padding to disable MSIE and Chrome friendly error page -->\r\n<!-- a padding to disable MSIE and Chrome friendly error page -->\r\n<!-- a padding to disable MSIE and Chrome friendly error page -->\r\n'
            try:
                response_data = json.loads(response_text)
            except json.JSONDecodeError:
                response_data = dict()
            if response_data.get("code") == "RESP001":
                # Could not get content. try enabling javascript rendering for a higher success rate (RESP001)
                #config.zenrows_com_js = True
                #config.zenrows_com_antibot = True
                #logger_print(f"{num} retry. error: need javascript")
                logger_print(f"{num} 404 dmca")
                # create empty file
                filename_dcma = f"{new_subs_dir}/{num}.dmca"
                open(filename_dcma, 'a').close() # create empty file
                await response_cleanup()
                #await session_cleanup() # TODO
                result_dict["ok"] = True
                return result_dict
            if response_data.get("code") == "AUTH006":
                # The concurrency limit was reached. Please upgrade to a higher plan or ...
                logger_print(f"{num} {response_status} retry. error: concurrency limit was reached @ {response_text}")
                await response_cleanup()
                #await session_cleanup() # TODO
                # pause scraper, retry
                result_dict["retry"] = True
                result_dict["pause"] = True
                logger_print(f"{num} {response_status} sleep 30"); await asyncio.sleep(30)
                return result_dict
            if response_data.get("code") == "BLK0001":
                # Your IP address has been blocked for exceeding the maximum error rate ...
                logger_print(f"{num} {response_status} retry. error: IP address was blocked @ {response_text}")
                await response_cleanup()
                #await session_cleanup() # TODO
                # pause scraper, change IP address, retry
                result_dict["retry"] = True
                result_dict["pause"] = True
                result_dict["change_ipaddr"] = True
                logger_print(f"{num} {response_status} sleep 30"); await asyncio.sleep(30)
                return result_dict
            if response_data.get("code") == "CTX0002":
                # Operation timeout exceeded (CTX0002)
                await response_cleanup()
                #await session_cleanup() # TODO
                # pause scraper, retry
                result_dict["retry"] = True
                result_dict["pause"] = True
                logger_print(f"{num} {response_status} sleep 30"); await asyncio.sleep(30)
                return result_dict
            logger_print(f"{num} {response_status} retry. headers: {response_headers}. response_text: {response_text}")
            # example:
            # response_text: '<!DOCTYPE html>\n<html>\n<head>\n<title>503 Backend fetch failed</title>\n</head>\n<body>\n<h1>Error 503 Backend fetch failed</h1>\n<p>Backend fetch failed</p>\n<h3>Guru Meditation:</h3>\n<p>XID: 408454847</p>\n<hr>\n<p>Varnish cache server</p>\n</body>\n</html>\n'
            #raise SystemExit # stop scraper
            await response_cleanup()
            #await session_cleanup() # TODO
            result_dict["retry"] = True
            result_dict["pause"] = True
            logger_print(f"{num} {response_status} sleep 30"); await asyncio.sleep(30)
            return result_dict
        downloads_since_change_ipaddr += 1

        response_content_str_or_bytes = None

        logger_print("response_content read ...")
        # FIXME file download progress is not visible
        # downloadProgress events?
        # TODO open chrome://downloads/ in first tab

        if hasattr(response, "_filepath") and response._filepath != None:
            # aiohttp_chromium
            logger_print(f"response._filepath = {repr(response._filepath)}")
            # FIXME wait until response is complete
            # FIXME this can hang. TODO timeout + retry
            logger_print("response._wait_complete ...")
            t1 = time.time()
            try:
                await response._wait_complete(timeout=2*60)
            except TimeoutError:
                await response_cleanup()
                raise Exception(f"{num} download failed")
            t2 = time.time()
            logger_print("response._wait_complete done after {(t2 - t1):.3f} seconds")
            # TODO move response._filepath to output path
            logger_print("response._filepath open")
            with open(response._filepath, "rb") as f:
                logger_print("response._filepath read")
                response_content_str_or_bytes = f.read()
            logger_print("response._filepath unlink")
            os.unlink(response._filepath)
        elif type(response_content) in {str, bytes}:
            # requests
            logger_print("response_content_str_or_bytes = response_content")
            response_content_str_or_bytes = response_content
        elif type(response_content) in {_io.TextIOWrapper, _io.BufferedReader}:
            # aiohttp_chromium.ClientSession.Response
            # FIXME scraper can hang after: ClientResponse.content: done
            logger_print("response_content.read() ...")
            response_content_str_or_bytes = response_content.read()
            logger_print("response_content.read() done")
        # TODO require type of aiohttp response object
        elif hasattr(response_content, "read"):
            # aiohttp
            #response_content_str_or_bytes = await response_content.read()
            # FIXME scraper can hang after: ClientResponse.content: done
            logger_print("response_content.read() ...")
            response_content_str_or_bytes = response_content.read()
            logger_print("response_content.read() done")
            if inspect.isawaitable(response_content_str_or_bytes):
                logger_print("response_content.read() await ...")
                response_content_str_or_bytes = await response_content_str_or_bytes
                logger_print("response_content.read() await done")
        else:
            await response_cleanup()
            #await session_cleanup() # TODO
            raise NotImplementedError(f"read response_content object of type {type(response_content)}")

        logger_print("response_content read done")

        if response_status != 200:
            await response_cleanup()
            #await session_cleanup() # TODO
            raise Exception(f"{num} unexpected response_status {response_status}. headers: {response_headers}. content: {response_content_str_or_bytes}")

        if False:
            # debug
            logger_print(f"{num} content_type:", content_type)
            logger_print(f"{num} response.headers Content-Type:", response.headers.get("Content-Type"))
            # this works only with my custom "class Headers"
            logger_print(f"{num} response.headers.headers:", response.headers.headers)
            logger_print(f"{num} response.content:", response.content)

        # FIXME detect captcha
        # see also docs/captchas.md

        if content_type != "application/zip":

            # FIXME response 200: 1954265422 subtitle file doesnt exists, you can contact admin GetSubtitleContents()
            # from url https://dl.opensubtitles.org/en/download/sub/5687213
            # note: 1954265422 != 5687213

            # FIXME not printed
            logger_print(f"{num} content_type:", content_type)

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
                await response_cleanup()
                #await session_cleanup() # TODO
                raise NotImplementedError(f"{num}: unknown Content-Type: {content_type}")

        #logger_print(f"{num} response", dir(response))
        #logger_print(f"{num} response_headers", response_headers)
        # 'Zr-Content-Disposition': 'attachment; filename="nana.s01.e14.family.restaurant.of.shambles.(2006).ita.1cd.(9181475).zip"'
        content_disposition = content_disposition or response_headers.get("Content-Disposition")
        logger_print(f"{num} content_disposition:", content_disposition)

        if content_disposition:
            # parse filename from the Content-Disposition header
            # https://stackoverflow.com/a/73418983/10440128

            #content_filename = pyrfc6266.parse_filename(content_disposition)

            value, params = pyrfc6266.parse(content_disposition)
            if value != "attachment":
                await response_cleanup()
                #await session_cleanup() # TODO
                raise NotImplementedError(f"FIXME handle non-attachment content_disposition {repr(content_disposition)}")

            content_filename = next(map(lambda p: p.value, filter(lambda p: p.name == "filename", params)), None)
            if content_filename == None:
                await response_cleanup()
                #await session_cleanup() # TODO
                raise NotImplementedError(f"FIXME handle missing filename in content_disposition {repr(content_disposition)}")

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
            # TODO
            #await response_cleanup()
            #await session_cleanup() # TODO
            assert filename.endswith(suffix), f"num mismatch between url and filename. num: {num}, filename: {filename}"
            filename = filename[0:(-1 * len(suffix))] + ".zip"
        else:
            # file basename is f"{num}.zip"
            #logger_print(f"{num} FIXME missing filename? response_headers", response_headers)
            pass

        logger_print(f"{num} filename", filename)

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
        if type(response_content_str_or_bytes) == str:
            file_open_mode = "w"

        logger_print(f"writing {filename}")

        with open(filename_tmp, file_open_mode) as f:
            f.write(response_content_str_or_bytes)

        # TODO rename filename to output_file_path
        shutil.move(filename_tmp, filename)

        if filename.endswith(".html"):
            # FIXME 1954265422 subtitle file doesnt exists, you can contact admin GetSubtitleContents()
            # -> {num}.not-found"
            # FIXME solve captcha
            # <b>Please confirm you are not robot.</b>
            # <h1>CAPTCHA robot test</h1>
            html_errors.append(True)
            html_error_probability = sum(map(lambda _: 1, filter(lambda x: x == True, html_errors))) / len(html_errors)
            logger_print(f"{num} retry. error: html filename={repr(filename)} p={html_error_probability * 100:.2f}%")
            await response_cleanup()
            #await session_cleanup() # TODO
            result_dict["retry"] = True
            return result_dict
        else:
           html_errors.append(False)

        logger_print(f"response_cleanup() ...")
        await response_cleanup()
        #await session_cleanup() # TODO
        logger_print(f"response_cleanup() done")

        # cleanup
        # aiohttp_chromium.ClientSession.Response.__del__: close and delete the tempfile
        del response


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
                shutil.move(filename, filename + ".broken")

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
        #sleep_each = random.randint(sleep_each_min, sleep_each_max)
        sleep_each = get_sleep_each_time()
        if sleep_each > 0:
            logger_print(f"{num} 200 dt={dt_download:.3f} dt_avg={dt_download_avg:.3f}{dt_par_str}{debug_headers_str} -> waiting {sleep_each} seconds")
        else:
            logger_print(f"{num} 200 dt={dt_download:.3f} dt_avg={dt_download_avg:.3f}{dt_par_str}{debug_headers_str}")
        #if dt_download_avg_parallel > 1:
        #    logger_print(f"635: {num} 200 dt_download_avg_parallel > 1: dt_download_list_parallel = {dt_download_list_parallel}")
        logger.debug(f"{num} sleep {sleep_each} ...")
        await asyncio.sleep(sleep_each)
        logger.debug(f"{num} sleep {sleep_each} done")
        #break
        #num += 1
        #num_requests_done_ok += 1
        result_dict["ok"] = True
        return result_dict

    logger.debug(f"{num} semaphore release")



# global state, shared between functions
user_agents = None
aiohttp_chromium_session = None



def random_hash():
    return hex(random.getrandbits(128))[2:]

def sha1sum(file_path=None, data=None):
    if data:
        return hashlib.sha1(data).digest()
    assert file_path
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



class Response():

    def __init__(
            self,
            status,
            headers,
            content_type,
            content_encoding,
            content_length,
            content_filename,
            content_filepath,
            content_bytes,
            har,
            har_path,
            request_number,
        ):

        # standard attributes
        # same API as requests / aiohttp / ?
        self.status = status
        self.headers = headers
        self.content = content_bytes

        # nonstandard attributes
        self.content_type = content_type
        #self._text = text
        self.content_encoding = content_encoding
        self.content_length = content_length
        self.content_filename = content_filename
        self.content_filepath = content_filepath
        self.har = har
        self.har_path = har_path
        self.request_number = request_number

        #self.content_is_file = type(self.content) in {_io.BufferedReader, _io.TextIOWrapper}

    async def text(self):
        # await response.text()
        return self.content.decode(self.content_encoding)

    def __del__(self):
        # open(file_path, "rb") -> _io.BufferedReader
        # open(file_path, "r") -> _io.TextIOWrapper
        #if self.content_is_file:
        content_is_file = type(self.content) in {_io.BufferedReader, _io.TextIOWrapper}
        if content_is_file:
            # close file handle and delete file
            # TODO check if self.content is open
            self.content.close()
            # TODO check if self.content_filepath exists
            logger_print(f"deleting tempfile {self.content_filepath}")
            os.unlink(self.content_filepath)
            # also delete the f"req{request_number}" folder
            os.rmdir(os.path.dirname(self.content_filepath))



class Headers():
    def __init__(self, headers):
        # headers from the HAR file is list of objects:
        # [ { "name": "x", "value": "y" } ]
        # transform it to a list of tuples, to save memory
        self.headers = []
        if type(headers) == list:
            if len(headers) > 0:
                if type(headers[0]) == dict:
                    if headers[0].get("name") != None and headers[0].get("value") != None:
                        self.headers = list(map(lambda h: (h["name"].lower(), h["value"]), headers))
                    else: raise NotImplementedError(f"parse headers: {repr(headers)}")
                else: raise NotImplementedError(f"parse headers: {repr(headers)}")
        elif type(headers) == dict:
            # note: this can be lossy. header keys can be duplicated
            self.headers = list(map(lambda k: (k.lower(), headers[k]), headers.keys()))
        else: raise NotImplementedError(f"parse headers: {repr(headers)}")
    def get(self, key, default=None):
        # return the first matching header
        # TODO better? how to handle duplicate keys in self.headers
        key = key.lower()
        try:
            return next(h for h in self.headers if h[0] == key)[1]
        except StopIteration: # not found
            #raise KeyError
            return default



# TODO refactor

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
    logger_print("cleanup_main ...")
    if hooks.exit_code is not None:
        logger_print("cleanup_main: death by sys.exit(%d)" % hooks.exit_code)
    elif hooks.exception is not None:
        (exc_type, exc, exc_args) = hooks.exception
        logger_print(f"cleanup_main: death by exception: {exc_type.__name__}: {exc}")
        traceback.print_exception(exc)
    else:
        logger_print("cleanup_main: natural death")

    #if True:
    if False:
        logger_print("cleanup_main: debug: hit enter to continue")
        input()

    logger_print(f'cleanup_main: aiohttp_chromium_session.close')
    if aiohttp_chromium_session:
        #await aiohttp_chromium_session.close()
        asyncio.get_event_loop().run_until_complete(
            aiohttp_chromium_session.close()
        )

    current_process = psutil.Process()
    children = current_process.children(recursive=True)
    for child in children:
        try:
            # this can raise psutil.NoSuchProcess
            logger_print(f'cleanup_main: killing child process {child.name()} pid {child.pid}')
            child.terminate()
            # TODO wait max 30sec and then child.kill()?
        except Exception as e:
            logger_print(f'cleanup_main: killing child process failed: {e}')
    # remove tempfiles
    for temp_path in global_remove_files_when_done:
        logger_print(f'cleanup_main: removing temp path: {temp_path}')
        try:
            # FIXME OSError: [Errno 39] Directory not empty: 'Default'
            # cleanup_main: removing temp path: /run/user/1000/fetch-subs-20240106T203345.802589Z/chromium-user-data
            # TODO rm -rf
            shutil.rmtree(temp_path)
        except NotADirectoryError:
            os.unlink(temp_path)
        except FileNotFoundError:
            pass
    logger_print("cleanup_main done")



change_ipaddr_fritzbox_aiohttp_chromium_session = None

if fritzbox_login:
    logger_print("change_ipaddr: using fritzbox_login")
    # TODO solve this without aiohttp_chromium.ClientSession
    # or at least with selenium and headless=True
    async def change_ipaddr_fritzbox():
        global change_ipaddr_fritzbox_aiohttp_chromium_session
        if not change_ipaddr_fritzbox_aiohttp_chromium_session:
            logger_print("change_ipaddr: starting aiohttp_chromium.ClientSession")
            change_ipaddr_fritzbox_aiohttp_chromium_session = await aiohttp_chromium.ClientSession(
                fritzbox_login=fritzbox_login,
                tempdir=tempdir,
                _headless=True,
            )
        return await change_ipaddr_fritzbox_aiohttp_chromium_session.change_ipaddr()
    change_ipaddr = change_ipaddr_fritzbox



async def main():

    try:

        await main_scraper()

    except SystemExit:

        # cleanup
        # TODO better. try/finally?

        # TODO off by one error?
        diff_download_quota = None
        if last_download_quota != None and first_download_quota != None:
            diff_download_quota = first_download_quota - last_download_quota

        # stats
        logger_print(f"done scraping. stats: {num_requests_done} requests + {num_requests_done_ok} ok + {num_requests_done_fail} fail + {num_requests_done_dmca} dmca + quota diff {diff_download_quota}")

        if opensubtitles_org_login_cookie_jar:
            # TODO loop logins
            # TODO fix opensubtitles_org_login_cookie_jar.save
            logger_print(f"saving cookies to {opensubtitles_org_login_cookies_txt_path}")
            opensubtitles_org_login_cookie_jar.save(opensubtitles_org_login_cookies_txt_path)

        pass

    return

    # TODO run main_socks5_proxy in separate thread

    # RuntimeWarning: coroutine 'main_socks5_proxy' was never awaited
    #await asyncio.to_thread(main_socks5_proxy)

    tasks = []
    #tasks.append(asyncio.create_task(main_tcp_proxy()))
    #tasks.append(asyncio.create_task(main_socks5_proxy()))
    tasks.append(asyncio.create_task(main_scraper()))
    return_value_list = await asyncio.gather(*tasks)
    return

    async with intercept(listen_port=tcp_proxy_port) as interceptor:

        # https://gist.github.com/linw1995/4630163c5f3fb2b575bb6fd50e89aa80
        # run in other thread to avoid blocking main thread
        #await asyncio.to_thread(main_socks5_proxy, interceptor=interceptor, tcp_proxy_port=tcp_proxy_port)

        # async function is invoked normally via await statement
        await main_scraper(
            #interceptor=interceptor, tcp_proxy_port=tcp_proxy_port
        )
    return

    await main_scraper()

# https://stackoverflow.com/questions/46413879/how-to-create-tcp-proxy-server-with-asyncio
# https://stackoverflow.com/questions/49106456/how-to-safely-read-readerstream-from-asyncio-without-breaking-the-stream
# https://docs.aiohttp.org/en/stable/index.html
# https://github.com/abhinavsingh/proxy.py
# https://github.com/inaz2/proxy2/blob/master/proxy2.py

import aiohttp
import aiohttp_socks

# nested asyncio.gather
# https://stackoverflow.com/questions/69736380/using-nested-asyncio-gather-inside-another-asyncio-gather
# TODO asyncio.gather(main_tcp_proxy, main_scraper)

# TODO use asyncio, maybe aiohttp
# https://github.com/qwj/python-proxy
# https://github.com/Amaindex/asyncio-socks-server
# https://stackoverflow.com/questions/74755697/running-an-asyncoio-socket-server-and-client-on-the-same-process-for-tests
# https://gist.github.com/2minchul/609255051b7ffcde023be93572b25101#file-proxy-py
# https://stackoverflow.com/questions/71348604/error-when-running-python-asyncio-socks-proxy-server-in-a-thread
# https://duckduckgo.com/?q=python+selenium+http+proxy+capture+live+http+traffic

# https://github.com/wkeeling/selenium-wire
# install root certificate https://github.com/wkeeling/selenium-wire/raw/master/seleniumwire/ca.crt
# Certificates > Authorities > import



"""
# TODO python asyncio socks5 proxy
# https://github.com/Amaindex/asyncio-socks-server
import asyncio_socks_server
"""


# not used
"""
# https://github.com/mitmproxy/mitmproxy
# git clone https://github.com/mitmproxy/mitmproxy lib/thirdparty/mitmproxy
#import lib.thirdparty.mitmproxy.mitmproxy.master
import mitmproxy.master
import mitmproxy.options
import mitmproxy.addons
"""



# pyppeteer/util.py
import gc
import socket
def get_free_port() -> int:
    """Get free port."""
    sock = socket.socket()
    #sock.bind(('localhost', 0))
    sock.bind(('127.0.0.1', 0))
    port = sock.getsockname()[1]
    sock.close()
    del sock
    gc.collect()
    return port



tcp_proxy_port = get_free_port()
tcp_proxy_port_2 = get_free_port()



# TODO? https://github.com/VeNoMouS/cloudscraper
# A Python module to bypass Cloudflare's anti-bot page.



"""
# check proxies
# but free proxies are still unstable
# and not usable with chromium
# https://github.com/TheSpeedX/socker/blob/master/socker.py
import thespeedx_socker
"""

# in total, these lists have 10K unique proxies
# about 500 proxies = 5% will pass the proxy check
# most proxies fail the check because timeout
# timeout depends on the location of the scraper machine
# different scraper machines will have different latencies to proxies
# see get_remote_socks5_proxy_data_list
# note: proxy lists can contain "\r" which is removed by line.strip()

socks5_proxy_list_url_list = [
    "https://github.com/TheSpeedX/PROXY-List/raw/master/socks5.txt", # 4651 proxies, 2.4K stars
    "https://github.com/hookzof/socks5_list/raw/master/proxy.txt", # 330 proxies, 550 stars
    "https://github.com/roosterkid/openproxylist/raw/main/SOCKS5_RAW.txt", # 299 proxies, 230 stars
    "https://github.com/mmpx12/proxy-list/raw/master/socks5.txt", # 279 proxies, 200 stars
    "https://github.com/MuRongPIG/Proxy-Master/raw/main/socks5.txt", # 9654 proxies, 170 stars
    "https://github.com/prxchk/proxy-list/raw/main/socks5.txt", # 14 proxies, 130 stars
    "https://github.com/Zaeem20/FREE_PROXIES_LIST/raw/master/socks5.txt", # 90 proxies, 130 stars
    "https://github.com/ErcinDedeoglu/proxies/raw/main/proxies/socks5.txt", # 3807 proxies, 120 stars
    "https://github.com/casals-ar/proxy-list/raw/main/socks5", # 1247 proxies, 50 stars
]

remote_socks5_proxy_timeout = 15

remote_socks5_proxy_data_list = None



# https://stackoverflow.com/questions/46413879/how-to-create-tcp-proxy-server-with-asyncio
async def main_tcp_proxy_pipe_1(reader, writer):
    try:
        while not reader.at_eof():
            buf = await reader.read(2048)
            logger_print(f"tcp proxy: pipe 1: buf = {repr(buf[0:200])}...")
            writer.write(buf)
    finally:
        writer.close()

async def main_tcp_proxy_pipe_2(reader, writer):
    try:
        while not reader.at_eof():
            buf = await reader.read(2048)
            logger_print(f"tcp proxy: pipe 2: buf = {repr(buf[0:200])}...")
            writer.write(buf)
    finally:
        writer.close()



# https://stackoverflow.com/questions/46413879/how-to-create-tcp-proxy-server-with-asyncio
async def main_tcp_proxy_handle_client(local_reader, local_writer):
    logger_print(f"tcp proxy: handle_client")
    try:
        remote_reader, remote_writer = await asyncio.open_connection('127.0.0.1', tcp_proxy_port_2)
        pipe1 = main_tcp_proxy_pipe_1(local_reader, remote_writer)
        pipe2 = main_tcp_proxy_pipe_2(remote_reader, local_writer)
        await asyncio.gather(pipe1, pipe2)
    finally:
        local_writer.close()

# https://stackoverflow.com/questions/46413879/how-to-create-tcp-proxy-server-with-asyncio
async def main_tcp_proxy():
    logger_print(f"tcp proxy: start")
    return asyncio.start_server(main_tcp_proxy_handle_client, '127.0.0.1', tcp_proxy_port)



"""
# based on asyncio_socks_server/__main__.py
#from asyncio_socks_server.app import SocksServer
#from asyncio_socks_server.config import BASE_LOGO, SOCKS_SERVER_PREFIX, Config
import asyncio_socks_server.app
#import asyncio_socks_server.config

async def main_socks5_proxy__asyncio_socks_server():
    logger_print(f"socks5 proxy: start")
    #return asyncio.start_server(main_tcp_proxy_handle_client, '127.0.0.1', tcp_proxy_port)
    config_args = {
        "LISTEN_HOST": "127.0.0.1",
        "LISTEN_PORT": tcp_proxy_port,
        #"AUTH_METHOD": args.method,
        "ACCESS_LOG": sys.stdout,
        "DEBUG": True,
        #"STRICT": args.strict,
    }
    app = asyncio_socks_server.app.SocksServer(
        # Path to the config file in json format.
        #config=None,
        # Prefix of the environment variable to be loaded as the config
        #env_prefix=args.env_prefix,
        **{k: v for k, v in config_args.items() if v is not None},
    )
    return app.run()
"""



# OLD https://gist.github.com/linw1995/4630163c5f3fb2b575bb6fd50e89aa80
# https://github.com/devsecops-tools/wapiti/blob/master/wapitiCore/net/intercepting_explorer.py
from typing import Callable, Optional
import contextlib




class MitmCaptureRequests:
    def __init__(self, data_queue: asyncio.Queue):
        self._queue = data_queue
        #self._headers = headers
        #self._drop_cookies = drop_cookies

    async def request(self, *args, **kwargs):
        logger_print(f"MitmCaptureRequests.request", args, kwargs)
        """
        for key, value in self._headers.items():
            # This will use our user-agent too
            flow.request.headers[key] = value
        """

    async def response(self, *args, **kwargs):
        logger_print(f"MitmCaptureRequests.response", args, kwargs)
        """
        if self._drop_cookies:
            if "set-cookie" in flow.response.headers:
                del flow.response.headers["set-cookie"]

        content_type = flow.response.headers.get("Content-Type", "text/plain")
        flow.response.stream = False
        if "text" in content_type or "json" in content_type:
            request = mitm_to_wapiti_request(flow.request)

            decoded_headers = decode_key_value_dict(flow.response.headers)

            response = Response(
                httpx.Response(
                    status_code=flow.response.status_code,
                    headers=decoded_headers,
                    # httpx expect the raw content (not decompressed)
                    content=flow.response.raw_content,
                ),
                url=flow.request.url
            )

            await self._queue.put(
                (request, response)
            )
        """



async def main_socks5_proxy(
        #port: int,
        #data_queue: asyncio.Queue,
        #headers: httpx.Headers,
        #proxy: Optional[str] = None,
        #drop_cookies: bool = False
    ):
    logger_print(f"socks5 proxy: start")

    opt = mitmproxy.options.Options()

    # We can use an upstream proxy that way but socks is not supported
    #if proxy:
    #    log_blue(f"Using upstream proxy {proxy}")
    #    opt.update(mode=f"upstream:{proxy}")

    opt.update(mode=[f"socks5@127.0.0.1:{tcp_proxy_port}"])
    #opt.update(listen_port=tcp_proxy_port)

    logging.getLogger("mitmproxy.proxy.server").setLevel(logging.DEBUG)

    #logging.getLogger("selenium.webdriver.remote.remote_connection").setLevel(logging.INFO)
    #logging.getLogger("urllib3.connectionpool").setLevel(logging.INFO)

    master = mitmproxy.master.Master(opt)

    master.addons.add(mitmproxy.addons.core.Core())

    master.addons.add(mitmproxy.addons.proxyserver.Proxyserver())

    #master.addons.add(mitmproxy.addons.next_layer.NextLayer())

    # mitmproxy will generate an authority cert in the ~/.mitmproxy directory. Load it in your browser.
    #master.addons.add(mitmproxy.addons.tlsconfig.TlsConfig())

    # If ever we want to have both the interception proxy and an automated crawler then we need to sync cookies
    #master.addons.add(AsyncStickyCookie())

    # Finally here is our custom addon that will generate Wapiti Request and Response objects and push them to the queue
    data_queue = asyncio.queues.Queue()
    #master.addons.add(MitmFlowToWapitiRequests(data_queue, headers, drop_cookies))
    #master.addons.add(MitmCaptureRequests(data_queue))

    await master.run()



"""
class Interceptor___zzz:
    def __init__(self):
        self.response_hook: Optional[ResponseHook] = None

    @contextlib.contextmanager
    def hook_response(self, hook_function: ResponseHook):
        self.response_hook = hook_function
        try:
            yield
        finally:
            self.response_hook = None

    def response(self, flow: HTTPFlow):
        logger_print(f"Interceptor.response: ")
        if self.response_hook is not None:
            self.response_hook(flow)
"""

class Interceptor:
    def __init__(self):
        self.response_hook: Optional[ResponseHook] = None

    '''
    @contextlib.contextmanager
    def hook_response(self, hook_function: ResponseHook):
        self.response_hook = hook_function
        try:
            yield
        finally:
            self.response_hook = None
    '''

    def response(self, *args, **kwargs):
        logger_print(f"Interceptor.response", args, kwargs)
        '''
        if self.response_hook is not None:
            self.response_hook(flow)
        '''

    def request(self, *args, **kwargs):
        logger_print(f"Interceptor.request", args, kwargs)

@contextlib.asynccontextmanager
async def intercept(listen_port: int = 8080) -> None:
    options = mitmproxy.options.Options(listen_host="0.0.0.0", listen_port=listen_port)
    master = mitmproxy.master.Master(options)
    master.server = server = ProxyServer(ProxyConfig(options))

    # TODO: Keeps this line until the major version 7 is released
    master.addons.add(core.Core())

    master.start()
    await master.running()

    interceptor = Interceptor()
    master.addons.add(interceptor)
    try:
        yield interceptor
    finally:
        # Don't use `Master.shutdown()`.
        # It will make the process being unable to exit.
        # And I don't know what is causing this.
        master.should_exit.set()
        server.shutdown()

async def main_socks5_proxy__interceptor(interceptor=None, tcp_proxy_port=8100):
    logger_print(f"socks5 proxy: start")

    logging.getLogger("mitmproxy").setLevel(logging.DEBUG)
    logging.getLogger("mitmproxy.master").setLevel(logging.DEBUG)
    logging.getLogger("mitmproxy.options").setLevel(logging.DEBUG)
    logging.getLogger("mitmproxy.proxy.server").setLevel(logging.DEBUG)

    #app = lib.thirdparty.mitmproxy.mitmproxy.master.Master(
    options = mitmproxy.options.Options(
        mode=[f"socks5@127.0.0.1:{tcp_proxy_port}"],
    )
    app = mitmproxy.master.Master(options)
    return app.run()



async def verbose_sleep(sleep_total, sleep_step=10):
    for sec_left in range(sleep_total, 1, -1*sleep_step):
        logger_print(f"time left: {sec_left} seconds")
        await asyncio.sleep(sleep_step)



# stats
num_requests_done = 0
num_requests_done_ok = 0
num_requests_done_fail = 0
num_requests_done_dmca = 0
downloads_since_change_ipaddr = 0
first_download_quota = None
last_download_quota = None
last_download_quota_bak = None



daily_quota = 1000 # vip account
daily_quota_is_exceeded = False



async def main_scraper():

    # global state
    global options
    global user_agents
    global aiohttp_chromium_session
    global chromium_user_data_dir
    global opensubtitles_com_login_headers
    global opensubtitles_org_login_cookies_txt_path
    global opensubtitles_org_login_cookie_jar
    global remote_socks5_proxy_data_list
    global max_concurrency
    global num_requests_done
    global num_requests_done_ok
    global num_requests_done_fail
    global num_requests_done_dmca
    global daily_quota_is_exceeded
    global missing_numbers
    global metadata_db_con
    global metadata_db_cur

    #logger_print(f"main scraper: waiting for socks5 proxy")
    #await asyncio.sleep(10) # TODO dynamic



    await update_metadata_db()

    if options.only_update_metadata_db:
        logger_print(f"done update_metadata_db - exiting")
        return

    if options.metadata_db:
        logger_print(f"using metadata db {repr(options.metadata_db)}")
        metadata_db_con = sqlite3.connect(options.metadata_db)
        metadata_db_cur = metadata_db_con.cursor()



    if options.tempdir:
        tempdir = options.tempdir
    else:
        # tempdir=$(mktemp -d -p /run/user/$(id -u) -t fetch-subs.XXXXXXXXXXX)
        # use tmpfs in RAM to avoid disk writes
        tempdir = f"/run/user/{os.getuid()}"
        if not os.path.exists(tempdir):
            raise ValueError(f"tempdir does not exist: {tempdir}")
        tempdir = tempdir + f"/fetch-subs-{datetime_str()}"

    logger_print(f"creating tempdir {tempdir}")
    os.makedirs(tempdir, exist_ok=True)

    #first_num_file = last_num_db
    #last_num_file = 1

    os.makedirs(new_subs_dir, exist_ok=True)
    nums_done = []

    logger_print(f"parsing {new_subs_repo_shards_dir}")
    len_1 = len(nums_done)
    for file_path in glob.glob(f"{new_subs_repo_shards_dir}/shards/*/*.db"):
        file_name = os.path.basename(file_path)
        shard_id = int(file_name[:-6]) # remove "xxx.db" suffix
        #logger_print(f"found shard {shard_id}")
        shard_num_list = list(range(shard_id * 1000, (shard_id + 1) * 1000))
        #logger_print(f"found shard {shard_id}: shard_num_list", shard_num_list[:10], "...", shard_num_list[-10:])
        assert len(shard_num_list) == 1000
        nums_done += shard_num_list
    len_2 = len(nums_done)
    logger_print(f"parsing {new_subs_repo_shards_dir} -> found {len_2 - len_1} nums in {int((len_2 - len_1) / 1000)} shards")
    #raise 123

    filenames = []
    #if os.path.exists(f"{new_subs_repo_dir}/files.txt"):
    if False:
        with open(f"{new_subs_repo_dir}/files.txt") as f:
            for line in f:
                filenames.append(line.strip())

        # FIXME this is wrong
        # this should count only downloads made with the vip account login
        # this is so much easier in bash...
        day_today = time.strftime("%Y-%m-%d")
        downloads_done_today = int(subprocess.check_output(["/bin/sh", "-c", f"""
            git -C {new_subs_repo_dir} log --format=format:%aI |
            head -n{daily_quota * 2} |
            grep {day_today} |
            wc -l
        """], encoding="utf8").strip()) or 0
        logger_print(f"downloads_done_today: {downloads_done_today}")

        # rate-limiting can start before the daily limit of 1000
        # so, check against 0.9 of the daily limit -> 900
        # usually, the scraper uses 100% of the daily quota
        # until it gets the "Sorry, maximum download count for IP" message
        daily_quota_is_exceeded = downloads_done_today > (0.9 * daily_quota)
        logger_print(f"daily_quota_is_exceeded: {daily_quota_is_exceeded}")

    # debug: ignore daily_quota
    daily_quota_is_exceeded = False

    logger_print(f"parsing {new_subs_dir}")
    filenames += os.listdir(new_subs_dir)

    len_1 = len(nums_done)
    for filename in filenames:
        #match = re.fullmatch(r"([0-9]+)\.(.+\.)?zip", filename)
        # retry .html files
        # FIXME if/else
        # NOTE "dcma" is wrong
        match = re.fullmatch(r"([0-9]+)\.(zip|not-found|dmca|not-found-dmca|dcma|not-found-dcma|.*\.zip)", filename)
        if match:
            # new format in f"{new_subs_repo_dir}/files.txt"
            num = int(match.group(1))
            nums_done.append(num)
        match = re.fullmatch(r".*\.\([0-9]*\)\.[a-z]{3}\.[0-9]+cd\.\(([0-9]+)\)\.zip", filename)
        if match:
            # original format in new_subs_dir
            num = int(match.group(1))
            nums_done.append(num)
    len_2 = len(nums_done)
    logger_print(f"parsing {new_subs_dir} -> found {len_2 - len_1} nums")

    logger_print(f"found {len(nums_done)} done nums")

    nums_done = sorted(nums_done)

    #nums_done_min = 9180517 # last num in opensubs.db
    #nums_done_min = 9521948 # last num in opensubtitles.org.dump.9180519.to.9521948
    nums_done_min = nums_done[0]

    # optimization: limit range of numbers
    if options.first_num:
        logger_print(f"setting nums_done_min to {options.first_num}")
        nums_done_min = options.first_num

    if options.force_download:
        # quickfix
        logger_print(f"ignoring nums_done to force download")
        nums_done = []

    #raise 123

    # too much. todo compress to ranges
    #logger.debug(f"nums_done {nums_done}")
    #logger.debug(f"nums_done {nums_done[:100]} ... {nums_done[-100:]}")
    #raise NotImplementedError



    # TODO are there more missing subs?
    # get the latest version of subtitles_all.txt.gz
    # run subtitles_all.txt.gz-parse.py
    # check release/opensubtitles.org.dump.9180519.to.9521948.by.lang.2023.04.26/langs/*.db
    # with a fork of opensubs-find-missing-subs.py

    # load missing numbers list
    # these are the missing subs in opensubs.db
    # between num 1 and 9180517
    # generated by opensubs-find-missing-subs.py
    missing_nums_path = "opensubs-find-missing-subs.py.txt"
    nums = []
    # NOTE here we need the full nums_done
    # which was not reduced with options.first_num
    nums_done_set = set(nums_done)
    if os.path.exists(missing_nums_path):
        with open(missing_nums_path) as f:
            for line in f.readlines():
                if line[0] != "+":
                    continue
                num = int(line[2:])
                if num in nums_done_set:
                    continue
                nums.append(num)
        logger_print(f"loaded missing_numbers from {missing_nums_path}: {nums}")
        missing_numbers += nums

    logger.debug(f"{__line__()} missing_numbers = {missing_numbers}")

    logger_print(f"found {len(missing_numbers)} missing numbers")

    #raise 123

    #num_stack_last = None
    num_stack_first = None

    # optimization: limit range of numbers
    if options.first_num:
        len_before = len(nums_done)
        nums_done = list(filter(lambda num: num >= options.first_num, nums_done))
        logger_print(f"using options.first_num {options.first_num} as lower limit for nums_done. len(nums_done): {len_before} -> {len(nums_done)}")

    nums_done_set = set(nums_done)

    if missing_numbers:
        # filter: remove done numbers
        missing_numbers = list(filter(lambda n: n in nums_done_set, missing_numbers))

    logger.debug(f"{__line__()} missing_numbers = {missing_numbers}")

    # compress nums_done to ranges
    nums_done_ranges = []
    prev_num = -1 # first valid number is 1
    range_start = 0
    for num in nums_done:
        if num != prev_num + 1:
            # finish previous range
            if range_start != 0:
                if range_start == prev_num:
                    # only one number in this range
                    nums_done_ranges.append(range_start)
                elif range_start + 1 == prev_num:
                    # only two numbers in this range
                    nums_done_ranges.append(range_start)
                    nums_done_ranges.append(prev_num)
                else:
                    # javascript has no tuples
                    #nums_done_ranges.append((range_start, prev_num))
                    nums_done_ranges.append([range_start, prev_num])
            # start new range
            range_start = num
        prev_num = num
    # add last range
    if range_start != 0:
        if range_start == prev_num:
            # only one number in this range
            nums_done_ranges.append(range_start)
        elif range_start + 1 == prev_num:
            # only two numbers in this range
            nums_done_ranges.append(range_start)
            nums_done_ranges.append(prev_num)
        else:
            # javascript has no tuples
            #nums_done_ranges.append((range_start, prev_num))
            nums_done_ranges.append([range_start, prev_num])

    #logger.debug(f"nums_done_ranges: {nums_done_ranges}")
    #raise NotImplementedError




    def is_num_done(num, nums_done_ranges, nums_done_min=None):
        # all out-of-range nums are done
        if nums_done_min and num < nums_done_min:
            return True
        for range_or_num in nums_done_ranges:
            if num == range_or_num: return True
            if type(range_or_num) == int: continue
            if range_or_num[0] <= num and num <= range_or_num[1]: return True
            # no! ranges are not sorted
            # shortcut: ranges are sorted
            #if range_or_num[1] < num: return False

    #logger_print("is_num_done 9843118", is_num_done(9843118, nums_done_ranges))
    #assert is_num_done(9843118, nums_done_ranges) == True
    #raise NotImplementedError



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



    chromium_cookie_jar = None



    # init scraper

    if options.proxy_provider == "zenrows.com":

        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    elif options.proxy_provider == "scrapfly.io":

        # read cache to resume after error
        nums = []
        for path in glob.glob("new-subs/*.scrapfly.json"):
            match = re.match(r"new-subs/([0-9]+)\.scrapfly\.json", path)
            if not match:
                continue
            num = int(match.group(1))
            nums.append(num)
        logger_print(f"loaded missing_numbers from new-subs/*.scrapfly.json: {nums}")
        missing_numbers = nums + missing_numbers

        logger.debug(f"{__line__()} missing_numbers = {missing_numbers}")

    elif options.proxy_provider == "chromium":

        cookie_jar = []

        if opensubtitles_org_logins and not daily_quota_is_exceeded:

            # TODO loop logins
            if options.username:
                logger_print(f"getting opensubtitles.org login for username {repr(options.username)}")
                username, password = next(
                    (x for x in opensubtitles_org_logins if x[0] == options.username),
                    #opensubtitles_org_logins[0]
                )
            else:
                username, password = opensubtitles_org_logins[0]

            # load stored cookies from cookies.txt file
            cookies_txt_path = f"cookies/opensubtitles.org-cookies.{username}.txt"

            cookie_jar = aiohttp_chromium.MozillaCookieJar()

            # load cookies 1
            logger_print("init scraper: loading cookies from", cookies_txt_path)
            cookie_jar.load(cookies_txt_path)

            chromium_cookie_jar = cookie_jar

        aiohttp_chromium_session = await aiohttp_chromium.ClientSession(
            cookie_jar=cookie_jar,
            tempdir=tempdir,
            _headless=True,
        )

        # later cleanup:
        # await aiohttp_chromium_session.close()

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

    elif options.proxy_provider == "free-proxies":
        # load proxy list
        remote_socks5_proxy_data_list = await aiohttp_chromium.ClientSession.get_remote_socks5_proxy_data_list(
            check_proxies=False,
        )
        max_concurrency = 100



    # TODO rename proxy_provider to download_method or scraping_method
    if options.proxy_provider == "javascript-console":

        # generate javascript code
        # which can be pasted to a browser javascript-console
        # on https://www.opensubtitles.org/en/search/sublanguageid
        # which will click download links of all missing subs
        # and loop through the pages, until it finds a captcha

        js_code = (
            "// fetch subs\n"
            "function sleep(ms) { return new Promise(resolve => setTimeout(resolve, ms)); };\n"
            "var done_sub_nums = new Set();\n"
            "var nums_done_ranges = " + repr(nums_done_ranges) + ";\n"
            "var done_links = 0;\n"
            "function is_num_done(num) {\n"
            "    for (const rangeOrNum of nums_done_ranges) {\n"
            "        if (num == rangeOrNum) return true;\n"
            "        if (isFinite(rangeOrNum)) continue; // rangeOrNum is a number\n"
            "        // rangeOrNum is a range\n"
            "        if (rangeOrNum[0] <= num && num <= rangeOrNum[1]) return true;\n"
            "        // shortcut: ranges are sorted\n"
            "        if (rangeOrNum[1] < num) return false;\n"
            "    }\n"
            "    return false;\n"
            "}\n"
            "var subLinkSelector = `a[href^='https://dl.opensubtitles.org/en/download/sub/']`;\n"
            "var nextPageLinkSelector = `#pager > div > strong+a`;\n"
            "async function scrape() {\n"
            "    while (!document.querySelector(nextPageLinkSelector)) {\n"
            "        // wait for page load\n"
            "        await sleep(1000);\n"
            "    }\n"
            "    var subLinkList = Array.from(document.querySelectorAll(subLinkSelector));\n"
            "    for (const a of subLinkList) {\n"
            "        const num = Number(a.href.split('/').slice(-1)[0]);\n"
            "        if (done_sub_nums.has(num) == true) { continue; }\n"
            "        if (is_num_done(num)) { continue; }\n"
            "        console.log(`clicking ${num}`);\n"
            # no. this fails on error pages
            #"        a.click();\n"
            # open link in new tab
            "        window.open(a.href, '_blank');\n"
            # we must sleep some time between requests
            # otherwise chromium loses=ignores requests
            # TODO dynamic. the loss is dynamic
            # so we have to check the download folder
            # if all requests are done
            "        await sleep(1000);\n"
            "        done_links++;\n"
            "        done_sub_nums.add(num);\n"
            #"        if (done_links > 3) { break; } // debug\n"
            "    }\n"
            # NOTE navigating to next page will clear JS console
            "    console.log(`clicking next page`);\n"
            "    document.querySelector(nextPageLinkSelector).click();\n"
            "}\n"
            "await scrape();\n"
        )
        output_path = "fetch-subs.javascript-console.js"
        logger_print(f"writing {output_path}")
        with open(output_path, "w") as f:
            f.write(js_code)
        logger_print(f"TODO copy to clipboard: cat {output_path} | xclip -i -sel c")
        logger_print(f"TODO paste to javascript-console of browser at https://www.opensubtitles.org/en/search/sublanguageid-all")
        raise SystemExit



    # TODO condition?
    if True:

        # TODO check the login status
        #if "<strong>You are not logged in!</strong>" in page_source:

        if not opensubtitles_org_logins:

            raise NotImplementedError("login to opensubtitles.org")

            #url = "https://www.opensubtitles.org/en/search/subs"
            url = "https://www.opensubtitles.org/en/login"

            logger_print(f"opening url {url}")
            await asyncify(driver.get(url, timeout=3*60))
            await asyncio.sleep(5) # wait for page load
            logger_print(f"please login to opensubtitles.org. you have 2 minutes")

            driver.find_element_by_id("NdbxLoginForm_username").write("username")
            driver.find_element_by_id("NdbxLoginForm_password").write("password")
            driver.find_element_by_name("loginButton").click()
            driver.find_element_by_xpath("//*[@id='resultsFound']/div/table/tbody/tr/td[1]/a").click

            await verbose_sleep(120)

            # TODO wait for login cookie



        # check the login status
        # login-by-cookies can fail
        # because the login session can have expired

        # TODO retry loop, try/except, bla bla bla ...
        # TODO refactor all this bullshit

        url = "https://www.opensubtitles.org/en/search/subs"
        logger.debug(f"checking login: opening url {url}")
        """
        await asyncify(driver.get(url, timeout=60))
        await asyncio.sleep(5) # wait for page load
        page_source = await driver.page_source
        """
        async with await aiohttp_chromium_session.get(url, timeout=3*60) as resp:
            page_source = await resp.text()

        logger.debug(f"checking login: page_source: " + repr(page_source[:50] + " ... " + page_source[-50:]))

        # <div id="logindetail" class="top_info_left">Logged-in as: <a href="/en/profile/iduser-12345">username</a>
        if ">Logged-in as: <a href" in page_source:
            logger.debug(f"checking login: ok")

        elif "<strong>You are not logged in!</strong>" in page_source:

            # TODO is this reachable? - no

            logger.debug(f"checking login: fail. not logged in")

            # open the login page
            url = "https://www.opensubtitles.org/en/login"
            logger.debug(f"checking login: opening url {url}")
            """
            await asyncify(driver.get(url, timeout=60))
            await asyncio.sleep(5)
            """

            # FIXME this can hang somewhere
            # when i solve the captcha, click the login button
            # then the request to https://www.opensubtitles.org/en/login hangs
            # and after timeout, the next page says
            # logged-in as: xxx

            async with await aiohttp_chromium_session.get(url, timeout=3*60) as resp:

                #page_source = await resp.text()
                driver = resp._driver

                # fill the login form

                # TODO loop logins
                if options.username:
                    logger_print(f"getting opensubtitles.org login for username {repr(options.username)}")
                    username, password = next(
                        (x for x in opensubtitles_org_logins if x[0] == options.username),
                        #opensubtitles_org_logins[0]
                    )
                else:
                    username, password = opensubtitles_org_logins[0]

                async def elem_set_value(driver, elem, text):
                    # this would append text: elem.write(text)
                    # but we want to set the input value
                    js_code = """
                        const elem = arguments[0];
                        const value = arguments[1];
                        elem.value = value; // TODO elem.setAttribute ?
                        return true;
                    """
                    return await driver.execute_script(js_code, elem, text) == True

                logger.debug(f"checking login: entering username")
                elem = await driver.find_element(By.CSS_SELECTOR, "div.right_login input.login[name='user']")
                #await elem.write(username)
                await elem_set_value(driver, elem, username)

                logger.debug(f"checking login: entering password")
                elem = await driver.find_element(By.CSS_SELECTOR, "div.right_login input.login[name='password']")
                #await elem.write(password)
                await elem_set_value(driver, elem, password)

                logger.debug(f"checking login: enabling \"remember me\"")
                elem = await driver.find_element(By.CSS_SELECTOR, "div.right_login input[name='remember']")
                await elem.click()



                # click captcha

                logger.debug(f"checking login: clicking captcha")
                iframe = await driver.find_element(By.CSS_SELECTOR, "#g-recaptcha > div > div > iframe")
                logger.debug(f"checking login: clicking captcha: iframe {repr(iframe)}")

                iframe_doc = await iframe.content_document
                logger.debug(f"checking login: clicking captcha: iframe_doc {repr(iframe_doc)}")
                elem = await iframe_doc.find_element(By.CSS_SELECTOR, "#recaptcha-anchor")
                logger.debug(f"checking login: clicking captcha: elem {repr(elem)}")
                await elem.click()

                # TODO use captcha solver
                # https://www.crx4chrome.com/crx/102543/ # ReCaptcha Solver
                # https://anti-captcha.com/

                # check if captcha is solved
                # wait until captcha is solved
                logger.debug(f"checking login: waiting until captcha is solved")
                while True:
                    await asyncio.sleep(5)
                    try:
                        elem = await iframe_doc.find_element(By.CSS_SELECTOR, "span.recaptcha-checkbox-checked")
                        # ok. captcha is solved
                        logger.debug(f"checking login: captcha is solved")
                        break
                    except NoSuchElementException:
                        # no. captcha is not solved
                        # wait for user to solve the captcha
                        pass

                # TODO check "Logged-in as:" in page_source

                # submit the login form
                # xpath: /html/body/div[1]/div[6]/form/table/tbody/tr[4]/td/input[5]
                # css: #subtitles_body > div.content > div.right_login > form > table > tbody > tr:nth-child(4) > td > input.searchSubmit
                # html: <input type="submit" class="searchSubmit" value="Login">
                logger.debug(f"checking login: submitting the login form")
                elem = await driver.find_element(By.CSS_SELECTOR, "div.right_login input[type='submit'][value='Login']")
                await elem.click()

                logger.debug(f"checking login: current_url: " + repr(await driver.current_url))

                # wait for login
                await asyncio.sleep(10)

                # TODO wait for change of driver.current_url
                # a: https://www.opensubtitles.org/en/login
                # b: https://www.opensubtitles.org/en/search/subs
                """
                # wait for the user to click "login"
                logger.debug(f"checking login: please submit the login form")
                while (await driver.current_url) != "https://www.opensubtitles.org/en/search/subs":
                    await asyncio.sleep(5)
                # wait for page load
                await asyncio.sleep(5)
                """

                logger.debug(f"checking login: current_url: " + repr(await driver.current_url))

                # verify login status
                page_source = await driver.page_source
                logger.debug(f"checking login: page_source: " + repr(page_source[:50] + " ... " + page_source[-50:]))
                if "<strong>You are not logged in!</strong>" in page_source:
                    # TODO retry loop
                    logger.debug(f"checking login: FIXME login failed?")
                    await asyncio.sleep(99999)

            # login done

            # save cookies
            cookies_txt_path = f"cookies/opensubtitles.org-cookies.{username}.txt"
            cookie_jar = aiohttp_chromium.MozillaCookieJar()
            # copy cookies from driver to cookiejar
            # cookiejar is a list of dicts
            cookie_jar.extend(await driver.get_cookies())
            logger_print("checking login: saving cookies to", cookies_txt_path)
            cookie_jar.save(cookies_txt_path)
            del cookie_jar



    #if options.proxy_provider == "chromium" and not daily_quota_is_exceeded:

    scrape_latest_descending = False

    if scrape_latest_descending and options.proxy_provider == "chromium":

        # scrape the 1000 latest subs in descending order

        logger_print(f"scraping the 1000 latest subs in descending order")

        # FIXME use aiohttp_chromium_session.get(...)
        # resp = await aiohttp_chromium_session.get(url, timeout=60*5)

        # dont enter the "fetch_sub" loop
        # because requesting the sub urls directly
        # gets us blocked after 30...35 requests
        # instead
        # open the "start" page https://www.opensubtitles.org/en/search/subs
        # wait for the user to login
        # open the "new subs" page https://www.opensubtitles.org/en/search/sublanguageid-all
        # parse metadata: download counts, ratings
        # click download links of missing subs
        # go to next page, repeat



        # parse ratings and download counts from html

        # yeah i know the dogma "dont use regex to parse html"
        # but this is faster than lxml or beautifulsoup4
        # it will break when the html format is changed
        # but same problem with html parsers and xpath/css selectors

        """
        pattern_text = (
            r'<tr onclick.*? id="name([0-9]{1,10})".*?'
            r'>([0-9]+)x\n</a><br.*?'
            r'<span title="([0-9]+) votes">([0-9.]+)</span>.*?'
            r'</tr>'
        )
        """

        # devmode: only capture .*? to get the min/max match sizes
        sub_metadata_regex_text_devmode = (
            r'<tr onclick(.*?) id="name[0-9]{1,10}"(.*?)'
            r'>[0-9]+x\n</a><br(.*?)'
            r'<span title="[0-9]+ votes">[0-9.]+</span>'
            r'(.*?)'
            r'<td><a href="/en/profile/iduser-[0-9.]+"'
            r'(.*?)'
            r'</tr>'
        )

        sub_metadata_regex_pattern_devmode = re.compile(sub_metadata_regex_text_devmode, re.S)

        # optimized the "match all" ranges from ".*?" to ".{80,200}?" etc
        sub_metadata_regex_text = (
            r'<tr onclick.{80,200}? ' # [111, 132]
            r'id="name([0-9]{1,10})".{700,3000}?' # [920, 1454]
            r'>([0-9]+)x\n</a><br.{30,70}?' # [48, 51]
            r'<span title="([0-9]+) votes">([0-9.]+)</span>'
            r'.*?'
            r'<td><a href="/en/profile/iduser-([0-9.]+)"'
            #r'.{300,2000}?' # [400, 404]
            #r'</tr>'
        )

        # unoptimized
        sub_metadata_regex_text = (
            r'<tr onclick.*? ' # [111, 132]
            r'id="name([0-9]{1,10})".*?' # [920, 1454]
            r'>([0-9]+)x\n</a><br.*?' # [48, 51]
            r'<span title="([0-9]+) votes">([0-9.]+)</span>'
            r'.*?'
            r'<td><a href="/en/profile/iduser-([0-9.]+)"'
            r'.*?'
            r'</tr>'
        )

        sub_metadata_regex_pattern = re.compile(sub_metadata_regex_text, re.S)



        subs_downloads_ratings_connection = sqlite3.connect("subs_downloads_ratings.db")
        subs_downloads_ratings_connection.execute(
            "CREATE TABLE IF NOT EXISTS subs_downloads_ratings (\n"
            "  num INTEGER PRIMARY KEY,\n"
            "  downloads INTEGER,\n"
            "  rating INTEGER,\n"
            "  votes INTEGER,\n"
            "  uploader_id INTEGER,\n"
            "  scrape_day INTEGER\n"
            ")"
        )
        subs_downloads_ratings_cursor = subs_downloads_ratings_connection.cursor()



        # https://www.selenium.dev/selenium/docs/api/py/webdriver_chrome/selenium.webdriver.chrome.webdriver.html
        #driver = aiohttp_chromium_session._selenium_driver



        #await asyncio.sleep(88888888)
        #raise NotImplementedError



        # TODO disable images, styles, scripts, popups
        # we only need html
        # https://www.crx4chrome.com/crx/1089/ # Web Developer
        # https://www.crx4chrome.com/crx/3596/ # uMatrix
        # https://www.crx4chrome.com/crx/7739/ # disable-HTML



        # FIXME this fails after 1000 subs == 25 pages
        # because the server limits the offset parameter to 960
        # if we try to get page 26, 27, 28, ...
        # then the server always returns page 25 == offset 960

        # fix: scrape EVERY FUCKING PAGE...
        # because that "admin" idiot wants it "the hard way"
        # f"https://www.opensubtitles.org/en/subtitles/{num}"

        # but first...
        # lets keep this for continuous scraping
        # run this 2 times per day (or 4 times)
        # to download about 1000 new subs per day

        # and then...
        # TODO get list of all missing sub numbers
        # from subtitles_all.txt.gz
        # minus nums of releases and new-subs-repo
        # then open a chromium window
        # and download all
        # url = f"https://dl.opensubtitles.org/en/download/sub/{num}"
        # dont resolve the http redirect
        # because we have a cookie for dl.opensubtitles.org

        """
        first_index_offset = None
        if first_index_offset == None:
            # get rowcount from subs_downloads_ratings.db
            sql_query = "SELECT count() FROM subs_downloads_ratings"
            num_subs_done = subs_downloads_ratings_cursor.execute(sql_query).fetchone()[0]
            logger_print(f"found {num_subs_done} rows in subs_downloads_ratings")
            first_index_offset = math.floor(num_subs_done / 40) * 40
            if first_index_offset > 0:
                # repeat scraping the last page
                first_index_offset -= 40
                logger_print(f"continuing scrape from index_offset {first_index_offset}")
        index_offset = first_index_offset - 40
        while True:
            index_offset += 40
        """



        # FIXME move to xxx
        """
        # open downloads in a new tab
        # https://www.selenium.dev/documentation/webdriver/interactions/windows/

        # workaround for
        # Exception in callback SingleCDPSocket._exc_handler(<Task finishe... cancelled>')>)
        # handle: <Handle SingleCDPSocket._exc_handler(<Task finishe... cancelled>')>)>
        # asyncio.exceptions.InvalidStateError: CANCELLED: <Future cancelled>

        driver_main_window = await asyncify(driver.current_window_handle)
        #logger_print("driver_main_window", repr(driver_main_window))

        # open downloads tab
        # open new tab, switch to new tab
        driver_downloads_window = await asyncify(driver.switch_to.new_window('tab'))
        #logger_print("new_window_result", repr(new_window_result))
        await asyncify(driver.get("chrome://downloads/", timeout=10))

        # open all download links in this tab
        # open new tab, switch to new tab
        # TODO restart this tab on error
        driver_download_worker_window = await asyncify(driver.switch_to.new_window('tab'))
        #logger_print("new_window_result", repr(new_window_result))

        await asyncify(driver.switch_to.window(driver_main_window))
        """



        for index_offset in range(0, 1000, 40):

            logger_print(f"index_offset {index_offset} of 1000")

            this_page_num_downloads = 0

            scrape_time = time.time() # utc timestamp

            # compress time from 4 bytes to 2 bytes
            # this will grow to 3 bytes on
            # $ date --utc -d "2000-01-01+$((256 * 256))days" -Is
            # 2179-06-07T00:00:00+00:00
            # 4 byte timestamps will overflow on
            # $ date --utc -d "1970-01-01+4294967296sec" -Is
            # 2106-02-07T06:28:16+00:00
            # -> year 2106 problem
            # see also https://en.wikipedia.org/wiki/Year_2038_problem
            # storing date as string would take len("21060207") == 8 bytes
            # subtitles_all.txt.gz stores SubAddDate as "2004-10-31 23:54:23" = 19 bytes
            # for 7 million subtitles:
            # 2 * 7E6 = 13 MiByte
            # 4 * 7E6 = 27 MiByte
            # 8 * 7E6 = 53 MiByte
            # 19 * 7E6 = 127 MiByte

            # $ date --utc +%s -d 2000-01-01
            # 946684800
            year_2000_timestamp = 946684800

            scrape_time_days_since_year_2000 = math.floor((time.time() - year_2000_timestamp) / (60 * 60 * 24))

            #url = "https://www.opensubtitles.org/en/search/sublanguageid-all"
            # sort by upload date ascending
            # ideally we would sort by subtitle number, but that is not possible
            # upload date is the next-best sort field, because it creates a stable sort
            # so the pagination offsets are stable
            # https://www.opensubtitles.org/en/search/sublanguageid-all/sort-5/asc-1

            # no. this fails after 1000 subs
            #url = f"https://www.opensubtitles.org/en/search/sublanguageid-all/offset-{index_offset}/sort-5/asc-1"

            url = f"https://www.opensubtitles.org/en/search/sublanguageid-all/offset-{index_offset}"

            if index_offset == 0:
                # remove the "/offset-0" suffix
                url = f"https://www.opensubtitles.org/en/search/sublanguageid-all"

            # https://www.opensubtitles.org/en/search/sublanguageid-all/offset-5520/sort-10/asc-0
            # sort-0 = sort by movie name
            # sort-2 = sort by number of parts (1cd, 2cd, 3cd, ...)
            # sort-5 = sort by upload date
            # sort-6 = sort by subtitle rating
            # sort-7 = sort by download count
            # sort-8 = sort my movie rating
            # sort-9 = sort by uploader
            # sort-10 = sort by number of comments
            # not working:
            # sort-1 = sort by languagename
            # sort-3 = sort by ???
            # sort-4 = sort by ???
            # sort-11 = sort by ???
            # sort-12 = sort by ???
            # sort-13 = ignored

            """
            # FIXME something is broken, retrying does not help
            # retry loop
            # FIXME the page load can take forever...
            # TODO block images/scripts/styles
            while True:
                # TODO print page number, instead of index_offset
                # page 1 of 25
                # page 2 of 25
                # page 3 of 25
                # ...

                logger_print(f"index_offset {index_offset} of 1000: opening url {url}")
                # FIXME asyncio ERROR Exception in callback SingleCDPSocket._exc_handler(<Task finishe... cancelled>')>)
                # FIXME asyncio.exceptions.InvalidStateError: CANCELLED: <Future cancelled>
                try:
                    await asyncify(driver.get(url, timeout=120))
                    break

                #except TimeoutError:
                except Exception as e:

                    #logger_print(f"index_offset {index_offset} of 1000: got timeout -> retrying")
                    logger_print(f"index_offset {index_offset} of 1000: got exception {type(e).__name__}: {e} -> retrying")

                    # open new tab, close old tab
                    old_window = await asyncify(driver.current_window_handle)

                    # open new tab, switch to new tab
                    logger_print(f"index_offset {index_offset} of 1000: open new tab")
                    new_window_result = await asyncify(driver.switch_to.new_window('tab'))
                    await asyncio.sleep(1)

                    # switch to old tab
                    logger_print(f"index_offset {index_offset} of 1000: switch to old tab")
                    # FIXME ConnectionClosedError: sent 1000 (OK); no close frame received
                    await asyncify(driver.switch_to.window(old_window))
                    await asyncio.sleep(1)

                    # close old tab, switch to new tab
                    logger_print(f"index_offset {index_offset} of 1000: close old tab")
                    await asyncify(driver.close())
                    await asyncio.sleep(1)
            """

            page_source = None

            # retry loop
            # FIXME implement "retry on TimeoutError" in session.get
            got_response = False
            for retry_idx in range(100):

                # catch asyncio.exceptions.TimeoutError
                try:

                    async with await aiohttp_chromium_session.get(url, timeout=3*60) as resp:

                        page_source = await resp.text()

                    got_response = True
                    break

                except asyncio.exceptions.TimeoutError as e:
                    logger_print(f"index_offset {index_offset}: got TimeoutError {e} -> retrying {retry_idx}")
                    # retry
                    await asyncio.sleep(35)

            if not got_response:
                logger_print(f"index_offset {index_offset}: got TimeoutError -> giving up")
                continue

            # selenium_driverless: AttributeError: 'Chrome' object has no attribute 'implicitly_wait'
            """
            if selenium_webdriver.__package__ != "selenium_driverless":
                # set timeout for the following calls to driver.find_element
                driver.implicitly_wait(60)
            """

            """
            logger.debug(f"index_offset {index_offset}: waiting for page load")
            # wait for page load
            # wait for <div id="pager">
            logger.debug(f"index_offset {index_offset}: driver.find_element #pager ...")
            pager_elem = await asyncify(driver.find_element(By.ID, "pager", timeout=20))
            # WebElement("HTMLDivElement
            logger.debug(f"index_offset {index_offset}: driver.find_element #pager done: {pager_elem}")

            # sleep some more to wait for page load
            #await asyncio.sleep(5)

            page_source = await driver.page_source
            logger.debug(f"index_offset {index_offset}: page_source: " + repr(page_source[:50] + " ... " + page_source[-50:]))
            """



            # parse metadata: download counts, ratings, uploader
            # FIXME download counts and ratings are useless
            # when scraping the latest subs
            # because they mostly have zero downloads and zero votes
            logger_print(f"index_offset {index_offset} of 1000: parsing metadata")

            if True:
                # TODO optimize sub_metadata_regex_text
                # devmode: also print min_max_len_list
                min_max_len_list = [
                    [999999, 0],
                    [999999, 0],
                    [999999, 0],
                    [999999, 0],
                    [999999, 0],
                ]
                for match in sub_metadata_regex_pattern_devmode.finditer(page_source):
                    for i, g in enumerate(match.groups()):
                        l = len(g)
                        min_max_len_list[i][0] = min(min_max_len_list[i][0], l)
                        min_max_len_list[i][1] = max(min_max_len_list[i][1], l)
                logger_print(f"index_offset {index_offset} of 1000: min_max_len_list: {min_max_len_list}")

            subs_count = 0

            this_page_num_list = []

            for match in sub_metadata_regex_pattern.finditer(page_source):
                subs_count += 1
                sub_num = int(match.group(1))
                this_page_num_list.append(sub_num)
                download_count = int(match.group(2))
                num_votes = int(match.group(3))
                # rating is float between 0.0 and 10.0
                # convert to int between 0 and 100
                rating = int(float(match.group(4)) * 10)
                uploader_id = int(match.group(5))
                #print("sub_num, download_count, num_votes, rating = ", (sub_num, download_count, num_votes, rating))
                # TODO store these values with scrape_time_days_since_year_2000 in sqlite
                sql_query = "REPLACE INTO subs_downloads_ratings (num, downloads, rating, votes, uploader_id, scrape_day) VALUES (?, ?, ?, ?, ?, ?)"
                sql_args = (sub_num, download_count, rating, num_votes, uploader_id, scrape_time_days_since_year_2000)
                subs_downloads_ratings_cursor.execute(sql_query, sql_args)

            # FIXME commit less often. reduce number of disk writes
            subs_downloads_ratings_connection.commit()

            # NOTE last page can have less than 40
            #assert subs_count == 40, f"unexpected subs_count {subs_count}"

            #if subs_count < 40:
            # some subs can be missing
            # for example, a count of 39 can happen
            # this is a server bug
            if subs_count < 30:
                # every page should have 40 subs (default UI config)
                # FIXME this is probably a bug in sub_metadata_regex_text
                # where the "match all" ranges are too narrow
                # TODO use min_max_len_list to fix these ranges
                logger_print(f"index_offset {index_offset} of 1000: unexpected subs_count {subs_count}")
                # debug
                debug_html_path = f"{aiohttp_chromium_session.tempdir}/debug-offset-{index_offset}.{datetime_str()}.html"
                logger_print(f"index_offset {index_offset} of 1000: unexpected subs_count {subs_count}: writing {debug_html_path}")
                with open(debug_html_path, "w") as f:
                    f.write(page_source)

            # sub table row:
            # table#search_results > tbody > tr[onclick]
            # table#search_results > tbody > tr.change
            # table#search_results > tbody > tr.expandable

            # sub id: tr.id # example: "name228088"
            # sub rating: tr.childNodes[5].childNodes[0].innerText # example: "4.5"
            # sub download count: tr.childNodes[4].childNodes[0].innerText # example: "100x"

            # no, mostly we download zero subs
            # because we get only the metadata
            #logger_print(f"index_offset {index_offset} of 1000: downloading 40 subtitles")

            """
            await asyncify(driver.switch_to.window(driver_download_worker_window))
            """

            """
            FIXME blocked, too many requests
            https://dl.opensubtitles.org/en/download/sub/9843468
            returns html error page

            <div class="msg error">Sorry, maximum download count for IP: <b>250.158.192.75</b> exceeded.
            If you will continue trying to download, <b>your IP will be blocked</b> by our firewall.
            For more information read our <a href="/faq#antileech">FAQ</a> or contact us, if you think
            you should not see this error. This deny will be removed after around 24 hours, so be patient.</div>

            TODO detect this error, stop scraping

            TODO change_ipaddr

            TODO how many requests per day

            TODO also check for other error messages
            1958403938 subtitle file doesnt exists, you can contact admin GetSubtitleContents()
            1958403938 != num
            """

            # https://dl.opensubtitles.org/en/download/sub/12345
            # FIXME ERR_NETWORK_CHANGED Your connection was interrupted. A network change was detected.
            # this appears in the "download worker" tab
            # when the index pages have no new subs
            # = when we already have downloaded all subs of an index page
            # so we can probably ignore this error

            this_page_num_done_count = 0

            for num_idx, num in enumerate(this_page_num_list):

                if is_num_done(num, nums_done_ranges, nums_done_min):
                    continue

                this_page_num_done_count += 1

                logger_print(f"index_offset {index_offset} of 1000: downloading sub {num_idx + 1} of 40: {num}")

                url = f"https://dl.opensubtitles.org/en/download/sub/{num}"

                # retry loop
                # FIXME implement "retry on TimeoutError" in session.get
                got_response = False
                for retry_idx in range(100):

                    # catch asyncio.exceptions.TimeoutError
                    try:

                        async with await aiohttp_chromium_session.get(url, timeout=3*60) as resp:

                            #logger_print(f"index_offset {index_offset} of 1000: downloading sub {num_idx + 1} of 40: {num}: FIXME handle file download")
                            #await asyncio.sleep(999999)

                            logger_print(f"{num} resp._is_file: {resp._is_file}")

                            if not resp._is_file:

                                page_source = await resp.text()

                                logger_print(f"{num} page_source: {repr(page_source[:200])} ... {repr(page_source[-200:])}")

                                #logger_print(f"index_offset {index_offset} of 1000: downloading sub {num_idx + 1} of 40: {num}: FIXME resp._is_file = {resp._is_file}")
                                #logger_print("page_source:", page_source)
                                #await asyncio.sleep(999999)

                                # parse error html page

                                # subtitle file doesnt exists, you can contact admin GetSubtitleContents()

                                error_source = "subtitle file doesnt exists"
                                if error_source in page_source:
                                    logger_print(f"FIXME subtitle file doesnt exists. retry download later, or mark this sub as missing")
                                    await asyncio.sleep(99999999)

                                # Sorry, maximum download count for IP: <b>123.123.123.123</b> exceeded.
                                error_source = "Sorry, maximum download count for IP"
                                if error_source in page_source:
                                    logger_print(f"FIXME too many requests. wait and/or change_ipaddr")
                                    # TODO loop accounts: use next account for opensubtitles.org
                                    # change_ipaddr?
                                    # no. the rate-limiting is linked to my account
                                    # so change_ipaddr only helps
                                    # if i continue scraping without login = without cookies
                                    await asyncio.sleep(99999999)

                                error_source = "<b>Please confirm you are not robot.</b>"
                                if error_source in page_source:
                                    logger_print(f"FIXME too many requests. wait and/or change_ipaddr")
                                    await asyncio.sleep(99999999)

                                continue # download next file

                            #filename = response.content_filename
                            filename = resp._filename
                            # only prepend num
                            # risk: this can exceed the maximum filename length of 255 bytes
                            new_filename = f"{num}.{filename}"
                            parsed_filename = re.match(r"(.*)\.\(([0-9]+)\)\.zip", filename)
                            if parsed_filename:
                                # move num from end to start of filename
                                # moving num is needed to stay below the maximum filename length of 255 bytes
                                prefix, num_str = parsed_filename.groups()
                                if num_str == str(num):
                                    new_filename = f"{num}.{prefix}.zip"
                                else:
                                    logger_print(f"{num}: warning: sub number mismatch between url and filename")
                            #output_path = f"{new_subs_dir}/{new_filename}"
                            output_filepath = f"{new_subs_dir}/{new_filename}"

                            logger_print(f"moving download: {resp._filepath} -> {output_filepath}")

                            # OSError: [Errno 18] Invalid cross-device link
                            # os.rename only works if source and destination are on the same filesystem
                            #os.rename(resp._filepath, output_filepath)

                            shutil.move(resp._filepath, output_filepath)

                            nums_done_ranges.append(num)

                            # FIXME remove driver.switch_to.window

                        # success. dont retry
                        got_response = True
                        break

                    except asyncio.exceptions.TimeoutError as e:
                        logger_print(f"{num}: got TimeoutError {e} -> retrying {retry_idx}")
                        # retry
                        await asyncio.sleep(35)

                if not got_response:
                    logger_print(f"{num}: got TimeoutError -> giving up")
                    continue

            logger_print(f"index_offset {index_offset} of 1000: this_page_num_done_count {this_page_num_done_count}")

            # wait for all downloads to finish
            await asyncio.sleep(5) 

            # no. moved up
            r"""
            # find downloaded files
            # and add nums to nums_done_ranges
            for filename in os.listdir(aiohttp_chromium_session.downloads_path):
                if not filename.endswith(").zip"):
                    logger_print(f"ignoring download: no zip: {filename}")
                    continue
                # parse num from filename
                num = re.search(r"\(([0-9]+)\)\.zip$", filename)
                if not num:
                    logger_print(f"ignoring download: no num: {filename}")
                num = int(num.group(1))
                logger_print(f"found download {filename}")
                #found_download_num_list.append(num)
                nums_done_ranges.append(num)
                logger_print(f"moving download: {aiohttp_chromium_session.downloads_path}/{filename} -> {aiohttp_chromium_session.done_downloads_path}/{filename}")
                os.rename(
                    f"{aiohttp_chromium_session.downloads_path}/{filename}",
                    f"{aiohttp_chromium_session.done_downloads_path}/{filename}",
                )
            """

            # FIXME ConnectionClosedError: sent 1000 (OK); no close frame received
            # close other tabs
            """
            for window_handle in await asyncify(driver.window_handles):
                if window_handle == driver_main_window:
                    continue
                await asyncify(driver.switch_to.window(window_handle))
                await asyncify(driver.close())
            """

            """
            # switch back to main tab
            await asyncify(driver.switch_to.window(driver_main_window))
            """

            continue



            #raise NotImplementedError

            # find_element(By.TAG_NAME, "html")
            # find_element(By.ID, "some-id")
            # find_element(By.CLASS_NAME, "some-class")
            # driver.page_source
            # driver.current_url
            # driver.download_file(file_name: str, target_directory: str)
            #while (page_title := await asyncify(driver.title)) != "nowSecure":

            # TODO wait for page load
            # TODO click all download links
            # TODO go to next page, repeat

            # Synchronously Executes JavaScript
            #driver.execute_script(js_code)

            # selenium_driverless: AttributeError: 'Chrome' object has no attribute 'set_script_timeout'
            """
            if selenium_webdriver.__package__ != "selenium_driverless":
                driver.set_script_timeout(120)
            """

            """
            # create backup of chromium preferences
            chromium_preferences_path = f"{aiohttp_chromium_session.tempdir}/chromium-user-data/Default/Preferences"
            chromium_preferences_path_bak1 = f"{aiohttp_chromium_session.tempdir}/chromium-preferences.json.1"
            logger_print(f"writing {chromium_preferences_path_bak1}")
            with open(chromium_preferences_path) as f:
                chromium_preferences = json.load(f)
            with open(chromium_preferences_path_bak1, "w") as f:
                json.dump(chromium_preferences, f)
            logger_print(f"TODO: cat {chromium_preferences_path} | jq >{aiohttp_chromium_session.tempdir}/chromium-preferences.json.2; diff -u {aiohttp_chromium_session.tempdir}/chromium-preferences.json.{{1,2}}")
            """


            # no. this fails on error pages
            # opening the download links in new tabs
            # would grab the window focus on every click
            # so just use  the parsed list of subs
            # and open each download link with driver.get



            # TODO get live output from javascript console.log("...")
            js_code = (
                "// fetch subs\n"
                # this callback function will set js_result here in python
                "var set_js_result = arguments[arguments.length - 1];\n"
                "console.log('set_js_result:', set_js_result);\n"
                #"window.setTimeout(function(){ set_js_result('timeout') }, 3000);\n"
                "function sleep(ms) { return new Promise(resolve => setTimeout(resolve, ms)); };\n"
                #"var done_sub_nums = new Set();\n"
                "var nums_done_ranges = " + repr(nums_done_ranges) + ";\n"
                "var missing_nums_set = new Set(" + repr(missing_nums_list) + ");\n"
                #"var done_links = 0;\n"
                "function is_num_done(num) {\n"
                # all out-of-range nums are done
                "    if (num < " + str(nums_done_min) + ") return true;\n"
                "    for (const rangeOrNum of nums_done_ranges) {\n"
                "        if (num == rangeOrNum) return true;\n"
                "        if (isFinite(rangeOrNum)) continue; // rangeOrNum is a number\n"
                "        // rangeOrNum is a range\n"
                "        if (rangeOrNum[0] <= num && num <= rangeOrNum[1]) return true;\n"
                "        // shortcut: ranges are sorted\n"
                "        if (rangeOrNum[1] < num) return false;\n"
                "    }\n"
                "    return false;\n"
                "}\n"
                "var subLinkSelector = `a[href^='https://dl.opensubtitles.org/en/download/sub/']`;\n"
                "var nextPageLinkSelector = `#pager > div > strong+a`;\n"
                "async function scrape() {\n"
                "    while (!document.querySelector(nextPageLinkSelector)) {\n"
                "        // wait for page load\n"
                "        await sleep(1000);\n"
                "    }\n"
                "    var subLinkList = Array.from(document.querySelectorAll(subLinkSelector));\n"
                "    var clicked_num_list = [];\n"
                "    for (const a of subLinkList) {\n"
                "        const num = Number(a.href.split('/').slice(-1)[0]);\n"
                #"        if (done_sub_nums.has(num) == true) { continue; }\n"
                "        if (!missing_nums_set.has(num) && is_num_done(num)) { continue; }\n"
                #"        console.log(`clicking ${num}`);\n"
                # no. this fails on error pages
                #"        a.click();\n"
                # FIXME this steals focus to the chromium window
                # open link in new tab
                "        window.open(a.href, '_blank');\n"
                "        clicked_num_list.push(num);\n"
                # we must sleep some time between requests
                # otherwise chromium loses=ignores requests
                # TODO dynamic. the loss is dynamic
                # so we have to check the download folder
                # if all requests are done
                # FIXME sleep less
                "        await sleep(1000);\n"
                "        await sleep(5000);\n"
                #"        done_links++;\n"
                #"        done_sub_nums.add(num);\n"
                #"        if (done_links > 3) { break; } // debug\n"
                "    }\n"
                # NOTE navigating to next page will clear JS console
                #"    console.log(`clicking next page`);\n"
                #"    document.querySelector(nextPageLinkSelector).click();\n"
                "    return clicked_num_list;\n"
                "}\n"
                # no: JSEvalException: SyntaxError: await is only valid in async functions and the top level bodies of modules
                #"await scrape();\n"
                "scrape().then(clicked_num_list => set_js_result(clicked_num_list));\n"
                #"set_js_result('ok');\n"
            )

            logger_print(f"index_offset {index_offset} of 1000: downloading subs")

            clicked_num_list = []

            try:
                clicked_num_list = await asyncify(driver.execute_async_script(js_code, timeout=60*5))

                # success
                #keep_clicking_download_links = False

            except cdp_socket.exceptions.CDPError as e:

                logger_print(f"FIXME CDPError {e}")
                await asyncio.sleep(999999)
                raise e

                if e.code == -32000:
                    # FIXME avoid this by opening links in new tabs
                    # e.message == "Execution context was destroyed."
                    # https://dl.opensubtitles.org/en/download/sub/9842876 returns html error page
                    # 1958403943 subtitle file doesnt exists, you can contact admin GetSubtitleContents()
                    # wait for downloads to finish
                    await asyncio.sleep(5)
                    # go back
                    await asyncify(driver.execute_script("window.history.go(-1)"))

                    # repeat clicking download links
                    #keep_clicking_download_links = True

                    # find downloaded files
                    # and add nums to nums_done_ranges
                    for filename in os.listdir(aiohttp_chromium_session.downloads_path):
                        if not filename.endswith(").zip"):
                            logger_print(f"ignoring download: no zip: {filename}")
                            continue
                        # parse num from filename
                        num = re.search(r"\(([0-9]+)\)\.zip$", filename)
                        if not num:
                            logger_print(f"ignoring download: no num: {filename}")
                        num = int(num.group(1))
                        logger_print(f"found download {filename}")
                        #found_download_num_list.append(num)
                        nums_done_ranges.append(num)
                        shutil.move(
                            f"{aiohttp_chromium_session.downloads_path}/{filename}",
                            f"{aiohttp_chromium_session.done_downloads_path}/{filename}",
                        )

                else:
                    logger_print(f"FIXME CDPError {e}")
                    await asyncio.sleep(999999)
                    raise e

            except Exception as e:
                logger_print(f"FIXME Exception {type(e).__name__}: {e}")
                await asyncio.sleep(999999)
                raise e

            logger.debug(f"index_offset {index_offset}: downloading subs done: " + repr(clicked_num_list))

            this_page_num_downloads = len(clicked_num_list)

            # update nums_done_ranges
            if len(clicked_num_list) == 1:
                num = clicked_num_list[0]
                nums_done_ranges.append(num)
            elif len(clicked_num_list) > 1:
                # FIXME nums are sorted in descending order
                num_1 = clicked_num_list[0]
                num_2 = clicked_num_list[-1]
                nums_done_ranges.append([num_1, num_2])

            # wait for downloads to finish
            await asyncio.sleep(5)

            # retry loop
            while True:

                # check the downloads folder
                # compare with clicked_num_list
                found_download_num_list = []
                missing_download_num_list = clicked_num_list[:]
                for filename in os.listdir(aiohttp_chromium_session.downloads_path):
                    if not filename.endswith(").zip"):
                        logger_print(f"ignoring download: no zip: {filename}")
                        continue
                    # parse num from filename
                    num = re.search(r"\(([0-9]+)\)\.zip$", filename)
                    if not num:
                        logger_print(f"ignoring download: no num: {filename}")
                    num = int(num.group(1))
                    logger_print(f"found download {filename}")
                    found_download_num_list.append(num)
                    missing_download_num_list.remove(num)
                    shutil.move(
                        f"{aiohttp_chromium_session.downloads_path}/{filename}",
                        f"{aiohttp_chromium_session.done_downloads_path}/{filename}",
                    )

                if not missing_download_num_list:
                    # all clicked nums were downloaded
                    break

                # some clicked nums were not downloaded
                # retry download
                js_code = (
                    "// fetch subs\n"
                    # this callback function will set js_result here in python
                    "var set_js_result = arguments[arguments.length - 1];\n"
                    #"window.setTimeout(function(){ set_js_result('timeout') }, 3000);\n"
                    "function sleep(ms) { return new Promise(resolve => setTimeout(resolve, ms)); };\n"
                    "var missing_download_num_list = " + repr(missing_download_num_list) + ";\n"
                    "var missing_download_num_set = new Set(missing_download_num_list);\n"
                    "var subLinkSelector = `a[href^='https://dl.opensubtitles.org/en/download/sub/']`;\n"
                    "var nextPageLinkSelector = `#pager > div > strong+a`;\n"
                    "async function scrape() {\n"
                    "    while (!document.querySelector(nextPageLinkSelector)) {\n"
                    "        // wait for page load\n"
                    "        await sleep(1000);\n"
                    "    }\n"
                    "    var subLinkList = Array.from(document.querySelectorAll(subLinkSelector));\n"
                    "    for (const a of subLinkList) {\n"
                    "        const num = Number(a.href.split('/').slice(-1)[0]);\n"
                    "        if (!missing_download_num_set.has(num)) { continue; }\n"
                    #"        console.log(`clicking ${num}`);\n"
                    # no. this fails on error pages
                    #"        a.click();\n"
                    # open link in new tab
                    "        window.open(a.href, '_blank');\n"
                    "        await sleep(1000);\n"
                    "    }\n"
                    "    return 'ok';\n"
                    "}\n"
                    "scrape().then(result => set_js_result(result));\n"
                )
                # FIXME close all the new tabs

                logger_print(f"index_offset {index_offset} of 1000: retrying download of {missing_download_num_list}")
                js_result = await asyncify(driver.execute_async_script(js_code, timeout=60*5))
                logger_print(f"index_offset {index_offset} of 1000: retrying download done:", repr(js_result))

                clicked_num_list = missing_download_num_list

                # wait for downloads to finish
                await asyncio.sleep(5)

            if this_page_num_downloads > 0:
                logger_print(f"index_offset {index_offset} of 1000: done downloads: {this_page_num_downloads}")

            #await asyncio.sleep(88888888)
            #raise NotImplementedError

        # no. continue scraping missing subs
        # done scraping
        #raise SystemExit

        if chromium_cookie_jar:
            logger_print("init scraper: saving cookies to", chromium_cookie_jar._file_path)
            chromium_cookie_jar.save()

        #if opensubtitles_org_logins and not daily_quota_is_exceeded:
        if False:

            # TODO loop logins
            if options.username:
                logger_print(f"getting opensubtitles.org login for username {repr(options.username)}")
                username, password = next(
                    (x for x in opensubtitles_org_logins if x[0] == options.username),
                    #opensubtitles_org_logins[0]
                )
            else:
                username, password = opensubtitles_org_logins[0]

            cookies_txt_path = f"cookies/opensubtitles.org-cookies.{username}.txt"

            cookie_jar = aiohttp_chromium.MozillaCookieJar()

            # FIXME UnboundLocalError: local variable 'driver' referenced before assignment
            # copy cookies from driver to cookiejar
            # cookiejar is a list of dicts
            cookie_jar.extend(await driver.get_cookies())

            # save cookies
            logger_print("saving cookies to", cookies_txt_path)
            cookie_jar.save(cookies_txt_path)

            del cookie_jar



        # no. continue scraping missing subs
        #raise NotImplementedError



    # scrape missing subs in ascending order

    logger_print(f"scraping missing subs in ascending order")

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

    # limit parallel downloads
    logger_print(f"creating semaphore with max_concurrency={max_concurrency}")
    semaphore = asyncio.Semaphore(max_concurrency)

    aiohttp_session_args = dict()
    # fix: aiohttp.client_exceptions.ClientConnectorCertificateError: Cannot connect to host dl.opensubtitles.org:443 ssl:True [SSLCertVerificationError: (1, '[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self-signed certificate in certificate chain (_ssl.c:997)')]
    #aiohttp_session_args["verify_ssl"] = False
    aiohttp_session_args["headers"] = {
        **default_request_headers,
        "User-Agent": user_agent,
    }



    if opensubtitles_org_logins and not daily_quota_is_exceeded:

        # TODO loop logins
        if options.username:
            logger_print(f"getting opensubtitles.org login for username {repr(options.username)}")
            username, password = next(
                (x for x in opensubtitles_org_logins if x[0] == options.username),
                #opensubtitles_org_logins[0]
            )
        else:
            username, password = opensubtitles_org_logins[0]

        # load stored cookies from cookies.txt file
        # https://stackoverflow.com/questions/14742899/using-cookies-txt-file-with-python-requests
        # cookies/opensubtitles.org-cookies.milaxnuts.txt
        cookies_txt_path = f"cookies/opensubtitles.org-cookies.{username}.txt"
        #cookies_pickle_path = f"cookies/opensubtitles.org-cookies.{username}.pickle"

        jar = None
        if os.path.exists(cookies_txt_path):
            # load cookies 2
            # TODO deduplicate with "init scraper: loading cookies"?
            logger_print(f"main: loading cookies from {cookies_txt_path}")
            jar = AiohttpMozillaCookieJar()
            jar.load(cookies_txt_path)
            opensubtitles_org_login_cookies_txt_path = cookies_txt_path
            opensubtitles_org_login_cookie_jar = jar
        # pickle is obscure and unneeded for cookies
        #elif os.path.exists(cookies_pickle_path):
        #    jar = aiohttp.CookieJar()
        #    jar.load(cookies_pickle_path)
        else:
            raise NotImplementedError("no cookie file was found. FIXME login with headful scraper")

        # init session.cookie_jar
        # TODO modify session.cookie_jar later?
        #session = aiohttp.ClientSession(cookie_jar=jar)
        # FIXME AttributeError: 'MozillaCookieJar' object has no attribute 'filter_cookies'
        aiohttp_session_args["cookie_jar"] = opensubtitles_org_login_cookie_jar

    elif opensubtitles_com_logins:

        raise NotImplementedError("opensubtitles.com sucks")

        # get session token
        # TODO loop logins
        username, password, apikey = opensubtitles_com_logins[0]
        url = "https://api.opensubtitles.com/api/v1/login"
        data = {
            "username": username,
            "password": password,
        }
        headers = {
            "User-Agent": "", # <<{{APP_NAME}} v{{APP_VERSION}}>>
            "Api-Key": apikey,
        }
        response = await aiohttp_session.post(url, json=data, headers=headers)
        response_status = response.status
        response_type = response.headers.get("Content-Type")
        response_data = await response.json()
        logger_print(f"api.opensubtitles.com login response:", json.dumps(response_data, indent=2))
        logger_print(f"api.opensubtitles.com login user.allowed_downloads:", response_data["user"]["allowed_downloads"])
        logger_print(f"api.opensubtitles.com login user.vip:", response_data["user"]["vip"])
        assert response_data["status"] == 200
        assert response_data["user"]["vip"] == True
        assert response_data["token"]
        opensubtitles_com_login_headers = {
            "User-Agent": "", # <<{{APP_NAME}} v{{APP_VERSION}}>>
            "Api-Key": apikey,
            "Authorization": "Bearer " + response_data["token"],
        }



    async with aiohttp.ClientSession(**aiohttp_session_args) as aiohttp_session:

        # loop download batches
        while True:

            if options.last_num == None:

                # estimate last_num
                # with a "growth rate" of 1000 new subs per day
                with open("last-sub-add-date.txt", "r") as f:
                    # 9792008|2023-11-19 09:11:56
                    # 9998553|2024-04-24 08:59:27
                    sub_num, sub_date_str = f.read().strip().split("|")
                    sub_num = int(sub_num)
                    sub_date = datetime.datetime.strptime(sub_date_str + " +0000", "%Y-%m-%d %H:%M:%S %z")
                    sub_time = sub_date.timestamp()
                    dt = time.time() - sub_time
                    dt_days = dt / (60 * 60 * 24)
                    new_subs_per_day = 1000
                    dn = round(new_subs_per_day * dt_days)
                    options.last_num = sub_num + dn
                    logger_print(f"guessing options.last_num {options.last_num} from sub_num {sub_num} on {sub_date_str}")

            # avoid this request
            # "estimate last_num" is good enough
            #if options.last_num == None:
            if False:
                # first request
                # this can already be blocked by captcha
                logger_print(f"getting options.last_num from remote")
                #url = "https://www.opensubtitles.org/en/search/subs"
                # "new subtitles" page
                # TODO screen parsing:
                # find position of the "downloads" column
                # and download all missing subs from urls like
                # https://www.opensubtitles.org/en/subtitleserve/sub/12345
                #url_path = "/en/search/subs"
                url_path = "/en/search/sublanguageid-all"
                url = "https://www.opensubtitles.org" + url_path

                response = None
                response_status = None
                response_type = None
                response_text = None
                response_done = False

                num_retries = 10
                #num_retries = 1

                retry_sleep_seconds = 15

                def do_retry(response, response_status, response_type, response_text):
                    if response_status in {503}:
                        return True
                    return False

                # retry loop
                for retry_step in range(1, 1 + num_retries):

                    if options.proxy_provider == None:
                        # no proxy
                        response = await aiohttp_session.get(url)
                        response_status = response.status
                        response_type = response.headers.get("Content-Type")
                        # TODO response_headers?
                        # TODO handle binary response
                        response_text = await response.text()

                    elif options.proxy_provider == "chromium":
                        #response = await aiohttp_chromium_session.get(url)
                        # TODO retry loop
                        try:
                            response = await aiohttp_chromium_session.get(url)
                        except asyncio.exceptions.TimeoutError as e:
                            logger_print(f"main_scraper: aiohttp_chromium_session.get({url}) -> TimeoutError {e}")
                            #raise # TODO why?
                            # FIXME session.get hangs at aiohttp_chromium.client DEBUG _request: response_queue.get
                            # FIXME the scraper tab is not marked as "old" and reused
                            logger_print(f"main_scraper: aiohttp_chromium_session.get -> TimeoutError {e} -> retrying")
                            # FIXME close old tab on TimeoutError
                            await asyncio.sleep(retry_sleep_seconds)
                            continue # retry
                        response_status = response.status
                        response_type = response.headers.get("Content-Type")
                        # TODO response_headers?
                        # TODO handle binary response
                        response_text = await response.text()

                        async def response_cleanup_chromium():
                            await response.__aexit__(None, None, None)
                        response_cleanup = response_cleanup_chromium
                        # TODO session_cleanup

                    #elif options.proxy_provider == "chromium":
                    elif False:
                        # call get_response___chromium
                        logger_print(f"main_scraper: calling aiohttp_chromium_session.get_response({repr(url)})")
                        response = await aiohttp_chromium_session.get_response(
                            url,
                            #return_har_path=True, # debug
                        )
                        response_status = response.status
                        response_type = response.headers.get("Content-Type")
                        # TODO handle binary response
                        # FIXME handle redirects to captcha page
                        # see also docs/captchas.md
                        if response.status == 200:
                            response_text = await response.text()
                        elif response.status == 301:
                            # first response is a redirect
                            # probably the result is a captcha page
                            raise NotImplementedError("FIXME ideally solve this in aiohttp_chromium_session.get_response")

                    else:
                        raise NotImplementedError(f"options.proxy_provider {options.proxy_provider}")

                    if do_retry(response, response_status, response_type, response_text):
                        logger_print(f"{url_path} {response_status} -> request failed. retrying in {retry_sleep_seconds} seconds")
                        time.sleep(retry_sleep_seconds)
                        await response_cleanup()
                        continue

                    response_done = True
                    break

                if response_done == False:
                    logger_print(f"{url_path} {response_status} -> fatal error. giving up after {num_retries} retries")
                    await response_cleanup()
                    #await session_cleanup() # TODO
                    sys.exit(1)

                # response_status can be 429 Too Many Requests -> fatal error
                if response_status == 403:
                    if response_text.startswith("""<!DOCTYPE html><html lang="en-US"><head><title>Just a moment...</title><meta http-equiv="Content-Type" content="text/html; charset=UTF-8"><meta http-equiv="X-UA-Compatible" content="IE=Edge"><meta name="robots" content="noindex,nofollow"><meta name="viewport" content="width=device-width,initial-scale=1"><link href="/cdn-cgi/styles/challenges.css" rel="stylesheet"></head><body class="no-js"><div class="main-wrapper" role="main"><div class="main-content"><noscript><div id="challenge-error-title"><div class="h2"><span class="icon-wrapper"><div class="heading-icon warning-icon"></div></span><span id="challenge-error-text">Enable JavaScript and cookies to continue</span></div></div></noscript></div></div><script>(function(){window._cf_chl_opt="""):
                        logger_print(f"{url_path} 403 Access Denied [blocked by cloudflare] -> fatal error")
                        await response_cleanup()
                        #await session_cleanup() # TODO
                        sys.exit(1)
                    logger_print(f"{url_path} 403 Access Denied -> fatal error")
                    await response_cleanup()
                    #await session_cleanup() # TODO
                    sys.exit(1)
                if response_status == 429:
                    logger_print(f"{url_path} 429 Too Many Requests -> fatal error")
                    await response_cleanup()
                    #await session_cleanup() # TODO
                    sys.exit(1)
                if response_status == 503:
                    # FIXME retry some times
                    logger_print(f"{url_path} 503 Service Unavailable -> fatal error")
                    await response_cleanup()
                    #await session_cleanup() # TODO
                    sys.exit(1)

                if response_status != 200:
                    await response_cleanup()
                    raise Exception(f"{url_path} unexpected response_status {response_status}")

                if response_type != "text/html; charset=UTF-8":
                    await response_cleanup()
                    raise Exception(f"{url_path} unexpected response_type {repr(response_type)}")

                r"""
                # parse /en/search/subs
                remote_nums = re.findall(r'href="/en/subtitles/(\d+)/', await response.text())
                logger.debug(f"{url_path} remote_nums {repr(remote_nums)}")
                options.last_num = max(map(int, remote_nums))
                logger_print(f"{url_path} options.last_num", options.last_num)
                """
                # parse /en/search/sublanguageid-all
                # href="/en/subtitleserve/sub/12345"
                print("re.findall /en/subtitleserve/sub/nnnn", re.findall(r'href="/en/subtitleserve/sub/(\d+)"', await response.text()))
                remote_nums = list(map(int, re.findall(r'href="/en/subtitleserve/sub/(\d+)"', await response.text())))
                logger.debug(f"{url_path} remote_nums {repr(remote_nums)}")
                # TODO? rename to options.latest_num
                options.last_num = remote_nums[0]
                logger_print(f"{url_path} options.last_num", options.last_num)
                # TODO? use all remote_nums as queue
                # then go to next pages:
                # https://www.opensubtitles.org/en/search/sublanguageid-all/offset-40
                # https://www.opensubtitles.org/en/search/sublanguageid-all/offset-80
                # https://www.opensubtitles.org/en/search/sublanguageid-all/offset-120
                # ...
                # note: the offset is relative to the latest subtitle (options.last_num)
                # so when new subs are ADDED while we are scraping
                # then we see some duplicate sub ids
                # but: when subs are REMOVED while we are scraping (yes that is possible)
                # then we miss some sub ids
                # so instead of using the default offsets (0, 40, 80, 120, 160, ...)
                # we use smaller offsets (example: 0, 30, 60, 90, 120, 150, ...)
                # so we get some overlap, so we always get at least one duplicate ID
                # to ensure continuitiy of the sub ids
                # if we dont get even one duplicate id between previous page and this page
                # then we have to seek back to get the missing sub ids
                # all this is stupid, complex, expensive...
                # and maybe we should cache the parsed sub ids somewhere
                # i can only repeat: opensubtitles is run by idiots.
                # these people are too stupid to implement proper pagination
                # based on a stable offset = the subtitle ID
                #
                # https://www.w3.org/TR/selectors-3/#selectors
                # E[foo^="bar"]	an E element whose "foo" attribute value begins exactly with the string "bar"
                # E[foo$="bar"]	an E element whose "foo" attribute value ends exactly with the string "bar"
                # E[foo*="bar"]	an E element whose "foo" attribute value contains the substring "bar"
                # ->
                # sub download links:
                #   a[href^="/en/subtitleserve/sub/"]
                # next page link:
                #   .pager-list strong+a
                #
                # use javascript console to click link
                # example: click the first download link
                #   Array.from(document.querySelectorAll('a[href^="/en/subtitleserve/sub/"]'))[0].click()
                #
                # click multiple links
                """
                function sleep(ms) { return new Promise(resolve => setTimeout(resolve, ms)); };
                var done_sub_nums = new Set([9801862, 9801857, 9801820, 9801821]);
                var done_links = 0;
                for (const a of Array.from(document.querySelectorAll('a[href^="/en/subtitleserve/sub/"]'))) {
                    const num = Number(a.href.split("/").slice(-1)[0]);
                    if (done_sub_nums.has(num) == true) { continue; }
                    console.log(`clicking ${num}`);
                    a.click();
                    await sleep(3000);
                    done_links++;
                    done_sub_nums.add(num);
                    if (done_links > 3) { break; } // debug
                }
                """
                # working. chrome popup: page wants to download multiple files -> allow
                # TODO download 20 subs, then try next download, solve captcha, download 20 subs, ...

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
                    logger.debug(f"num_stack = missing_numbers")
                    num_stack = missing_numbers
                    break

                # add numbers to the stack
                #num_stack_first = num_stack_last + 1
                num_stack_last = num_stack_first + options.sample_size
                # next iteration
                #num_stack_first = num_stack_last + 1

                if options.last_num and num_stack_last > options.last_num:
                    logger_print(f"lowering num_stack_last {num_stack_last} to options.last_num {options.last_num}")
                    num_stack_last = options.last_num
                logger.debug(f"stack range: ({num_stack_first}, {num_stack_last})")
                if num_stack_last < num_stack_first:
                    logger.debug(f"stack range is empty")
                    break
                def filter_num(num):
                    return (
                        num not in nums_done_set
                        # already handled by num_stack_last
                        #and num <= options.last_num
                    )

                if metadata_db_cur:
                    sql_query = f"select IDSubtitle from subz_metadata where IDSubtitle between {num_stack_first} and {num_stack_last}"
                    num_stack_expand = (
                        map(lambda row: row[0],
                            metadata_db_cur.execute(sql_query).fetchall()
                        )
                    )
                else:
                    num_stack_expand = (
                        range(num_stack_first, num_stack_last + 1)
                        #random.sample(range(num_stack_first, options.last_num + 1), options.sample_size)
                    )

                num_stack_expand = list(
                    filter(filter_num,
                        range(num_stack_first, num_stack_last + 1),
                        #random.sample(range(num_stack_first, options.last_num + 1), options.sample_size)
                    )
                )

                #logger.debug(f"num_stack_expand: {repr(num_stack_expand[:5])} ... {repr(num_stack_expand[-5:])}")
                logger.debug(f"num_stack_expand: {num_stack_expand[:5]} ... {num_stack_expand[-5:]}")
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

            #logger.debug(f"num_stack: {num_stack[:10]} ...")
            #logger.debug(f"num_stack: {repr(num_stack[:10])} ... {repr(num_stack[-10:])}")
            logger.debug(f"num_stack: {num_stack[:10]} ... {num_stack[-10:]}")

            if fetch_nums_in_random_order:
                # scraping nums in random order is required to bypass blocking
                random.shuffle(num_stack)
            else:
                # scraping nums in linear order helps to complete shards earlier
                # when scraping in random order, we get many incomplete shards
                # TODO verify scrape nums in ascending order
                num_stack.sort()

            # TODO add options.num_requests
            # quickfix: increase options.num_downloads to 999999
            # and let scraper run until its blocked
            if options.num_downloads:
                num_remain = options.num_downloads - num_requests_done_ok
                logger_print(f"done: {num_requests_done_ok}. remain: {num_remain}")
                if num_remain <= 0:
                    logger_print(f"done {options.num_downloads} nums")
                    raise SystemExit
                num_stack = num_stack[0:num_remain]
                logger.debug(f"num_stack: {num_stack}")

            logger_print(f"batch size: {len(num_stack)}")
            # no. too verbose
            #logger.debug(f"batch: {num_stack}")
            logger.debug(f"batch: {num_stack[:10]} ... {num_stack[-10:]}")

            # fetch subs
            return_value_list = None
            if max_concurrency == 1:
                # serial processing
                return_value_list = []
                while num_stack:
                    num = num_stack.pop()
                    return_value_list.append(await fetch_num(num, aiohttp_session, semaphore, dt_download_list, t2_download_list, html_errors, config))
            else:
                # parallel processing
                tasks = []
                while num_stack:
                    num = num_stack.pop()
                    task = asyncio.create_task(fetch_num(num, aiohttp_session, semaphore, dt_download_list, t2_download_list, html_errors, config))
                    tasks.append(task)
                return_value_list = await asyncio.gather(*tasks)

            # TODO show progress
            #logger_print("return_value_list", return_value_list)
            pause_scraper = False
            do_change_ipaddr = False
            # process num result
            # process return values from fetch_num
            for return_value in return_value_list:
                # FIXME why (num_requests_done == 0) after run
                num_requests_done += 1
                if type(return_value) == dict:
                    result_dict = return_value
                    num = result_dict["num"]
                    if result_dict.get("ok") == True:
                        # FIXME this is too high
                        # stats: 1000 requests + 1000 ok + 0 fail + 0 dmca + quota diff 94
                        num_requests_done_ok += 1
                        # TODO off by one error?
                        diff_download_quota = None
                        #if last_download_quota != None and first_download_quota != None:
                        #    diff_download_quota = first_download_quota - last_download_quota
                        if last_download_quota != None and last_download_quota_bak != None:
                            diff_download_quota = last_download_quota_bak - last_download_quota
                            logger_print(f"{num} diff_download_quota", diff_download_quota)
                            # assert diff_download_quota == 1
                            # quota has changed -> request was successful
                            num_requests_done_ok += 1
                        try:
                            missing_numbers.remove(num)
                        except ValueError:
                            pass
                    else:
                        num_requests_done_fail += 1
                    if result_dict.get("dmca") == True:
                        num_requests_done_dmca += 1
                        # missing_numbers can contain "dmca" files
                        try:
                            missing_numbers.remove(num)
                        except ValueError:
                            pass
                    if result_dict.get("not_found") == True:
                        # missing_numbers can contain deleted files
                        try:
                            missing_numbers.remove(num)
                        except ValueError:
                            pass
                    if result_dict.get("retry") == True:
                        num_stack.append(num)
                    if result_dict.get("pause") == True:
                        pause_scraper = True
                    if result_dict.get("change_ipaddr") == True:
                        do_change_ipaddr = True

                '''
                if return_value == None:
                    # success
                    #num_requests_done_ok += 1

                    # FIXME return {"num": num, "ok": True}
                    """
                    if missing_numbers:
                        try:
                            missing_numbers.remove(num)
                        except ValueError:
                            pass
                    """
                    continue
                if return_value == False:
                    # response 404 is not counted in quota
                    continue
                if type(return_value) == int:
                    # retry
                    num_stack.append(return_value)
                '''

            if do_change_ipaddr:
                logger_print("changing IP address")
                await change_ipaddr()

            # FIXME this has no effect. this is too late
            # here, a list of results was returned from many fetch_num calls
            #if pause_scraper:
            if False:
                t_sleep = random.randrange(20, 60)
                logger_print(f"pausing scraper for {t_sleep} seconds")
                #time.sleep(t_sleep)
                await asyncio.sleep(t_sleep)
                # reset t2 values
                while t2_download_list:
                    t2_download_list.pop()

    if opensubtitles_org_login_cookie_jar:
        # TODO loop logins
        # TODO fix opensubtitles_org_login_cookie_jar.save
        logger_print(f"saving cookies to {opensubtitles_org_login_cookies_txt_path}")
        opensubtitles_org_login_cookie_jar.save(opensubtitles_org_login_cookies_txt_path)



asyncio.get_event_loop().run_until_complete(main())

#asyncio.run(main())
