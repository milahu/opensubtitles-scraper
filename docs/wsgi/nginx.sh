#!/bin/sh

set -x

exec nginx -c "$PWD"/docs/wsgi/nginx.conf -e "$PWD"/docs/wsgi/nginx.error.log -g "daemon off;"
