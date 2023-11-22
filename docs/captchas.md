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
