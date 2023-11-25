# Chrome DevTools Protocol

https://chromedevtools.github.io/devtools-protocol/

The Chrome DevTools Protocol allows for tools to instrument, inspect, debug and profile Chromium

start chromium with --remote-debugging-port=9222

and in a separate chrome instance, open http://localhost:9222
this will open devtools of the first chrome instance

You can also issue your own commands using Protocol Monitor

Click the gear icon in the top-right of the DevTools to open the Settings panel. Select Experiments on the left of settings. Turn on "Protocol Monitor", th>



https://github.com/fake-name/ChromeController
Comprehensive wrapper and execution manager for the Chrome browser using the Chrome Debugging Protocol.

https://github.com/chazkii/chromewhip
Scriptable Google Chrome as a HTTP service + asyncio driver

https://github.com/hyperiongray/python-chrome-devtools-protocol
Python type wrappers for Chrome DevTools Protocol (CDP)

https://github.com/scivisum/browser-debugger-tools
A python client for the devtools protocol



problem: chromium does not write content to HAR file if status is 503

chromium writes status 500 (not 503) to the HAR file

https://github.com/sitespeedio/chrome-har/issues/8

{"command":"Network.getResponseBody","parameters":{"requestId": "0EE67697AFCD9CAF85E063B7C61AFABD"}}
