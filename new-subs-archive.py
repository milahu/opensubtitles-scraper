#! /usr/bin/env python3


# folders with zip files
input_dir_short_filenames = "new-subs-num"
input_dir_long_filenames = "new-subs"

# use short filenames in archive
# short: 1.zip
# long : 1.alien.3.(1992).eng.2cd.zip
# short filenames are better for lookup by sub_number
# about 10x faster than glob (readdir + regex)
use_short_filenames = True

# create filenames.txt with the full filenames
store_filenames = use_short_filenames

repeat_count = 2


# not mountable, slow random access
#output_format = "tar"

# harder to use than sqlite?
output_format = "iso"

# requires mount to write files? not reproducible: cannot set file times to zero
#output_format = "udf"

# only UDF version 2.60
#output_format = "udf-pycdlib"

# sqlite is reproducible by default. nice!
#output_format = "sqlite"


if output_format == "sqlite":
    use_short_filenames = False
    store_filenames = False # dont create filenames.txt
    repeat_count = 1 # we already know its reproducible

# average file size is 20KB
# TODO benchmark
"""
sqlite_page_size = 2**9 # 512B = min
sqlite_page_size = 2**10 # 1KiB
sqlite_page_size = 2**11 # 2KiB
sqlite_page_size = 2**12 # 4KiB = default
sqlite_page_size = 2**13 # 8KiB
sqlite_page_size = 2**14 # 16KiB
sqlite_page_size = 2**15 # 32KiB
sqlite_page_size = 2**16 # 64KiB = max
"""
sqlite_page_size = 2**12 # 4KiB = default

# benchmark
sqlite_compare_page_sizes = True
sqlite_page_sizes = [
    2**9, # 512B = min
    #2**10, # 1KiB
    #2**11, # 2KiB
    2**12, # 4KiB = default
    #2**13, # 8KiB
    2**14, # 16KiB
    #2**15, # 32KiB
    2**16, # 64KiB = max
]


# creation time is not relevant
# users want fast random read access
# iso: 600sec for 930MB
# sqlite: 150sec for 930MB


# opensubs.db: 1 - 9180517
# 9180518: not found
continue_from = 9180519
# opensubtitles-9180519-9225080.tar # tar, long names
# opensubtitles-9225081-9271106.tar # tar, long names
# opensubtitles-9271107-9331439.tar # tar, long names
#continue_from = 9331439 + 1
# opensubtitles-9331440-9379715.iso # iso, short names + filenames.txt
#continue_from = 9379715 + 1


# reproducible filesystem images
# https://reproducible-builds.org/docs/system-images/
# https://unix.stackexchange.com/questions/572751/how-to-make-a-reproducible-iso-file-with-mkisofs-genisoimage


# validate config

if use_short_filenames == False:
    assert store_filenames == False, "storing the long filenames only makes sense with use_short_filenames = True"



"""
mount image:

mkdir mnt
sudo mount -o loop,ro test.iso mnt
# ls -U: dont sort. files are already sorted in the filesystem
ls -U mnt | head
sudo umount mnt
"""

import subprocess
import sys
import os
import glob
import io
import math
import re
import shutil
import time
import hashlib
import sqlite3

import natsort

"""
# wontfix: pycdlib can create only UDF version 2.60
# but we want 2.01 or 1.50 for compatibility
# https://github.com/clalancette/pycdlib/issues/113
# create reproducible UDF image
# set all times to zero
import time
def zero_time():
    return 0.0
time.time = zero_time
# set all uuid's to zero
import uuid
real_uuid = uuid.UUID
def zero_uuid():
    return real_uuid(hex="00000000000000000000000000000000")
uuid.UUID = zero_uuid
real_uuid4 = uuid.uuid4
def zero_uuid4():
    return real_uuid4(hex="00000000000000000000000000000000")
uuid.uuid4 = zero_uuid4
# set random bits to zero
import random
def zero_getrandbits(k):
    return 0
random.getrandbits = zero_getrandbits
import pycdlib
"""


# https://en.wikipedia.org/wiki/DVD
# Capacity: 4.7 GB (single-sided, single-layer – common)
# DVD-5: 4.70GB
# All units are expressed with SI/IEC prefixes (i.e., 1 Gigabyte = 1,000,000,000 bytes).
dvd_size = int(4.7 * 1000 * 1000 * 1000)


#max_size = 1000 * 1000 * 1000 # 1 GB
# max_size criteria:
# - smaller than 1GB
# - align to size of DVD
max_size = (dvd_size // 5) - 5 # 935 MB
# remaining space on DVD: 5 * 5MB = 25MB = 0.53%

size_tolerance = 0.02 # reserve 2% for filesystem headers

size_tolerance_udf = 0.02 # reserve 2% in UDF filesystem

#udf_media_type = "hd" # OSError: [Errno 28] No space left on device
udf_media_type = "dvdrw"

udf_enable_vat = True
udf_enable_vat = False

# setting blocksize causes weird errors
#udf_block_size = 512
udf_block_size = None

# For normal data, UDF 1.50 is OK.
# UDF 2.00 and 2.01 introduce additional functionality for streaming audio/video.
# https://github.com/pali/udftools/blob/master/doc/HOWTO.udf
#udf_version = "2.01"
udf_version = "1.50"

# minimum blocks_count depends on format
# mkudffs: Error: Not enough blocks on device
udf_min_blocks_count = 260 # --media-type=dvdrw --vat
if udf_media_type == "hd":
    if udf_enable_vat:
        udf_min_blocks_count = 260
    else:
        udf_min_blocks_count = 131
elif udf_media_type == "dvdrw":
    if udf_enable_vat:
        udf_min_blocks_count = 300
    else:
        udf_min_blocks_count = 2000


if False:
#if True:
    # debug
    input_dir_short_filenames = "new-subs-sample"
    max_size = 10 * 1000 * 1000 # 10 MB # debug


def create_empty_udf_image(udf_image_path, blocks_count, label):
    print(f"creating test UDF image: {udf_image_path}")
    group_label = label
    args = [
        "mkudffs",
        "--utf8", # Treat identifier string options as strings encoded in UTF-8.
        "--label=" + label,
        "--vid=" + label, # Volume Identifier. default is "LinuxUDF"
        "--vsid=" + group_label, # Volume Set Identifier. default is "LinuxUDF"
        "--fsid=" + group_label, # File Set Identifier. default is "LinuxUDF"
        "--uuid=" + (16 * "0"), # 16 hexadecimal lowercase digits. default is random
        # In most cases operating systems are unable to mount UDF filesystem if UDF block size differs from logical sector size of device.  Typically  hard
        # disks have sector size 512 bytes and optical media 2048 bytes. Therefore UDF block size must match logical sector size of device.
        f"--media-type={udf_media_type}",
        f"--udfrev={udf_version}",
        "--new-file", # Create a new image file, fail if file already exists
        "--uid=0",
        "--gid=0",
        "--mode=0755", # mode of the root (/) directory. default is "0755"
        #"-path-list", sum_files_file,
        # Virtual Allocation Table a.k.a. VAT (Incremental Writing).
        # Used specifically for writing to write-once media
    ]
    if udf_block_size:
        args += [f"--blocksize={udf_block_size}"]
    if udf_enable_vat:
        args += ["--vat"]
    args += [
        udf_image_path, # device
        str(blocks_count),
    ]
    proc = subprocess.run(
        args,
        check=True,
    )
    assert os.path.exists(udf_image_path), f"mkudffs failed to create UDF image: {udf_image_path}"
    #os.chmod(udf_image_path, 0o644)


def create_empty_iso_image(iso_image_path, volid):
    print(f"creating test ISO image: {iso_image_path}")
    args = [
        "xorrisofs", # mkisofs compatibility mode of xorriso
        "-volid", volid,
        "-output", iso_image_path, # If not specified, stdout is used.
        #"-path-list", sum_files_file,
    ]
    proc = subprocess.run(
        args,
        check=True,
    )
    assert os.path.exists(iso_image_path), f"xorrisofs failed to create ISO image: {iso_image_path}"
    #os.chmod(iso_image_path, 0o644)


def mount_udf_image(udf_image_path, mount_dir):
    print(f"mounting UDF image: {udf_image_path}")

    # TODO set file times to zero (ctime, mtime, atime)
    # https://github.com/wolfcw/libfaketime
    # TZ=UTC faketime "1970-01-01 00:00:00" date +%s --utc
    mount_options = [
        "loop",
        "rw", # read-write
        "noatime", # Do not update access times for files on this filesystem.
        # https://www.kernel.org/doc/Documentation/filesystems/udf.txt
        "uid=0", # default user
        "gid=0", # default group
        "mode=0644", # default file permissions
        "dmode=0755", # default directory permissions
        #"umask=xxx", # default umask
    ]
    args = [
        "mount",
        "-o", ",".join(mount_options),
        "-t", "udf",
        udf_image_path,
        mount_dir,
    ]
    print("args", args)
    proc = subprocess.run(
        args,
        check=True,
    )


def mount_iso_image(iso_image_path, mount_dir):
    print(f"mounting ISO image: {iso_image_path}")

    # TODO set file times to zero (ctime, mtime, atime)
    # https://github.com/wolfcw/libfaketime
    # TZ=UTC faketime "1970-01-01 00:00:00" date +%s --utc
    mount_options = [
        "loop",
        "ro", # read only
    ]
    args = [
        "mount",
        "-o", ",".join(mount_options),
        "-t", "iso9660",
        iso_image_path,
        mount_dir,
    ]
    print("args", args)
    proc = subprocess.run(
        args,
        check=True,
    )


def unmount_dir(mount_dir):
    print(f"unmounting dir: {mount_dir}")
    args = [
        "umount",
        mount_dir,
    ]
    proc = subprocess.run(
        args,
        check=True,
    )


def test_mount_udf():
    # check if we can mount
    # create empty image file
    udf_image_path = "new-subs-archive.py-tmp.udf"
    create_empty_udf_image(udf_image_path, udf_min_blocks_count, "test")
    mount_dir = "new-subs-archive.py-tmp-mnt"
    os.makedirs(mount_dir, exist_ok=True)
    # unmount previously mounted image
    try:
        unmount_dir(mount_dir)
    except subprocess.CalledProcessError:
        pass
    try:
        mount_udf_image(udf_image_path, mount_dir)
    except subprocess.CalledProcessError:
        os.unlink(udf_image_path)
        os.rmdir(mount_dir)
        raise Exception(f"error: need root privileges to mount UDF image. hint: sudo python3 {sys.argv[0]}")
    unmount_dir(mount_dir)
    os.unlink(udf_image_path)
    os.rmdir(mount_dir)


def test_mount_iso():
    # check if we can mount
    # create empty image file
    iso_image_path = "new-subs-archive.py-tmp.iso"
    create_empty_iso_image(iso_image_path, "TEST")
    mount_dir = "new-subs-archive.py-tmp-mnt"
    os.makedirs(mount_dir, exist_ok=True)
    # unmount previously mounted image
    try:
        unmount_dir(mount_dir)
    except subprocess.CalledProcessError:
        pass
    try:
        mount_iso_image(iso_image_path, mount_dir)
    except subprocess.CalledProcessError:
        os.unlink(iso_image_path)
        os.rmdir(mount_dir)
        raise Exception(f"error: need root privileges to mount ISO image. hint: sudo python3 {sys.argv[0]}")
    unmount_dir(mount_dir)
    os.unlink(iso_image_path)
    os.rmdir(mount_dir)


# https://stackoverflow.com/a/1131238/10440128
def md5_filepath(filepath):
    file_hash = hashlib.md5()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            file_hash.update(chunk)
    return file_hash.hexdigest()


def pack_files(sum_files, sum_size):
    output_paths = []
    if repeat_count == 1:
        # dont repeat
        return pack_files_inner(sum_files, sum_size)
    print(f"creating {repeat_count} identical images ...")
    for _ in range(repeat_count):
        output_path = pack_files_inner(sum_files, sum_size)
        output_paths.append(output_path)
    print(f"creating {repeat_count} identical images done")
    print(f"identical image files:")
    for output_path in output_paths:
        print(f"  {output_path}")
    print(f"comparing checksums of {repeat_count} identical images ...")
    checksums = []
    print(f"identical image checksums:")
    for output_path in output_paths:
        checksum = md5_filepath(output_path)
        print(f"  {checksum}  {output_path}")
        # compare to all previous checksums
        # fail on the first mismatch
        for previous_checksum in checksums:
            assert checksum == previous_checksum, "failed to produce identical image files"
        checksums.append(checksum)


def pack_files_inner(sum_files, sum_size):
    # sum_files is sorted by natsorted = numeric sort
    first_file = sum_files[0]
    last_file = sum_files[-1]
    if last_file.endswith("/filenames.txt"):
        last_file = sum_files[-2]
    print(f"first_file {first_file}")
    print(f"last_file {last_file}")
    first_num = int(os.path.basename(first_file).split(".")[0])
    last_num = int(os.path.basename(last_file).split(".")[0])
    sum_files = sorted(sum_files)
    def get_archive_path(first_num, last_num, extension, suffix_before_duplicate=None):
        archive_path = f"opensubtitles-{first_num}-{last_num}.{extension}"
        if suffix_before_duplicate:
            archive_path = f"opensubtitles-{first_num}-{last_num}-{suffix_before_duplicate}.{extension}"
        duplicate = 1
        while os.path.exists(archive_path):
            duplicate += 1
            archive_path = f"opensubtitles-{first_num}-{last_num}.{duplicate}.{extension}"
            if suffix_before_duplicate:
                archive_path = f"opensubtitles-{first_num}-{last_num}-{suffix_before_duplicate}.{duplicate}.{extension}"
        return archive_path
    if output_format == "tar":
        archive_path = get_archive_path(first_num, last_num, "tar")
        pack_files_tar(archive_path, sum_files)
        return archive_path
    if output_format == "iso":
        archive_path = get_archive_path(first_num, last_num, "iso")
        volid = f"OPENSUBTITLES_{first_num}_{last_num}"
        pack_files_iso(archive_path, sum_files, volid)
        return archive_path
    if output_format == "udf":
        # mkudffs creates pure UDF, so we use extension "udf"
        archive_path = get_archive_path(first_num, last_num, "udf")
        label = f"opensubtitles-{first_num}-{last_num}"
        #group_label = f"opensubtitles"
        pack_files_udf(archive_path, sum_files, label, sum_size)
        return archive_path
    if output_format == "udf-pycdlib":
        # pycdlib creates impure UDF, so we use extension "iso"
        archive_path = get_archive_path(first_num, last_num, "iso")
        label = f"opensubtitles-{first_num}-{last_num}"
        #group_label = f"opensubtitles"
        pack_files_udf_pycdlib(archive_path, sum_files, label, sum_size)
        return archive_path
    if output_format == "sqlite":
        table_name = f"opensubtitles_zipfiles_{first_num}_{last_num}"
        if sqlite_compare_page_sizes:
            archive_path = None
            for page_size in sqlite_page_sizes:
                extra_suffix = f"pagesize{page_size}"
                archive_path = get_archive_path(first_num, last_num, "db", extra_suffix)
                pack_files_sqlite(archive_path, sum_files, table_name, page_size)
            return archive_path
        archive_path = get_archive_path(first_num, last_num, "db")
        pack_files_sqlite(archive_path, sum_files, table_name)
        return archive_path
    #elif output_format == "fat32":
    #    archive_path = f"opensubtitles-{first_num}-{last_num}.fat32"
    #    pack_files_fat32(archive_path, sum_files, sum_size)
    assert False, f"unknown output_format: {output_format}"


def pack_files_tar(archive_path, sum_files):
    print(f"packing {len(sum_files)} files to {archive_path}")
    sum_files_file = "new-subs-archive.py-sum_files.txt"
    with open(sum_files_file, "w") as f:
        f.write("\n".join(sum_files) + "\n")
    args = [
        "tar",
        # all these options are required to create reproducible archives
        # https://reproducible-builds.org/docs/archives/
        # TODO create reproducible archives with python tarfile
        # so this also works on windows
        "--format=gnu",
        "--sort=name", # sort filenames, independent of locale. tar v1.28
        "--mtime=0",
        "--owner=0",
        "--group=0",
        "--numeric-owner",
        "-c",
        "-f", archive_path,
        "-T", sum_files_file,
    ]
    subprocess.run(
        args,
        check=True,
    )


def pack_files_sqlite(db_path, sum_files, table_name, page_size=None):
    print(f"creating database {db_path} ...")
    t1 = time.time()
    assert os.path.exists(db_path) == False, f"error: output file exists: {db_path}"
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    if page_size == None:
        page_size = sqlite_page_size
    cur.executescript(f"PRAGMA page_size = {sqlite_page_size}; VACUUM;")
    cur.execute(
        f"CREATE TABLE {table_name} (\n"
        f"  num INTEGER PRIMARY KEY,\n"
        f"  name TEXT,\n"
        f"  content BLOB\n"
        f")"
    )
    sql_query = f"INSERT INTO {table_name} (num, name, content) VALUES (?, ?, ?)"
    for file_path in sum_files:
        file_name = os.path.basename(file_path)
        name_parts = file_name.split(".")
        num = int(name_parts[0])
        assert name_parts[-1] == "zip", f"not a zip file: {file_path}"
        # check for legacy file format before new-subs-rename-remove-num-part.py
        assert name_parts[-2] != f"({num})", f"bad filename format: {file_path}"
        name = ".".join(name_parts[1:-1])
        # too complex
        # store only files here
        # and use a separate DB for all metadata
        #lang = name_parts[-3]
        #assert re.match(r"^[a-z]{3}$", lang)
        with open(file_path, "rb") as f:
            content = f.read()
        sql_args = (num, name, content)
        cur.execute(sql_query, sql_args)
    con.commit()
    con.close()
    t2 = time.time()
    print(f"creating database {db_path} done in {t2 - t1} seconds")


def pack_files_iso(iso_image_path, sum_files, volid):
    """
    ignore this error? ISO seems fine. later: error is gone.
    FIXME fails to create large iso of 1GB
    libisofs: FATAL : Image is most likely damaged. Calculated/written tree end address mismatch.
    libisofs: FATAL : Image is most likely damaged. Calculated/written image end address mismatch.
    libburn : FAILURE : Premature end of input encountered. Missing: 2048 bytes
    """
    t1 = time.time()
    print(f"packing {len(sum_files)} files to {iso_image_path}")
    print(f"creating image {iso_image_path} ...")
    sum_files_file = "new-subs-archive.py-sum_files.txt"
    with open(sum_files_file, "w") as f:
        f.write("\n".join(sum_files) + "\n")
    # TODO is this reproducible?
    assert re.match(r"^[A-Z0-9_]{0,32}$", volid), f"invalid volid: {repr(volid)}"
    # note: xorriso does not produce UDF filesystems
    args = [
        #"mkisofs",
        "xorrisofs", # mkisofs compatibility mode of xorriso
        "--modification-date=1970010100000000", # YYYYMMDDhhmmsscc
        "--set_all_file_dates", "set_to_mtime",
        "-uid", "0",
        "-gid", "0",
        "-volid", volid,
        #"--gpt_disk_guid", "modification-date",
        "--gpt_disk_guid", "00000000000000000000000000000000",
        "-no-cache-inodes", # we have no hardlinks
        "-dir-mode", "0755",
        "-file-mode", "0644", # we have no executable files
        # To create reproducible ISO-9660 filesystem images,
        # the options: -creation-date, -effective-date, -modification-date and -noatime need to be specified
        # and the -o option must not be used.
        "-output", iso_image_path, # If not specified, stdout is used.
        "-input-charset", "utf8",
        "-preparer", "", # default: XORRISO-1.5.4 2021.02.06.123001, LIBISOBURN-1.5.4, LIBISOFS-1.5.4, LIBBURN-1.5.4
        # TODO how to set file paths in the image?
        # all files are written to the root directory
        "-path-list", sum_files_file,
        # Allow more than one dot in filenames (e.g. .tar.gz) (violates ISO9660)
        # ignored by xorrisofs
        #"-allow-multidot",
    ]
    try:
        proc = subprocess.run(
            args,
            check=True,
            env={
                "PATH": os.environ["PATH"],
                "SOURCE_DATE_EPOCH": "0", # for xorriso
            },
            # capture output because xorrisofs is too verbose
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            encoding="utf8",
        )
    except subprocess.CalledProcessError as err:
        print(f"creating image {iso_image_path} done with error")
        print(f"xorrisofs output:")
        print(proc.stdout)
        print()
    t2 = time.time()
    dt = t2 - t1
    print(f"creating image {iso_image_path} done in {dt} seconds")
    assert os.path.exists(iso_image_path), f"xorrisofs failed to create image: {iso_image_path}"
    # no. this takes long and requires root privileges
    # easier to create two identical images and assert equality
    # see repeat_count
    check_files = False
    if check_files:
        # check md5sum of all files
        t1 = time.time()
        print(f"checking files in {iso_image_path} ...")
        mount_dir = "new-subs-archive.py-tmp-mnt"
        os.makedirs(mount_dir, exist_ok=True)
        mount_iso_image(iso_image_path, mount_dir)
        for idx, src_file_path in enumerate(sum_files):
            if idx % 1000 == 0:
                print(f"progress: done {idx} of {len(sum_files)} files = {idx/len(sum_files)*100:.1f}%")
            with open(src_file_path, "rb") as f:
                expected_md5 = hashlib.md5(f.read()).hexdigest()
            dst_file_path = mount_dir + "/" + os.path.basename(src_file_path)
            with open(dst_file_path, "rb") as f:
                actual_md5 = hashlib.md5(f.read()).hexdigest()
            if actual_md5 != expected_md5:
                # cleanup
                unmount_dir(mount_dir)
                raise Exception(f"failed to verify file: {src_file_path} - expected md5: {expected_md5} - actual md5: {actual_md5}")
        unmount_dir(mount_dir)
        t2 = time.time()
        dt = t2 - t1
        print(f"checking files in {iso_image_path} done in {dt} seconds")


def pack_files_udf(output_path, sum_files, label, sum_size):
    udf_image_path = output_path
    print(f"packing {len(sum_files)} files to {output_path}")
    sum_files_file = "new-subs-archive.py-sum_files.txt"
    with open(sum_files_file, "w") as f:
        f.write("\n".join(sum_files) + "\n")
    # https://en.wikipedia.org/wiki/Universal_Disk_Format
    # Max. volume size:
    #   2 TiB (with 512-byte sectors)
    #   8 TiB (with 2 KiB sectors, like most optical discs)
    #   16 TiB (with 4 KiB sectors)
    # Max. filename length	255 bytes (path 1023 bytes)
    # note: dont use "genisoimage -udf" or "mkisofs -udf"
    # as they do not create a "pure UDF" filesystem
    # https://askubuntu.com/questions/1152527/creating-a-pure-udf-iso
    blocksize = 512
    #blocksize = 2048 # TODO?
    #blocksize = 4096 # TODO?
    blocks_count = math.ceil((1 + size_tolerance_udf) * sum_size / blocksize)
    blocks_count = max(blocks_count, udf_min_blocks_count)
    # FIXME OSError: [Errno 28] No space left on device
    blocks_count = 10 * blocks_count
    print(f"creating UDF filesystem of {blocks_count} * {blocksize} = {blocks_count * blocksize} bytes")

    # TODO is this reproducible?

    # create empty image file
    create_empty_udf_image(udf_image_path, udf_min_blocks_count, label)

    # unmount previously mounted image
    try:
        unmount_dir(mount_dir)
    except subprocess.CalledProcessError:
        pass

    # mount image file
    os.makedirs(mount_dir, exist_ok=True)
    mount_udf_image(udf_image_path, mount_dir)

    print(f"writing files to UDF image")
    for zipfile_path in sum_files:
        zipfile_name = os.path.basename(zipfile_path)
        dst_path = f"{mount_dir}/{zipfile_name}"
        # Copy the contents (no metadata)
        shutil.copyfile(zipfile_path, dst_path)
        # TODO subprocess.run(["faketime", "asdf", "cp", zipfile_path, dst_path])
    unmount_dir(mount_dir)
    os.rmdir(mount_dir)


def pack_files_udf_pycdlib(output_path, sum_files, label, sum_size):
    udf_image_path = output_path
    print(f"packing {len(sum_files)} files to {output_path}")
    iso = pycdlib.PyCdlib()
    udf_version = "2.60" # only supported UDF version in pycdlib
    iso.new(udf=udf_version)
    #foostr = b'foo\n'
    #iso.add_fp(BytesIO(foostr), len(foostr), '/FOO.;1', udf_path='/foo')
    #iso.add_directory('/DIR1', udf_path='/dir1')
    file_handles = []
    for input_path in sum_files:
        size = os.path.getsize(input_path)
        basename = os.path.basename(input_path)
        udf_path = "/" + basename
        # ISO9660 filenames at interchange level 1 cannot have more than 8 characters or 3 characters in the extension
        iso_path = "/" + basename.split(".", 1)[0]
        # note: must keep file_handle until after iso.close()
        file_handle = open(input_path, "rb")
        iso.add_fp(file_handle, size, iso_path, udf_path=udf_path)
        file_handles.append(file_handle)
    iso.write(output_path)
    iso.close()
    for file_handle in file_handles:
        file_handle.close()


print(f"output_format: {output_format}")


print()
print("checking tools ...")

if output_format == "iso":
    proc = subprocess.run(
        ["xorrisofs"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        encoding="utf8",
    )
    first_line = proc.stdout.lstrip().split("\n", 1)[0]
    print(f"found xorrisofs: {first_line}")

# we need root privileges to mount images
if output_format == "udf":
    test_mount_udf()
#if output_format == "iso":
#    test_mount_iso()

print("checking tools done")


sum_size = 0
sum_files = []

max_size_tolerant = max_size * (1 - size_tolerance)


print("calling new-subs-hardlink-num.py ...")
args = [
    sys.executable,
    "new-subs-hardlink-num.py",
]
t1 = time.time()
subprocess.run(
    args,
    check=True,
)
t2 = time.time()
print(f"calling new-subs-hardlink-num.py done in {t2 - t1} seconds")


print()
print(f"collecting input files from {input_dir_short_filenames}")
t1 = time.time()
#sorted_short_names = natsort.natsorted(glob.glob("*.zip", root_dir=input_dir_short_filenames))
short_names = glob.glob("*.zip", root_dir=input_dir_short_filenames)
t2 = time.time()

print(f"collecting input files from {input_dir_long_filenames}")
t1 = time.time()
#sorted_long_names = natsort.natsorted(glob.glob("*.zip", root_dir=input_dir_long_filenames))
long_names = glob.glob("*.zip", root_dir=input_dir_long_filenames)
t2 = time.time()

input_numbers_list = []
print(f"creating input_numbers_list")
for short_name in short_names:
    num = int(short_name[0:-4])
    input_numbers_list.append(num)
input_numbers_list = sorted(input_numbers_list)


# all nums are either in
# f"{input_dir_long_filenames}/{num}.not-found"
# or
# f"{input_dir_short_filenames}/{num}.zip"
# see also: missing_files in fetch-subs.py
"""
print("checking for missing files")
first_num = input_numbers_list[0]
last_num = input_numbers_list[-1]
has_missing_files = False
for num in range(first_num, last_num + 1):
    if os.path.exists(f"{input_dir_short_filenames}/{num}.zip"):
        continue
    if os.path.exists(f"{input_dir_long_filenames}/{num}.not-found"):
        continue
    if has_missing_files == False:
        print("missing numbers:")
    print(num)
    has_missing_files = True
assert has_missing_files == False, "error: missing files"
raise NotImplementedError
"""


print(f"creating long_names_dict")
long_names_dict = {}
for long_name in long_names:
    num = int(long_name.split(".", 1)[0])
    long_names_dict[num] = long_name


print()
print(f"processing files ...")
sum_names_long = []
for num in input_numbers_list:
    if num < continue_from:
        continue
    short_name = f"{num}.zip" # trivial
    try:
        long_name = long_names_dict[num]
    except KeyError:
        # bug in new-subs-hardlink-num.py
        # ".zip" should be ".not-found"
        # new-subs/9331545.not-found
        # new-subs-num/9331545.zip
        continue
    zip_file = None
    if use_short_filenames:
        zip_file = f"{input_dir_short_filenames}/{short_name}"
    else:
        zip_file = f"{input_dir_long_filenames}/{long_name}"
    size = os.path.getsize(zip_file)
    #print(size, short_name)
    if size == 0: # legacy. these files should be named f"{num}.not-found"
        continue
    sum_size += size
    if sum_size < max_size_tolerant:
        sum_files.append(zip_file)
        if store_filenames:
            sum_names_long.append(long_name)
    else:
        sum_size -= size

        # add filenames.txt
        if store_filenames:
            tempdir = "new-subs-archive.py-tempdir"
            os.makedirs(tempdir, exist_ok=True)
            filenames_txt_path = f"{tempdir}/filenames.txt"
            with open(filenames_txt_path, "w") as f:
                f.write("\n".join(sum_names_long) + "\n")
            sum_files.append(filenames_txt_path)
            sum_size += os.path.getsize(filenames_txt_path)

        print()
        print(f"packing {len(sum_files)} files at sum_size {sum_size}")
        pack_files(sum_files, sum_size)

        # reset
        sum_size = 0
        sum_files = []
        sum_names_long = []

        # continue
        sum_size += size
        sum_files.append(zip_file)
        if store_filenames:
            sum_names_long.append(long_name)


print()
print("NOTE: packing last archive")


print()
print(f"packing {len(sum_files)} files at sum_size {sum_size}")
pack_files(sum_files, sum_size)
