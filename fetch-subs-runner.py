#! /usr/bin/env python3

# workaround for: asyncio hangs

# python -u fetch-subs-runner.py 2>&1 | tee -a fetch-subs-runner.py.log

# t_sleep = random.randrange(20, 60)
dt_max = 60 + 10

import sys
import subprocess
import time
import contextlib
import signal

# https://stackoverflow.com/questions/15018519/python-timeout-context-manager-with-threads
class TimeoutException(Exception):
    pass
def timeout_handler(signum, frame):
    raise TimeoutException()
@contextlib.contextmanager
def timeout(seconds):
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)

while True:
    args = [
        sys.executable, # python exe
        "fetch-subs.py",
    ]
    proc = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        encoding="utf8",
    )

    # https://stackoverflow.com/questions/18421757/live-output-from-subprocess-command
    # replace "" with b"" for Python 3
    lines = iter(proc.stdout.readline, "")
    while True:
        try:
            with timeout(dt_max):
                line = next(lines)
        except TimeoutException:
            print("fetch-subs-runner.py: TimeoutException -> restarting fetch-subs.py")
            break
        except StopIteration:
            print("fetch-subs-runner.py: StopIteration -> restarting fetch-subs.py in 30 seconds")
            time.sleep(30)
            break
        sys.stdout.write(line)
