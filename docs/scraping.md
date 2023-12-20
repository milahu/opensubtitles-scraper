# scraping


# https://forum.opensubtitles.org/viewtopic.php?f=1&t=14559
#
# Q: I want download bulk subtitles from your site, what I should do?
# A: Don't be shy and contact us!
#
# email:
# so ...
# how many dollars do you want for 1 million subs?
# milahu@gmail.com

# https://www.opensubtitles.org/en/support#vip
# VIP member costs only 10 EUR for 1 YEAR.
# Higher download limits - 1000 subtitles/24 hours -
# useful when using programs such as media centers (but no abusing!)
# 1000 subs/day = 1000 days / 1M subs




# https://www.opensubtitles.org/en/statistics#uploaded_subtitles
# stats: upload: 1200 subs per day
# -> this is impossible to scrape with free accounts
# opensubtitles.org.Actually.Open.Edition.2022.07.25
# 2022-07-25: 5719123
# 2023-04-18: opensubtitles.org: 6633435 subtitles
# missing count: 6633435 - 5719123 = 914312
# missing size: 914312 * 130GB / 5719123 = 21GB
# 2022-07-25 to 2023-04-18 = 267 days
# 914312 subs / 267 days = 3424 subs/day
# 1M subs = 23GB



https://github.com/venomous/cloudscraper
A Python module to bypass Cloudflare's anti-bot page.
using paid captcha solver services



https://github.com/tholian-network/stealth
Secure, Peer-to-Peer, Private and Automateable Web Browser/Scraper/Proxy



https://www.reddit.com/r/dataengineering/comments/pjc2ka/comment/hct9lxt/?utm_source=reddit&utm_medium=web2x&context=3

There are 3 layers to the Cloudflare check.

1. IP check for rate limits and known bot ranges

2. Browser check on entry to page to see if you're a real user, often accompanied by captcha.

3. Repeat checks of 2 while scraping the page.

1. To avoid the IP check, you can use your home IP address, but at some point you will run into rate limits. Getting a proxy is your best bet. Some websites will allow access from datacenter proxies which are cheap. Other sites will require residential proxies, which are much harder to detect. There really is nothing else you can do about this if you need to make more requests than the rate limit is.

2. When you see "Attention Cloudflare" in your HTML title, or a "Please wait checking your browser" screen in your browser, it means Cloudflare wants to check if you're a human. If you're not using a browser, you automatically failed and you'll most likely get a Captcha in response. You can convince Cloudflare that you're a human by using Puppeteer or Playwright. Personally, I would use Playwright because it's more powerful than Puppeteer (or Selenium). You can use Playwright in headful mode by setting the headless: false launch option. This often convinces Cloudflare by itself. If it doesn't work, you'll need proper fingerprints, but that's quite a challenging task to pull out. I wrote a tutorial on [How to scrape the web with Playwright](https://blog.apify.com/how-to-scrape-the-web-with-playwright-ece1ced75f73/) so you might wanna check this out.

3. Depending on the website, you'll get the Cloudflare challenges on each request or from time to time. If you get them all the time, you will need to use Playwright for scraping. But if you only get them from time to time, you can use Playwright to get cookies from the website and then use those cookies with your normal requests to bypass Cloudflare. This can save a lot of time and resources.

Convincing Cloudflare that you're a human and not a bot is not easy, but we do that every day at Apify so if you need more help with scraping, you can definitely get in touch with us.

## use case

download one million zip files from f"https://dl.opensubtitles.org/en/download/sub/{num}"

average size is 23KByte

expected traffic is 23GByte

my goal is to continue the archive at
https://www.reddit.com/r/DataHoarder/comments/w7sgcz/5719123_subtitles_from_opensubtitlesorg/
which has 5.72 million subtitles = 130GByte

the opensubtitles.org server is protected by cloudflare

in theory, they have a rate limit of 200 downloads per day
but when i do sequential downloads, i get a captcha after 30 requests



### update 2023-23-20

for my scraper, i parse the last subtitle ID
from the section "New subtitles" at
https://www.opensubtitles.org/en/search/subs
see also options.last_num in fetch-subs.py

currently the last subtitle is
https://www.opensubtitles.org/en/subtitles/9828872/silent-night-nl

so in my unreleased dump
about 9828872 - 9756545 = 72327 subs are missing

> average size is 23KByte

72327 * 23 / 1024 / 1024 = 1.6GByte

note: this does not include the scraped html pages



### expected monthly traffic

subs-added-by-year.txt: 2022|421348

421348 / 12 = 35112 new subs per month

35112 * 23 / 1024 = 789MByte per month

35112 / 30.5 = 1151 new subs per day

scraper is blocked by cloudflare after 20 requests

1151 / 20 = 58 scraping sessions per day

200 requests per ip per day?
so we would need only 6 different ip addresses



## github CI

the cheapest scraping service ...

https://github.com/pricing

> free: 2,000 CI/CD minutes/month
>
> team: 3,000 CI/CD minutes/month, $3.67 per user/month
>
> enterprise: 50,000 CI/CD minutes/month, $19.25 per user/month

2000 minutes/month = 65 minutes/day



## scraping proxies

scrapingdog.com: returns broken zip files, http headers are missing

webscraping.ai: fails to bypass cloudflare

zenrows.com: works, also returns http headers like Content-Disposition, no HTTPS?

scrapingant.com: works, slow with free account

other providers are too expensive, i expect something like 100 USD per 1M requests

## free proxies

"known proxies" are banned by cloudflare

- https://github.com/topics/proxy-scraper
- https://www.proxyrack.com/free-proxy-list/

## Web Scraping Proxies

wanted specs: 23GB traffic in 1M requests

TODO use a "rotating proxy only" service, which is cheaper

sources:

- https://prowebscraper.com/blog/best-web-scraping-services/
- https://rapidapi.com/category/Data
- https://rapidapi.com/blog/top-10-best-web-scraping-apis-alternatives-2021/
- https://www.zenrows.com/blog/web-scraping-proxy # The 10 Best Web Scraping Proxy Services in 2023
- https://www.scrapingdog.com/blog/best-datacenter-proxies/
- https://scrapfly.io/blog/best-proxy-providers-for-web-scraping/
- https://www.geeksforgeeks.org/the-complete-guide-to-proxies-for-web-scraping/
- https://research.aimultiple.com/proxy-scraping/
- https://scrapeops.io/web-scraping-playbook/web-scraping-without-getting-blocked/
- https://scrapeops.io/proxy-providers/comparison/
- https://intoli.com/blog/making-chrome-headless-undetectable/

### scrapfly.io

https://scrapfly.io/
https://scrapfly.io/blog/best-proxy-providers-for-web-scraping/#scrapfly
https://scrapfly.io/blog/scraping-using-browsers/#fingerprints
https://www.reddit.com/r/webscraping/comments/tkueb7/scraping_cloudflare_protected_website/

free: 1K requests
paid: 30USD: 200K requests
paid: 100USD: 1M requests
good success rate (100%?)
response is encoded in json
binary files are encoded in base64
Anti Bot Bypass

### scrapingdog.com

https://www.scrapingdog.com/pricing
free version is not usable: returns broken zip files, see new-subs-broken-scrapingdog/
free: 1K requests
paid: 30USD: 200K requests
paid: 90USD: 1M requests
curl "https://api.scrapingdog.com/scrape?api_key=643f9f3b575aa419c1d7218a&url=https://dl.opensubtitles.org/xxxx&dynamic=false"

### apify.com

https://console.apify.com/billing#/pricing

https://help.apify.com/en/articles/1961361-several-tips-on-how-to-bypass-website-anti-scraping-protections



Blocked headless Chrome with Puppeteer

Puppeteer is essentially a Node.js API to headless Chrome. Although it is a relatively new library, there are already anti-scraping solutions on the market that can detect its usage based on a variable it puts into the browser's window.navigator property.

As a start, we developed a solution that removes the property from the web browser, and thus prevents this kind of anti-scraping protection from figuring out that the browser is automated. This feature later expanded to a stealth module that encompasses many useful tricks to make the browser look more human-like.


Here is an example of how to use it with Puppeteer and headless Chrome:

 

const Apify = require('apify');

Apify.main(async () => {
    const browser = await Apify.launchPuppeteer({ stealth: true });
    const page = await browser.newPage();
    
    await page.goto('https://www.example.com');
    
    // Add rest of your code here...    
    await page.close();
    await browser.close();
});
 

Browser fingerprinting
Another option sometimes used by anti-scraping protection tools is to create a unique fingerprint of the web browser and connect it using a cookie with the browser's IP address. Then if the IP address changes but the cookie with the fingerprint stays the same, the website will block the request. 

 

In this way, sites are also able to track or ban fingerprints that are commonly used by scraping solutions - for example, Chromium with the default window size running in headless mode.

The best way to fight this type of protection is to remove cookies and change the parameters of your browser for each run and switch to a real Chrome browser instead of Chromium. 

Here is an example of how to launch Puppeteer with Chrome instead of Chromium using Apify SDK:

 

const browser = await Apify.launchPuppeteer({
    useChrome: true,
});
const page = await browser.newPage();
This example shows how to remove cookies from the current page object:

 

// Get current cookies from the page for certain URL
const cookies = await page.cookies('https://www.example.com');
// And remove them
await page.deleteCookie(...cookies);
Note that the snippet above needs to be run before you call page.goto() !

And this is how you can randomly change the size of the Puppeteer window using the page.viewport() function:

 

await page.viewport({
    width: 1024 + Math.floor(Math.random() * 100),
    height: 768 + Math.floor(Math.random() * 100),
})
Finally, you can use Apify's base Docker image called Node.JS 8 + Chrome + Xvfb on Debian to make Puppeteer use a normal Chrome in non-headless mode using the X virtual framebuffer (Xvfb).






### webscraping.ai

fails to bypass cloudflare
free: 2K requests per months
paid: 30USD: 250K requests
paid: 100USD: 1M requests
Requests pricing
js=false + proxy=datacenter: 1 call
js=false + proxy=residential: 10 calls
js=true + proxy=datacenter: 5 calls
js=true + proxy=residential: 25 calls
error with webscraping_ai_option_proxy = "datacenter":
2023-04-19 11:26:39,820 INFO 9181481 status_code: 500
2023-04-19 11:26:39,822 INFO 9181481 headers: {'Date': 'Wed, 19 Apr 2023 09:26:39 GMT', 'Content-Type': 'application/json; charset=utf-8', 'Content-Length': '75', 'Connection': 'keep-alive', 'apigw-requestid': 'DnkIVgs-oAMEJyA=', 'x-cache': 'Error from cloudfront', 'via': '1.1 50c53efe331c3da25a4faf191817af8c.cloudfront.net (CloudFront)', 'x-amz-cf-pop': 'FRA56-P2', 'x-amz-cf-id': '9dBQ_mWW61TYiF-ITkBy9sLpFF1uSCVKtESuxyQvGgpEjLL8IBwHQw==', 'vary': 'Origin', 'CF-Cache-Status': 'DYNAMIC', 'Report-To': '{"endpoints":[{"url":"https:\\/\\/a.nel.cloudflare.com\\/report\\/v3?s=NP6Vjz%2ByGtsBHVJLz3OwJGnNmsOBJND%2BfPuOIA0frLW2dg6yFTyxdtpjfKm8vjETNL3wwx%2FukQ%2FQ8RoXPjwbr5Q6BV9SZjpr4x6Kf7961tqgd7nmwuw%2B1l6OARXCX6giZ7728Q%3D%3D"}],"group":"cf-nel","max_age":604800}', 'NEL': '{"success_fraction":0,"report_to":"cf-nel","max_age":604800}', 'Server': 'cloudflare', 'CF-RAY': '7ba41b69ed193673-FRA'}
#webscraping_ai_option_proxy = "datacenter"
webscraping_ai_option_proxy = "residential" # try in case if the target site is not accessible on datacenter proxies
error with webscraping_ai_option_proxy = "residential":
2023-04-19 11:28:25,852 INFO 9181480 status_code: 500
2023-04-19 11:28:25,853 INFO 9181480 headers: {'Date': 'Wed, 19 Apr 2023 09:28:25 GMT', 'Content-Type': 'application/json; charset=utf-8', 'Content-Length': '75', 'Connection': 'keep-alive', 'apigw-requestid': 'DnkY3ixoIAMEVtw=', 'x-cache': 'Error from cloudfront', 'via': '1.1 f4137273db9ae377298b8f8daf5b93f0.cloudfront.net (CloudFront)', 'x-amz-cf-pop': 'FRA56-P2', 'x-amz-cf-id': 'KhfJIg4PFRek_HSInpXhRRpgplPa0QamRYc_jLQeCern7JlvLrkG5A==', 'vary': 'Origin', 'CF-Cache-Status': 'DYNAMIC', 'Report-To': '{"endpoints":[{"url":"https:\\/\\/a.nel.cloudflare.com\\/report\\/v3?s=HBD9idRmi26KbYdAzGa9KG2DeWM9KqtWwPJAJomFgzLobhYFzv%2FVnsQQn7faqeu%2F2wJwMBw9DN8Qirx0c9QGkFdvl04WCxFhkl6aujHt9ltBMwGs33zDd43PME8hJixTdo5g8A%3D%3D"}],"group":"cf-nel","max_age":604800}', 'NEL': '{"success_fraction":0,"report_to":"cf-nel","max_age":604800}', 'Server': 'cloudflare', 'CF-RAY': '7ba41dff58953a4f-FRA'}

### webscrapingapi.com

https://crozdesk.com/software/webscrapingapi
free: 5K requests
paid: 50USD: 100K requests (Data Center Proxies)
paid: 150USD: 1M requests (Data Center Proxies)
Standard Request using Data Center Proxies: 1 API Credit
Standard Request using Residential Proxies: 10 API Credits

### proxyrack.com

https://www.proxyrack.com/pricing/
TODO https://www.proxyrack.com/free-proxy-list/
threads = parallel connections https://help.proxyrack.com/en/articles/5740997-what-is-a-thread-connection
paid: 14USD: trial for 7 days: 250 Global Rotating Datacenter Threads
paid: 50USD: 10GB
paid: 90USD: 20GB
paid: 65USD: Global Rotating Datacenter Proxies, 100 threads
paid: 120USD: Global Rotating Datacenter Proxies, 250 threads

### zenrows.com

https://zenrows.com/
free: 1K requests per month
paid: 50EUR: 250K requests per month
paid: 100EUR: 1M requests per month
no HTTPS?

https://www.zenrows.com/blog/playwright-cloudflare-bypass
https://www.zenrows.com/blog/stealth-web-scraping-in-python-avoid-blocking-like-a-ninja

### scraperbox.com


https://scraperbox.com/pricing
https://rapidapi.com/scraperbox/api/scraper-box
https://status.scraperbox.com/ # offline since 2023-03-27
not working: HTTP 502 Bad Gateway
free: 1K requests per month
paid: 30USD: 125K requests
paid: 90USD: 1M requests

### zyte.com

https://www.zyte.com/
aka Scrapinghub
https://www.zyte.com/pricing/#zyte-api
Return HTML efficiently from any website using a single API.
free: requires "Payment Info"
2USD: 10K requests
120USD: 1M requests
free: scrapy cloud starter, 1 thread, 1 hour per day

## expensive proxy providers

### smartproxy.com

https://smartproxy.com/proxies/datacenter-proxies/pricing
paid: 100USD: 100K requests (Web Scraping API)
paid: 250USD: 275K requests (Web Scraping API)

### scrapingant.com

scrapingant
slow with free account
https://app.scrapingant.com/dashboard
free: 10K requests per months
paid: 150USD: 200K requests
limitation: Content-Disposition header is missing
response_headers {'Ant-Page-Status-Code': '200', 'Content-Encoding': 'gzip', 'Content-Type': 'application/zip', 'Date': 'Mon, 17 Apr 2023 xxxxxxxxxx GMT', 'Server': 'uvicorn', 'Set-Cookie': 'PHPSESSID=2yJZsxxxxxxxxxxxxxxx; Path=/; SameSite=lax, pref_mk=%7B%22xxxxxxxxxxxx; Path=/; SameSite=lax', 'Vary': 'Accept-Encoding', 'Transfer-Encoding': 'chunked'}

### netnut.io

netnut
https://netnut.io/proxy-products/
paid: 300USD: 20GB

### smartproxy.com

https://smartproxy.com/proxies/residential-proxies/pricing
paid: 225USD: 25GB

### oxylabs

https://crozdesk.com/software/oxylabs-web-scraper-api
paid: 400USD: 400K requests

### scrapingbee

https://www.zenrows.com/blog/web-scraping-proxy#scrapingbee
https://rapidapi.com/daolf/api/scrapingbee
free: 100 requests
paid: 150USD: 200K requests
no residential IPs

https://www.scrapingbee.com/blog/web-scraping-without-getting-blocked/

### scrapers proxy

https://rapidapi.com/scapers-proxy-scapers-proxy-default/api/scrapers-proxy2
free: 100 requests
paid: 250USD: 100K requests

### browserless.io

https://www.browserless.io/blog/2020/12/15/stealth-mode/

### proxyscrape.com

https://proxyscrape.com/premium
paid: 24USD: 1000 proxies
paid: 54USD: 2500 proxies
paid: 102USD: 5000 proxies
TODO how many?

### brightdata.com

BrightData
https://brightdata.com/
paid: 500USD

### rayobyte.com

https://rayobyte.com/
7.3GB * 15USD/GB = 109.5USD

### homeip.io

HomeIP
https://homeip.io/
paid: 85USD: 5GB
paid: 200USD: 20GB
