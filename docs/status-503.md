# status 503

## backups and upgrades

```
$ curl -s http://dl.opensubtitles.org/en/download/sub/12345
<pre>Site will be online soon. We are doing some necessary backups and upgrades. Thanks for understanding.

$ curl -s http://dl.opensubtitles.org/en/download/sub/12345 | wc -c
106

$ curl -s http://dl.opensubtitles.org/en/download/sub/12345 | sha1sum -
705b6748ed371d5d161d3461f18f208cb4536848  -

$ curl -I http://dl.opensubtitles.org/en/download/sub/12345
HTTP/1.1 503 Service Unavailable
Content-Type: text/html; charset=UTF-8
Retry-After: 300
```

same result with other urls

- https://www.opensubtitles.org/en/search/subs
- https://www.opensubtitles.org/

response can be empty

```
$ curl -s https://www.opensubtitles.org/ | wc -c
0

$ curl -s https://www.opensubtitles.org/ | sha1sum -
da39a3ee5e6b4b0d3255bfef95601890afd80709  -
```

problem: chromium does not write content to HAR file if status is 503

chromium writes status 500 (not 503) to the HAR file

https://github.com/sitespeedio/chrome-har/issues/8

Network.getResponseBody(requestId) -> { body, base64Encoded }

https://chromedevtools.github.io/devtools-protocol/

The Chrome DevTools Protocol allows for tools to instrument, inspect, debug and profile Chromium

start chromium with --remote-debugging-port=9222

and in a separate chrome instance, open http://localhost:9222
this will open devtools of the first chrome instance

You can also issue your own commands using Protocol Monitor

Click the gear icon in the top-right of the DevTools to open the Settings panel. Select Experiments on the left of settings. Turn on "Protocol Monitor", then close and reopen DevTools. Now click the ⋮ menu icon, choose More Tools and then select Protocol monitor.

{"command":"Page.captureScreenshot","parameters":{"format": "jpeg"}}
{"command":"Network.getResponseBody","parameters":{"requestId": "0EE67697AFCD9CAF85E063B7C61AFABD"}}

Network.getResponseBody("0EE67697AFCD9CAF85E063B7C61AFABD")

https://github.com/fake-name/ChromeController
Comprehensive wrapper and execution manager for the Chrome browser using the Chrome Debugging Protocol.

https://github.com/chazkii/chromewhip
Scriptable Google Chrome as a HTTP service + asyncio driver

https://github.com/hyperiongray/python-chrome-devtools-protocol
Python type wrappers for Chrome DevTools Protocol (CDP)

https://github.com/scivisum/browser-debugger-tools
A python client for the devtools protocol
