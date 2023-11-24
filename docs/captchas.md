# captchas

now its getting interesting...

after about 20 requests from my IP address
opensubtitles.org starts to block my requests with captchas

there are multiple entries in har.log.entries

responses idx 0 1 2 are redirects to

- `https://www.opensubtitles.org/en/captcha2/`
- `https://www.opensubtitles.org/en/captcha2/`
- `/en/captcha/`

response idx 3 has status 429 (Too Many Requests) and has the "CAPTCHA robot test" page

```
$ har=/run/user/1000/fetch-subs-20231122T172649.037627Z/response-20231122T172849.797045Z-7184542c.har

$ jq -r '.log.entries | keys[]' "$har" | while read entry_idx; do jq -r ".log.entries[$entry_idx] | \"$entry_idx. \(.startedDateTime) \(.response.status) \(.response.statusText)\n  \(.request.url)\n  \(.response.redirectURL)\"" "$har"; done 
0. 2023-11-22T17:28:33.731Z 301 Moved Permanently
  https://dl.opensubtitles.org/en/download/sub/12345
  https://www.opensubtitles.org/en/captcha2/redirect-%7Cen%7Cdownload%7Csub%7C12345
1. 2023-11-22T17:28:33.837Z 301 Moved Permanently
  https://www.opensubtitles.org/en/captcha2/redirect-%7Cen%7Cdownload%7Csub%7C12345
  https://www.opensubtitles.org/en/captcha2/redirect-%7Cen%7Cdownload%7Csub%7C12345
2. 2023-11-22T17:28:34.230Z 302 Found
  https://www.opensubtitles.org/en/captcha2/redirect-%7Cen%7Cdownload%7Csub%7C12345
  /en/captcha/redirect-%7Cen%7Cdownload%7Csub%7C12345
3. 2023-11-22T17:28:34.360Z 429 Too Many Requests
  https://www.opensubtitles.org/en/captcha/redirect-%7Cen%7Cdownload%7Csub%7C12345
```

in total, there are about 20 requests
fetching static assets from

- `https://static.opensubtitles.org/`
- `https://www.recaptcha.net/recaptcha/api/`
- `https://www.gstatic.com/recaptcha/releases/`
- `https://fonts.googleapis.com/css`
- `https://fonts.gstatic.com/s/roboto/`

## captcha solving service

this works by adding a browser extension

### browser extensions

work with multiple services

- https://github.com/dessant/buster - Captcha solver extension for humans, available for Chrome, Edge and Firefox
  - https://www.crx4chrome.com/extensions/mpbjkejclgfgadiemmefgebjfooflfhl/

### services

- https://bestcaptchasolver.com/
- https://anti-captcha.com/
- https://2captcha.com/ or https://rucaptcha.com/
  - https://github.com/2captcha/2captcha-solver
  - https://www.crx4chrome.com/extensions/ifibfemgeogfhoebkmokieepdoobkbpo/ Captcha Solver
- https://nopecha.com/
  - https://www.crx4chrome.com/extensions/dknlfmjaanfblgfdfebhijalfmhmjjjo/
- https://captchas.io/
  - https://www.crx4chrome.com/extensions/lcohighjpfjacnlekljbbdclgapjadao/

### DeathByCaptcha

https://deathbycaptcha.com/browser-extension

> These plugins allow you to automatically solve CAPTCHAs found on any website!
>
> No user interaction required: With our captcha browser plugin, you`ll have a hassle-free experience - CAPTCHAs are recognized automatically, in the background.

https://chrome.google.com/webstore/detail/dbc-solver-auto-recogniti/ejagiilfhmflpcohicichiokfoofeljp

https://addons.mozilla.org/en-US/firefox/addon/dbc-solver/

### ReCaptcha Solver

https://www.crx4chrome.com/extensions/hapgiopokcmcnjmakciaeaocceodcjdn/

## todo

```
FIXME looks like solving captchas does not help
once i hit the rate-limit, i cant unblock it
also, the scripted chromium browser is blocked faster
than my normal desktop chromium browser
maybe because the scripted browser has no state
no tracking cookies, etc
or because the scripted browser loops directly over "download sub" urls
while the desktop browser interacts with the website
for example via the "new subs" page
https://www.opensubtitles.org/en/search/sublanguageid-all

FIXME the captcha solving is not automatic
i still have to click "solve this captcha with buster"
but okay, this can be scripted

FIXME the desktop browser throws ERR_TOO_MANY_REDIRECTS instead of "too many requests"

This page isn't working
www.opensubtitles.org redirected you too many times.
Try clearing your cookies.
ERR_TOO_MANY_REDIRECTS

but there is no cyclic redirect

$ curl -I https://www.opensubtitles.org/en/subtitleserve/sub/9797679
HTTP/2 301
content-type: text/html; charset=UTF-8
location: http://www.opensubtitles.org/en/captcha2/redirect-%7Cen%7Csubtitleserve%7Csub%7C9797679

$ curl -I http://www.opensubtitles.org/en/captcha2/redirect-%7Cen%7Csubtitleserve%7Csub%7C9797679
HTTP/1.1 301 Moved Permanently
Content-Type: text/html; charset=UTF-8
Location: https://www.opensubtitles.org/en/captcha2/redirect-%7Cen%7Csubtitleserve%7Csub%7C9797679

$ curl -I https://www.opensubtitles.org/en/captcha2/redirect-%7Cen%7Csubtitleserve%7Csub%7C9797679
HTTP/2 302
content-type: text/html; charset=UTF-8
location: /en/captcha/redirect-%7Cen%7Csubtitleserve%7Csub%7C9797679

$ curl -I https://www.opensubtitles.org/en/captcha/redirect-%7Cen%7Csubtitleserve%7Csub%7C9797679
HTTP/2 429 
content-type: text/html; charset=UTF-8

note the first redirect from https to http protocol
when i replace http with https
then i need 1 request less to get to "http 429"

$ curl -I https://www.opensubtitles.org/en/subtitleserve/sub/9797679
HTTP/2 301 
content-type: text/html; charset=UTF-8
location: http://www.opensubtitles.org/en/captcha2/redirect-%7Cen%7Csubtitleserve%7Csub%7C9797679

$ curl -I https://www.opensubtitles.org/en/captcha2/redirect-%7Cen%7Csubtitleserve%7Csub%7C9797679 
HTTP/2 302 
content-type: text/html; charset=UTF-8
location: /en/captcha/redirect-%7Cen%7Csubtitleserve%7Csub%7C9797679

$ curl -I https://www.opensubtitles.org/en/captcha/redirect-%7Cen%7Csubtitleserve%7Csub%7C9797679
HTTP/2 429 
content-type: text/html; charset=UTF-8

the desktop browser seems to work better in "incognito mode"
so its a problem with some extension
after solving the captcha, i am redirected to
https://www.opensubtitles.org/en/subtitles/9797679/fighting-spirit-new-challenger-en
where i must click "Download"
with the url https://www.opensubtitles.org/en/subtitleserve/sub/9797679
after solving the captcha, i can continue downloading about 30 subs :)
```
