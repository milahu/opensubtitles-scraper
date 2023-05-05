#!/usr/bin/env python3

import sys
import os
import re
import subprocess
import shlex


new_subs_dir = "new-subs"
remote_url = os.environ.get("NEW_SUBS_REPO_URL")

if not os.path.exists(f"{new_subs_dir}/.git"):
    os.makedirs(new_subs_dir, exist_ok=True)
    args = [
        "git",
        "-C", new_subs_dir,
        "init",
    ]
    print(shlex.join(args))
    proc = subprocess.run(
        args,
        check=True,
        timeout=10,
    )

# TODO check if remote exists
if True:
    print("git remote add")
    args = [
        "git",
        "-C", new_subs_dir,
        "remote",
        "add",
        "origin",
        remote_url,
    ]
    proc = subprocess.run(
        args,
        check=True,
        timeout=10,
    )

print("git pull")
args = [
    "git",
    "-C", new_subs_dir,
    "pull",
    "origin",
    "main",
    "--depth=1",
]
proc = subprocess.run(
    args,
    check=True,
    timeout=10,
)
