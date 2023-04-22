# https://github.com/matan1008/pygnuutils/issues/12

# author: Milan Hauth <milahu@gmail.com>
# license: MIT License

import functools

# static idx_t
# file_prefixlen (char const *s, ptrdiff_t *len)
def file_prefixlen(s):
    """
    Return the length of a prefix of S that corresponds to the suffix
    defined by this extended regular expression in the C locale:
        (\.[A-Za-z~][A-Za-z0-9~]*)*$
    Use the longest suffix matching this regular expression,
    except do not use all of S as a suffix if S is nonempty.
    """
    # not:
    #If *LEN is -1, S is a string; set *LEN to S's length.
    #Otherwise, *LEN should be nonnegative, S is a char array,
    #and *LEN does not change.

    #size_t n = *len;  /* SIZE_MAX if N == -1.  */
    n = len(s)
    #idx_t prefixlen = 0;
    prefixlen = 0

    #for (idx_t i = 0; ; )
    i = 0
    while True:
        # "len = -1" is not used
        #if (*len < 0 ? !s[i] : i == n)
        if i == n: # end of string
            #*len = i;
            #return prefixlen;
            return prefixlen

        #i++;
        i += 1
        #prefixlen = i;
        prefixlen = i
        #while (i + 1 < n && s[i] == '.' && (c_isalpha (s[i + 1])
        #                                    || s[i + 1] == '~'))
        # seek to start of extension
        while (
            i + 1 < n and
            s[i] == '.' and
            (s[i + 1].isalpha() or s[i + 1] == '~')
        ):
            # seek to end of extension
            #for (i += 2; i < n and (c_isalnum (s[i]) or s[i] == '~'); i++)
            i += 2
            while i < n and (s[i].isalnum() or s[i] == '~'):
                i += 1


#static int
#order (char const *s, idx_t pos, idx_t len)
def order(s, pos, len):
    """
    Return a version sort comparison value for S's byte at position POS.
    S has length LEN.  If POS == LEN, sort before all non-'~' bytes.
    """
    #if (pos == len)
    #    return -1;
    if pos == len:
        return -1

    #unsigned char c = s[pos];
    c = s[pos]
    #if (c_isdigit (c))
    #    return 0;
    if c.isdigit():
        return 0
    #else if (c_isalpha (c))
    #    return c;
    elif c.isalpha():
        return ord(c)
    #else if (c == '~')
    #    return -2;
    elif c == '~':
        return -2
    else:
        #static_assert (UCHAR_MAX <= (INT_MAX - 1 - 2) / 2);
        #INT_MAX = 32767 # Maximum value for an object of type int
        #assert (UCHAR_MAX <= (INT_MAX - 1 - 2) / 2)
        #return c + UCHAR_MAX + 1;
        UCHAR_MAX = 255 # Maximum value for an object of type unsigned char
        return ord(c) + UCHAR_MAX + 1


# static int _GL_ATTRIBUTE_PURE
# verrevcmp (const char *s1, idx_t s1_len, const char *s2, idx_t s2_len)
def verrevcmp(s1, s1_len, s2, s2_len):
    """
    slightly modified verrevcmp function from dpkg
    S1, S2 - compared char array
    S1_LEN, S2_LEN - length of arrays to be scanned

    This implements the algorithm for comparison of version strings
    specified by Debian and now widely adopted.  The detailed
    specification can be found in the Debian Policy Manual in the
    section on the 'Version' control field.  This version of the code
    implements that from s5.6.12 of Debian Policy v3.8.0.1
    https://www.debian.org/doc/debian-policy/ch-controlfields.html#s-f-Version
    """
    #idx_t s1_pos = 0;
    #idx_t s2_pos = 0;
    s1_pos = 0
    s2_pos = 0
    #while (s1_pos < s1_len || s2_pos < s2_len)
    while s1_pos < s1_len or s2_pos < s2_len:
        #int first_diff = 0;
        first_diff = 0
        #while ((s1_pos < s1_len && !c_isdigit (s1[s1_pos]))
        #        || (s2_pos < s2_len && !c_isdigit (s2[s2_pos])))
        while (
            (s1_pos < s1_len and not s1[s1_pos].isdigit()) or
            (s2_pos < s2_len and not s2[s2_pos].isdigit())
        ):
            #int s1_c = order (s1, s1_pos, s1_len);
            #int s2_c = order (s2, s2_pos, s2_len);
            s1_c = order(s1, s1_pos, s1_len)
            s2_c = order(s2, s2_pos, s2_len)
            #if (s1_c != s2_c)
            if s1_c != s2_c:
                #return s1_c - s2_c;
                return s1_c - s2_c
            #s1_pos++;
            #s2_pos++;
            s1_pos += 1
            s2_pos += 1
        #while (s1_pos < s1_len && s1[s1_pos] == '0')
        while s1_pos < s1_len and s1[s1_pos] == '0':
            #s1_pos++;
            s1_pos += 1
        #while (s2_pos < s2_len && s2[s2_pos] == '0')
        while s2_pos < s2_len and s2[s2_pos] == '0':
            #s2_pos++;
            s2_pos += 1
        #while (s1_pos < s1_len && s2_pos < s2_len
        #        && c_isdigit (s1[s1_pos]) && c_isdigit (s2[s2_pos]))
        while (
            s1_pos < s1_len and
            s2_pos < s2_len and
            s1[s1_pos].isdigit() and
            s2[s2_pos].isdigit()
        ):
            #if (!first_diff)
            if not first_diff:
                #first_diff = s1[s1_pos] - s2[s2_pos];
                first_diff = ord(s1[s1_pos]) - ord(s2[s2_pos])
            #s1_pos++;
            #s2_pos++;
            s1_pos += 1
            s2_pos += 1
        #if (s1_pos < s1_len && c_isdigit (s1[s1_pos]))
        if s1_pos < s1_len and s1[s1_pos].isdigit():
            #return 1;
            return 1
        #if (s2_pos < s2_len && c_isdigit (s2[s2_pos]))
        if s2_pos < s2_len and s2[s2_pos].isdigit():
            #return -1;
            return -1
        #if (first_diff)
        if first_diff:
            #return first_diff;
            return first_diff
    #return 0;
    return 0


# int
# filenvercmp (char const *a, ptrdiff_t alen, char const *b, ptrdiff_t blen)
def filenvercmp(a, alen, b, blen):
    """
    Compare versions A and B.
    """
    if alen == -1:
        alen = len(a)
    if blen == -1:
        blen = len(b)
    # Special case for empty versions.
    # bool aempty = alen < 0 ? !a[0] : !alen;
    #aempty = not a[0] if alen < 0 else not alen
    aempty = a == ""
    # bool bempty = blen < 0 ? !b[0] : !blen;
    #bempty = not b[0] if blen < 0 else not blen
    bempty = b == ""
    #if (aempty)
    if aempty:
        #return -!bempty;
        return -(not bempty)
    #if (bempty)
    if bempty:
        #return 1;
        return 1

    # Special cases for leading ".": "." sorts first, then "..", then
    # other names with leading ".", then other names.
    # if (a[0] == '.')
    if a[0] == ".":
        # {
        # if (b[0] != '.')
        if b[0] != ".":
            # return -1;
            return -1

        # bool adot = alen < 0 ? !a[1] : alen == 1;
        #adot = not a[1] if alen < 0 else alen == 1
        adot = alen == 1
        # bool bdot = blen < 0 ? !b[1] : blen == 1;
        #bdot = not b[1] if blen < 0 else blen == 1
        bdot = blen == 1
        #if (adot)
        if adot:
            #return -!bdot;
            return -(not bdot)
        #if (bdot)
        if bdot:
            #return 1;
            return 1

        # bool adotdot = a[1] == '.' && (alen < 0 ? !a[2] : alen == 2);
        #adotdot = a[1] == '.' and (not a[2] if alen < 0 else alen == 2)
        adotdot = a[1] == '.' and alen == 2
        # bool bdotdot = b[1] == '.' && (blen < 0 ? !b[2] : blen == 2);
        #adotdot = b[1] == '.' and (not b[2] if blen < 0 else blen == 2)
        bdotdot = b[1] == '.' and blen == 2
        # if (adotdot)
        if adotdot:
            # return -!bdotdot;
            return -(not bdotdot)
        # if (bdotdot)
        if bdotdot:
            # return 1;
            return 1
        # }
    #else if (b[0] == '.')
    elif b[0] == '.':
        #return 1;
        return 1

    # Cut file suffixes.
    # idx_t aprefixlen = file_prefixlen (a, &alen);
    aprefixlen = file_prefixlen(a)
    # idx_t bprefixlen = file_prefixlen (b, &blen);
    bprefixlen = file_prefixlen(b)

    # If both suffixes are empty, a second pass would return the same thing.
    # bool one_pass_only = aprefixlen == alen && bprefixlen == blen;
    one_pass_only = aprefixlen == alen and bprefixlen == blen

    # int result = verrevcmp (a, aprefixlen, b, bprefixlen);
    result = verrevcmp(a, aprefixlen, b, bprefixlen)

    # Return the initial result if nonzero, or if no second pass is needed.
    # Otherwise, restore the suffixes and try again.
    # return result || one_pass_only ? result : verrevcmp (a, alen, b, blen);
    return result or result if one_pass_only else verrevcmp(a, alen, b, blen)


# int
# filevercmp (const char *s1, const char *s2)
def filevercmp(a, b):
    """
    Compare versions A and B.
    """
    return filenvercmp(a, -1, b, -1)


fileverkey = functools.cmp_to_key(filevercmp)


filevernamekey = lambda x: (fileverkey(x), x)


def filevernamesorted(array, **kwargs):
    """
    version sort, compatible with GNU coreutils `sort --version-sort`
    """
    return sorted(array, key=filevernamekey, **kwargs)


def test_filevercmp():
    equal_list = [
        ("1.1", "1.01"),
        ("1.1.1", "1.01.01"),
        ("1.1.01", "1.01.1"),
        ("1.01.1", "1.1.01"),
    ]
    for a, b in equal_list:
        #print(f"filevercmp({repr(a)}, {repr(b)}) ->", filevercmp(a, b))
        assert filevercmp(a, b) == 0

    import os, subprocess
    lines = [
        ".",
        "..",
        "...",
        ".1",
        ".01",
        ".001",
        "..1",
        "..01",
        "..001",
        "...1",
        "...01",
        "...001",
        "1",
        "1~",
        "1~~",
        "1.",
        "1.~",
        "1.~~",
        "1.0",
        "1.0~",
        "1.1",
        "1.1~",
        "1.1~~",
        "1.1/",
        "1/",
        "1.01",
        "1.1.1",
        "1.01.1",
        "1.1.01",
        "1.01.01",
        "0",
        "1.1rc1",
        "1.1rc2",
        "1.1-rc1",
        "1.1-rc2",
        "1.1pre1",
        "1.1a",
        "1.1b",
        "a",
        "aa",
        "aaa",
        "ab",
        "abb",
        "aab",
        "b",
    ]

    # wrong order on equality
    #lines_sorted = sorted(lines, key=fileverkey)
    #lines_sorted = reversed(sorted(lines, key=fileverkey, reverse=True)) # still wrong

    # sort by alphabet, then sort by version
    # sorting by alphabet is required to sort equal versions
    #lines_sorted = sorted(sorted(lines), key=fileverkey)
    lines_sorted = filevernamesorted(lines)

    def join(lines):
        return "\n".join(lines) + "\n"

    actual = join(lines_sorted)

    proc = subprocess.run(
        ["sort", "-V"],
        encoding="utf8",
        input=join(lines),
        capture_output=True,
        check=True,
        timeout=10,
        env={
            "PATH": os.environ["PATH"],
            "LC_ALL": "C",
        },
    )
    expected = proc.stdout

    def fmt_cols(actual, expected):
        actual_lines = actual.split("\n")
        expected_lines = expected.split("\n")
        left_len = 0
        for line in actual_lines:
            left_len = max(left_len, len(line))
        result = ""
        for idx, actual_line in enumerate(actual_lines):
            expected_line = expected_lines[idx]
            result += f"{actual_line.ljust(left_len)} | {expected_line}\n"
        return result

    assert actual == expected, f"actual vs expected:\n\n{fmt_cols(actual, expected)}"


if __name__ == "__main__":
    test_filevercmp()
