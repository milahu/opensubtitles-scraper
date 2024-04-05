#!/usr/bin/env python3

# based on find_ads.py

import sys
import os
import re

# https://github.com/tkarabela/pysubs2/issues/43 # Add character encoding autodetection
#sys.path.append(os.path.dirname(sys.argv[0]) + "/lib/thirdparty/pysubs2")
# https://github.com/tkarabela/pysubs2/issues/43#issuecomment-1987206922
# ignore text encoding, and parse the raw bytes
# https://github.com/tkarabela/pysubs2/pull/84
# https://github.com/milahu/pysubs2bytes
sys.path.append(os.path.dirname(sys.argv[0]) + "/lib/thirdparty/pysubs2bytes")

import pysubs2



# https://stackoverflow.com/a/78136529/10440128
def regex_escape_fixed_string(string):
    "escape fixed string for regex"
    if type(string) == bytes:
        return re.sub(rb"[][(){}?*+.^$]", lambda m: b"\\" + m.group(), string)
    return re.sub(r"[][(){}?*+.^$]", lambda m: "\\" + m.group(), string)



# keywords to find advertisment candidates
# ignore case: text.lower()
bad_words = (
    b"www.",
    b".com",
    b".co.",
    b".org",
    b".net",
    b".info",
    b".link",
    b"edited by",
    b"corrected by",
    b"correction by",
    b"ripped by",
    b"fps",
    b"adapted by",
    b"arranged by",
    b"encoded by",
    b"re-encode by",
    b"resynced by",
    b"resync by",
    b"re-synced by",
    b"synced by",
    b"sync by",
    b"synchronized by",
    b"synchronization by",
    b"translated by",
    b"translation by",
    b"subtitle by",
    b"subtitles by",
    b"subtitling by",
    b"subscene",
    b"opensubtitles",
    b"open-subtitles",
    b"crazy4TV",
    b"addic7ed",
    b"explosiveskull",
    b"thepiratebay",
    b"playships",
    #b"member",
    #b"crew",
)

bad_words = tuple(map(lambda word: word.lower(), bad_words))

# when a sub has no fps value, use this pseudo fps
# this will produce wrong timings, but here, we dont care
fallback_pseudo_fps = 24

seen_text_set = set()
bad_text_list_1 = []
bad_text_list_2 = []
todo_text_list = []

def get_file_header_text(subfile_path):
    return f"################ subfile: {subfile_path} ################".encode("utf8")

file_header_regex = re.compile(b"################ subfile: (.*) ################")

for subfile_path in sys.argv[1:]:

    # TODO keep_html_tags=True
    # TODO keep_newlines=True # todo implement. dont replace "\n" with "\\N"

    args = dict(
        # subrip
        keep_html_tags=True,
        keep_unknown_html_tags=True,
        #keep_newlines=True,
        # microdvd
        keep_style_tags=True,
    )

    try:
        #ssa_event_list = pysubs2.load(subfile_path)
        #ssa_event_list = pysubs2.load(subfile_path, encoding=None)
        ssa_event_list = pysubs2.load(subfile_path, **args)
    except pysubs2.exceptions.UnknownFPSError:
        # example: 3614024: fps = 0
        ssa_event_list = pysubs2.load(subfile_path, fps=fallback_pseudo_fps, **args)
    except pysubs2.exceptions.FormatAutodetectionError:
        print(f"FIXME pysubs2.exceptions.FormatAutodetectionError: subfile_path = {subfile_path}")
        continue
    except FileNotFoundError:
        continue

    file_header_text = get_file_header_text(os.path.basename(subfile_path))

    bad_text_list_1.append(file_header_text)
    bad_text_list_2.append(file_header_text)
    todo_text_list.append(file_header_text)

    prev_text = None
    prev_is_bad_text = False

    seen_context_set = set()

    for ssa_event_idx, ssa_event in enumerate(ssa_event_list):

        text = ssa_event.text

        # no. we also need the original markup (colors, fonts)
        #plaintext = ssa_event.plaintext
        #print("plaintext", repr(plaintext))

        #if type(text) == bytes:
        #    text = text.decode("utf8")
        # https://github.com/tkarabela/pysubs2/pull/84
        # use bytestrings
        assert type(text) == bytes
        if text == b"": continue
        if text in seen_text_set:
            prev_text = text
            continue
        seen_text_set.add(text)
        is_bad_text = False
        if not is_bad_text:
            text_lower = text.lower()
            for word in bad_words:
                if word in text_lower:
                    if prev_text:
                        if not prev_text in seen_context_set:
                            # add context before match
                            #bad_text_list.append(prev_text)
                            bad_text_list_1.append(prev_text)
                            seen_context_set.add(prev_text)
                    #bad_text_list.append(text)
                    bad_text_list_1.append(text)
                    #is_bad_text = True
                    is_bad_text = 1
                    break
        if not is_bad_text:
            # subtitles longer than 5 seconds are suspicious
            # ads from opensubtitles usually last 6 seconds
            text_duration = ssa_event.end - ssa_event.start
            #print("text", text_duration, repr(text))
            if text_duration > 5000:
                #is_bad_text = True
                is_bad_text = 2
        if not is_bad_text:
            todo_text_list.append(text)
            if prev_is_bad_text:
                if not text in seen_context_set:
                    # add context after match
                    #bad_text_list.append(text)
                    if is_bad_text == 1:
                        bad_text_list_1.append(text)
                    elif is_bad_text == 2:
                        bad_text_list_2.append(text)
                    seen_context_set.add(text)
        prev_text = text
        prev_is_bad_text = is_bad_text

current_subfile_path = None

def print_text(text):
    global current_subfile_path
    match = file_header_regex.fullmatch(text)
    if match:
        subfile_path = match.group(1)
        current_subfile_path = subfile_path
        return
    if current_subfile_path:
        # print header before first text
        print()
        print("        # " + current_subfile_path.decode("utf8"))
        current_subfile_path = None

    #lines = tuple(map(regex_escape_fixed_string, text.split(b"\n")))
    lines = tuple(map(regex_escape_fixed_string, text.split(rb"\N")))

    print("        " + repr(lines) + ",")

print("    regex_lines_list = (")

print()
print("        # bad_text_list_1")
for text in bad_text_list_1:
    print_text(text)

print()
print("        # bad_text_list_2")
for text in bad_text_list_2:
    print_text(text)

print()
print("        # todo_text_list")
for text in todo_text_list:
    print_text(text)

print()
print("    )")
