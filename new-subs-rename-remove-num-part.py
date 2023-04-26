#! /usr/bin/env python3

# ./new-subs-rename-remove-num-part.py >>./new-subs-rename-remove-num-part.py.log

# a: 1.alien.3.(1992).eng.2cd.(1).zip
# b: 1.alien.3.(1992).eng.2cd.zip

import os
import re
import shlex

zipfiles_dir = "new-subs"

os.chdir(zipfiles_dir)

def get_zipfile_new(zipfile):
    if not zipfile.endswith(".zip"):
        return
    num = zipfile.split(".", 1)[0]
    suffix = f".({num}).zip"
    if not zipfile.endswith(suffix):
        return
    zipfile_new = zipfile[0:(-1 * len(suffix))] + ".zip"
    return zipfile_new

# test
assert get_zipfile_new("1.alien.3.(1992).eng.2cd.(1).zip") == "1.alien.3.(1992).eng.2cd.zip"
assert get_zipfile_new("1.alien.3.(1992).eng.2cd.zip") == None

for zipfile in os.listdir("."):
    zipfile_new = get_zipfile_new(zipfile)
    if not zipfile_new:
        continue
    print(f"mv \\\n  {shlex.quote(zipfile)} \\\n  {shlex.quote(zipfile_new)}")
    os.rename(zipfile, zipfile_new)
    #break # debug
