#!/usr/bin/env -S python3 -u

# TODO alternative?
# https://docs.github.com/en/actions/using-workflows/storing-workflow-data-as-artifacts

import sys
import os
import re
import subprocess
import shlex
import shutil
import time


new_subs_dir = "new-subs"
remote_url = os.environ.get("NEW_SUBS_REPO_URL")

# verbose
debug_print = print
# quiet
debug_print = lambda _: None

if not os.path.exists(f"{new_subs_dir}/.git"):
    os.makedirs(new_subs_dir, exist_ok=True)
    print("git init")
    args = [
        "git",
        "-c", "init.defaultBranch=main",
        "-C", new_subs_dir,
        "init",
    ]
    debug_print(shlex.join(args))
    proc = subprocess.run(
        args,
        check=True,
        timeout=10,
    )

    # debug: git branch
    args = [
        "git",
        "-C", new_subs_dir,
        "branch",
    ]
    debug_print(shlex.join(args))
    proc = subprocess.run(
        args,
        check=True,
        timeout=10,
    )

    print("git remote add")
    args = [
        "git",
        "-C", new_subs_dir,
        "remote",
        "add",
        "origin",
        remote_url,
    ]
    debug_print(shlex.join(args))
    proc = subprocess.run(
        args,
        check=True,
        timeout=10,
    )

    # debug: git branch
    args = [
        "git",
        "-C", new_subs_dir,
        "branch",
    ]
    debug_print(shlex.join(args))
    proc = subprocess.run(
        args,
        check=True,
        timeout=10,
    )



print("getting list of existing files")

print("git pull origin main")
args = [
    "git",
    "-C", new_subs_dir,
    "pull",
    #"--force", # untracked working tree files will be overwritten by checkout
    "--depth=1",
    "origin",
    "main",
]
debug_print(shlex.join(args))
proc = subprocess.run(
    args,
    check=True,
    timeout=10,
)

# debug: git branch
args = [
    "git",
    "-C", new_subs_dir,
    "branch",
]
debug_print(shlex.join(args))
proc = subprocess.run(
    args,
    check=True,
    timeout=10,
)

print("git checkout main")
args = [
    "git",
    "-C", new_subs_dir,
    "checkout",
    "--quiet",
    #"--force", # untracked working tree files will be overwritten by checkout
    "main",
]
debug_print(shlex.join(args))
proc = subprocess.run(
    args,
    check=True,
    timeout=10,
)

done_nums = []
files_txt_path = f"{new_subs_dir}/files.txt"
if os.path.exists(files_txt_path):
    with open(files_txt_path) as f:
        for line in f:
            filename = line.strip()
            if filename.startswith(".git"):
                continue
            if filename in {"files.txt", "nums"}:
                continue
            try:
                num = int(filename.split(".", 1)[0])
            except ValueError:
                print("skipping file", filename)
                continue
            done_nums.append(num)
print(f"found {len(done_nums)} done nums")
done_nums_set = set(done_nums)



# debug: git log
args = [
    "git",
    "-C", new_subs_dir,
    "log",
    "--oneline",
]
debug_print(shlex.join(args))
proc = subprocess.run(
    args,
    check=True,
    timeout=10,
)

# debug: git branch
args = [
    "git",
    "-C", new_subs_dir,
    "branch",
]
debug_print(shlex.join(args))
proc = subprocess.run(
    args,
    check=True,
    timeout=10,
)



print(f"processing files in {new_subs_dir} ...")

for filename in os.listdir(new_subs_dir):
    if filename.startswith(".git"):
        continue
    if filename in {"files.txt", "nums"}:
        continue
    try:
        num = int(filename.split(".", 1)[0])
    except ValueError:
        print("skipping file", filename)
        continue
    if num in done_nums_set:
        continue

    # add file to f"nums/{num}" branch
    # "-C", worktree_path,
    print("adding file", filename)

    # https://stackoverflow.com/questions/53005845/checking-out-orphan-branch-in-new-work-tree
    # d=subdir; n=some-branch; git worktree add --detach --no-checkout $d; git -C $d checkout --orphan $n; git reset; git clean -fdq; echo hello >$d/test.txt; git -C $d add test.txt; git -C $d commit -m init

    worktree_path = f"{new_subs_dir}/nums/{num}"

    if os.path.exists(worktree_path):
        # remove old worktree
        args = [
            "git",
            "-C", new_subs_dir,
            "worktree",
            "remove",
            #"--force",
            f"nums/{num}", # worktree path
        ]
        debug_print(shlex.join(args))
        proc = subprocess.run(
            args,
            check=True,
            timeout=10,
        )

    args = [
        "git",
        "-C", new_subs_dir,
        "worktree",
        "add",
        "--quiet",
        "--detach",
        "--no-checkout",
        f"nums/{num}", # worktree path
    ]
    debug_print(shlex.join(args))
    proc = subprocess.run(
        args,
        check=True,
        timeout=10,
    )

    # FIXME fatal: a branch named 'nums/9539188' already exists
    args = [
        "git",
        "-C", worktree_path,
        "checkout",
        "--quiet",
        "--orphan",
        f"nums/{num}", # branch name
    ]
    debug_print(shlex.join(args))
    proc = subprocess.run(
        args,
        check=True,
        timeout=10,
    )

    args = [
        "git",
        "-C", worktree_path,
        "reset",
    ]
    debug_print(shlex.join(args))
    proc = subprocess.run(
        args,
        check=True,
        timeout=10,
    )

    args = [
        "git",
        "-C", worktree_path,
        "clean",
        "-fdq",
    ]
    debug_print(shlex.join(args))
    proc = subprocess.run(
        args,
        check=True,
        timeout=10,
    )

    # copy file to worktree
    shutil.copyfile(
        f"{new_subs_dir}/{filename}",
        f"{new_subs_dir}/nums/{num}/{filename}",
    )

    args = [
        "git",
        "-C", worktree_path,
        "add",
        filename
    ]
    debug_print(shlex.join(args))
    proc = subprocess.run(
        args,
        check=True,
        timeout=10,
    )

    # disable compression for zip files
    gitattributes_path = f"{new_subs_dir}/nums/{num}/.gitattributes"
    # https://stackoverflow.com/questions/7102053/git-pull-without-remotely-compressing-objects
    with open(gitattributes_path, "w") as f:
        f.write("*.zip -delta\n")
    args = [
        "git",
        "-C", worktree_path,
        "add",
        os.path.basename(gitattributes_path),
    ]
    debug_print(shlex.join(args))
    proc = subprocess.run(
        args,
        check=True,
        timeout=10,
    )

    args = [
        "git",
        "-C", worktree_path,
        "commit",
        "--quiet",
        "-m", f"add {num}",
    ]
    debug_print(shlex.join(args))
    proc = subprocess.run(
        args,
        check=True,
        timeout=10,
    )

    args = [
        "git",
        "-C", new_subs_dir,
        "worktree",
        "remove",
        f"nums/{num}", # worktree path
    ]
    debug_print(shlex.join(args))
    proc = subprocess.run(
        args,
        check=True,
        timeout=10,
    )

    # add file to files.txt in main branch
    # "-C", new_subs_dir,

    with open(files_txt_path, "a") as f:
        f.write(f"{filename}\n")

    args = [
        "git",
        "-C", new_subs_dir,
        "add",
        # note: actually: relative path to new_subs_dir
        os.path.basename(files_txt_path),
    ]
    debug_print(shlex.join(args))
    proc = subprocess.run(
        args,
        check=True,
        timeout=10,
    )

    args = [
        "git",
        "-C", new_subs_dir,
        "commit",
        "--quiet",
        "-m", f"files.txt: add {num}",
    ]
    debug_print(shlex.join(args))
    proc = subprocess.run(
        args,
        check=True,
        timeout=10,
    )



# debug: git log
args = [
    "git",
    "-C", new_subs_dir,
    "log",
    "--oneline",
]
debug_print(shlex.join(args))
proc = subprocess.run(
    args,
    check=True,
    timeout=10,
)



print("git push")
args = [
    "git",
    "-C", new_subs_dir,
    "push",
    "--all", # push all branches
    "--force", # overwrite existing remote branches
    remote_url,
]
debug_print(shlex.join(args))
try:
    proc = subprocess.run(
        args,
        check=True,
        timeout=10,
        #capture_output=True,
        #encoding="utf8",
    )
# TODO more specific
# subprocess.XXXError
except Exception as error:
    print(error)
    print("failed to git-push. maybe another git-push was faster. retry in next run")
    # wait for output of git
    # TODO better
    time.sleep(5)
    sys.exit(1)
