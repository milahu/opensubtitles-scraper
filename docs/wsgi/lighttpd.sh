#!/bin/sh

set -x

exec lighttpd -f docs/wsgi/lighttpd.conf -D
