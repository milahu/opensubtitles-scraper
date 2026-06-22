#!/bin/sh

set -x
set -e

stat get-subs.py

exec gunicorn --preload --workers 4 --threads 1 --bind unix:"$PWD"/docs/wsgi/get-subs.sock get-subs:wsgi_request_handler
