#!/usr/bin/env python3

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
import asyncio # pyppeteer

import requests
import magic # libmagic



# captcha after 30 requests
#proxy_provider = "chromium"

proxy_provider = "pyppeteer"



pyppeteer_headless = True
pyppeteer_headless = False # debug



#proxy_provider = "scrapfly.io"
proxy_scrapfly_io_api_key = "scp-live-65607ed58a5449f791ba56baa5488098"

#proxy_provider = "scrapingdog.com"
api_key_scrapingdog_com = "643f9f3b575aa419c1d7218a"

#proxy_provider = "webscraping.ai"
api_key_webscraping_ai = "b948b414-dd1d-4d98-8688-67f154a74fe8"
webscraping_ai_option_proxy = "datacenter"
#webscraping_ai_option_proxy = "residential"

#proxy_provider = "zenrows.com"
api_key_zenrows_com = "88d22df90b3a4c252b480dc8847872dac59db0e0"

#proxy_provider = "scraperbox.com"
proxy_scraperbox_com_api_key = "56B1354FD63EB435CA1A9096B706BD55"

#proxy_provider = "scrapingant.com"
api_key_scrapingant_com = "6ae0de59fad34337b2ee86814857278a"



# TODO verify all 404 URLs



new_subs_dir = "new-subs"

last_num_db = 9180517 # last num in opensubs.db
print("last_num_db", last_num_db)

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

logging.basicConfig(
    format='%(asctime)s %(levelname)s %(message)s',
    #level="DEBUG",
    level="INFO",
)

logger = logging.getLogger("fetch-subs")



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


def new_session():
    requests_session = requests.Session()
    return requests_session
    # https://httpbin.org/headers
    # chromium headers:
    requests_session.headers = {
        #'user-agent': user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9",
        #"Host": "httpbin.org",
        "Sec-Ch-Ua": "\"Not A(Brand\";v=\"24\", \"Chromium\";v=\"110\"",
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": "\"Linux\"",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
        #"X-Amzn-Trace-Id": "Root=1-xxx"
    }
    return requests_session


async def main():

    if proxy_provider == "zenrows.com":
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    elif proxy_provider == "pyppeteer":
        # puppeteer is old, chrome only, but stealth plugin works?
        import pyppeteer
        # https://github.com/towry/n/issues/148
        # https://pypi.org/project/pyppeteer-stealth/
        # https://github.com/MeiK2333/pyppeteer_stealth
        sys.path.append("pyppeteer_stealth") # local version
        import pyppeteer_stealth
        print("pyppeteer_stealth", pyppeteer_stealth)
        # TODO test sites:
        # https://abrahamjuliot.github.io/creepjs/
        # http://f.vision/
        # via https://github.com/QIN2DIM/undetected-playwright/issues/2

        print("pyppeteer.launch")
        pyppeteer_browser = await pyppeteer.launch(
            # https://pptr.dev/api/puppeteer.puppeteerlaunchoptions
            headless=pyppeteer_headless,
            executablePath=os.environ["PUPPETEER_EXECUTABLE_PATH"],
            args=[
                # no effect
                #"--disable-blink-features=AutomationControlled",
            ],
        )

        print("pyppeteer_browser.newPage")
        pyppeteer_page = await pyppeteer_browser.newPage()

        # TODO why is this not working?
        print("pyppeteer_stealth.stealth")
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
            print(f"done: {path}")

        #await pyppeteer_browser.close()

        raise NotImplementedError

    #elif proxy_provider == "playwright":

    first_num_file = last_num_db
    last_num_file = 1

    os.makedirs(new_subs_dir, exist_ok=True)
    nums_done = []

    for filename in os.listdir(new_subs_dir):
        #match = re.fullmatch(r"([0-9]+)\.(.+\.)?zip", filename)
        match = re.fullmatch(r"([0-9]+)\..*", filename)
        if not match:
            continue
        num = int(match.group(1))
        nums_done.append(num)
        if num > last_num_file:
            last_num_file = num
        if num < first_num_file:
            first_num_file = num

    nums_done = sorted(nums_done)

    print("first_num_file", first_num_file)
    print("last_num_file", last_num_file)

    requests_session = new_session()

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

    print("num_stack_last", num)

    num_stack_first = num_stack_last

    downloads_since_change_ipaddr = 0

    # json file from https://www.useragents.me/
    with open("user_agents.json") as f:
        user_agents = json.load(f)
        # there is also x["pct"] = frequency of user agent in percent
        # but we dont need that value
        user_agents = list(map(lambda x: x["ua"], user_agents))

    user_agent = random.choice(user_agents)

    num_stack_size = 1000 # randomize the last 3 digits
    #num_stack_size = 100 # randomize the last 2 digits

    nums_done_set = set(nums_done)
    num_stack = []
    dt_download_list = collections.deque(maxlen=100) # average the last 100 dt

    #print("nums_done", nums_done)

    # loop subtitle numbers

    while True:

        while not num_stack: # while stack is empty
            # add random numbers to the stack
            num_stack_first = num_stack_last + 1
            num_stack_last = num_stack_first + num_stack_size
            num_stack = list(
                filter(lambda num: num not in nums_done_set,
                    range(num_stack_first, num_stack_last + 1)
                )
            )
            #print("num_stack", num_stack)
            random.shuffle(num_stack)

        t1_download = time.time()

        num = num_stack.pop()

        filename_glob = f"{new_subs_dir}/{num}.*"
        filename_zip = f"{new_subs_dir}/{num}.zip"
        filename_notfound = f"{new_subs_dir}/{num}.not-found"

        # handled by nums_done?
        # check again to make sure:
        existing_output_files = glob.glob(filename_glob)
        if len(existing_output_files) > 0:
            logger.info(f"{num} output file exists: {existing_output_files}")
            continue

        filename = filename_zip
        url = f"https://dl.opensubtitles.org/en/download/sub/{num}"
        proxies = {}
        requests_get_kwargs = {}
        content_type = None
        status_code = None
        content_disposition = None
        response_headers = None
        response_content = None

        if proxy_provider == "scrapingant.com":
            query = urllib.parse.urlencode({
                "url": url,
                "x-api-key": api_key_scrapingant_com,
                "browser": "false",
            })
            url = f"https://api.scrapingant.com/v2/general?{query}"
            response = requests.get(url, **requests_get_kwargs)
            status_code = response.status_code

        elif proxy_provider == "zenrows.com":
            proxy = f"http://{api_key_zenrows_com}:@proxy.zenrows.com:8001"
            proxies = {"http": proxy, "https": proxy}
            requests_get_kwargs["proxies"] = proxies
            requests_get_kwargs["verify"] = False
            response = requests.get(url, **requests_get_kwargs)
            status_code = response.status_code
            content_type = response.headers.get("Zr-Content-Type")
            content_disposition = response.headers.get("Zr-Content-Disposition")

        elif proxy_provider == "scrapingdog.com":
            query = urllib.parse.urlencode({
                "url": url,
                "api_key": api_key_scrapingdog_com,
                "dynamic": "false", # dont eval javascript
            })
            url = f"https://api.scrapingdog.com/scrape?{query}"

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

        elif proxy_provider == "webscraping.ai":
            # https://docs.webscraping.ai/reference/gethtml
            query = urllib.parse.urlencode({
                "url": url,
                "api_key": api_key_webscraping_ai,
                "proxy": webscraping_ai_option_proxy,
                "js": "false", # dont eval javascript
            })
            url = f"https://api.webscraping.ai/html?{query}"

            response = requests.get(url, **requests_get_kwargs)

            status_code = response.status_code
            logger.info(f"{num} status_code: {status_code}")

            logger.info(f"{num} headers: {response.headers}")

        elif proxy_provider == "scrapfly.io":
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

        elif proxy_provider == "scraperbox.com":
            # https://scraperbox.com/dashboard
            query = urllib.parse.urlencode({
                "url": url,
                "token": proxy_scraperbox_com_api_key,
                #"javascript_enabled": "true",
                #"proxy_location": "all",
                #"residential_proxy": "true",
            })
            url = f"https://scraperbox.com/api/scrape?{query}"

            response = requests.get(url, **requests_get_kwargs)

            status_code = response.status_code
            logger.info(f"{num} status_code: {status_code}")

            logger.info(f"{num} headers: {response.headers}")

        elif proxy_provider == "chromium":
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
                dt_download_avg = sum(dt_download_list) / len(dt_download_list)

                #logger.debug("headers: " + repr(dict(headers)))
                sleep_each = random.randint(sleep_each_min, sleep_each_max)
                if sleep_each > 0:
                    logger.info(f"{num} 200 dt={dt_download:.3f} dt_avg={dt_download_avg:.3f} -> waiting {sleep_each} seconds")
                else:
                    logger.info(f"{num} 200 dt={dt_download:.3f} dt_avg={dt_download_avg:.3f}")
                time.sleep(sleep_each)
                continue
            else:
                print(f"error: found multiple downloaded files for num={num}:", downloaded_files)
                raise NotImplementedError

        elif proxy_provider == "pyppeteer":
            await pyppeteer_page.goto(url)
            raise NotImplementedError

        else:
            # no proxy
            response = requests.get(url, **requests_get_kwargs)
            status_code = response.status_code

        response_content = response_content or response.content
        response_headers = response_headers or response.headers

        # https://scrapingant.com/free-proxies/
        #proxy = "socks5://54.254.52.187:8118"

        if proxy_provider == "scrapingant.com":
            try:
                status_code = int(response_headers["Ant-Page-Status-Code"])
            except KeyError as err:
                print(f"{num} status_code={status_code} KeyError: no Ant-Page-Status-Code. headers: {response_headers}. content: {response_content[0:100]}...")

        #print(f"{num} status_code={status_code} headers:", response_headers)

        if status_code == 404:
            open(filename_notfound, 'a').close() # create empty file
            t2_download = time.time()
            dt_download = t2_download - t1_download
            dt_download_list.append(dt_download)
            dt_download_avg = sum(dt_download_list) / len(dt_download_list)
            logger.info(f"{num} {status_code} dt={dt_download:.3f} dt_avg={dt_download_avg:.3f}")
            num += 1
            continue

        if status_code == 429:
            # rate limiting
            # this happens after 30 sequential requests
            # only successful requests are counted (http 404 is not counted)
            # blocking is done by cloudflare?
            #logger.info(f"{num} {status_code} Too Many Requests -> waiting {sleep_blocked} seconds")
            #time.sleep(sleep_blocked)
            print(f"{num} response_headers", response_headers)
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
            requests_session = new_session()
            time.sleep(sleep_change_ipaddr)
            continue

        if status_code == 500:
            logger.info(f"{num} {status_code} Internal Server Error -> retrying in 10 seconds")
            time.sleep(10)
            num_stack.append(num) # retry num. inverse of: num = num_stack.pop()
            continue

        assert status_code == 200, f"{num} unexpected status_code {status_code}. headers: {response_headers}. content: {response_content[0:100]}..."

        content_type = content_type or response_headers.get("Content-Type")

        if content_type != "application/zip":
            print(f"{num} status_code={status_code} content_type={content_type}. headers: {response_headers}. content: {response_content[0:100]}...")
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
                filename=f"{new_subs_dir}/{num}.html"
            else:
                filename=f"{new_subs_dir}/{num}.unknown"
                print(f"{num} saving response_content to file: {filename}")
                with open(filename, "wb") as dst:
                    dst.write(response_content)
                #print(f"{num} status_code={status_code} content_type={content_type}. headers: {response_headers}. content: {response_content[0:100]}...")
                raise NotImplementedError(f"{num}: unknown Content-Type: {content_type}")

        #print(f"{num} response", dir(response))
        #print(f"{num} response_headers", response_headers)
        # 'Zr-Content-Disposition': 'attachment; filename="nana.s01.e14.family.restaurant.of.shambles.(2006).ita.1cd.(9181475).zip"'
        content_disposition = content_disposition or response_headers.get("Content-Disposition")

        if content_disposition:
            # use filename from response_headers
            content_filename = content_disposition[22:-1]
            filename = f"{new_subs_dir}/{num}.{content_filename}"
        else:
            # file basename is f"{num}.zip"
            #print(f"{num} FIXME missing filename? response_headers", response_headers)
            pass

        # atomic write
        filename_tmp = filename + ".tmp"
        file_open_mode = "wb"
        if type(response_content) == str:
            file_open_mode = "w"
        with open(filename_tmp, file_open_mode) as f:
            f.write(response_content)
        os.rename(filename_tmp, filename)

        # check file
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
        dt_download_avg = sum(dt_download_list) / len(dt_download_list)

        #logger.debug("headers: " + repr(dict(headers)))
        sleep_each = random.randint(sleep_each_min, sleep_each_max)
        if sleep_each > 0:
            logger.info(f"{num} 200 dt={dt_download:.3f} dt_avg={dt_download_avg:.3f} -> waiting {sleep_each} seconds")
        else:
            logger.info(f"{num} 200 dt={dt_download:.3f} dt_avg={dt_download_avg:.3f}")
        time.sleep(sleep_each)
        #break
        #num += 1

asyncio.get_event_loop().run_until_complete(main())