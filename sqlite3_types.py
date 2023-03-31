from ctypes import *

# https://stackoverflow.com/questions/1825715/how-to-pack-and-unpack-using-ctypes-structure-str
# https://stackoverflow.com/questions/14215715/reading-a-binary-file-into-a-struct

class FileHeader(BigEndianStructure):
    #_pack_ = 1 # TODO what?
    _fields_ = [
        # 0 16 header string: "SQLite format 3" + "\x00"
        ("header_string", 16 * c_char),

        # 16 2 The database page size in bytes.
        # Must be a power of two between 512 and 32768 inclusive,
        # or the value 1 representing a page size of 65536.
        ("page_size", c_short),

        # 18 1 File format write version. 1 for legacy; 2 for WAL.
        ("format_write_version", c_byte),

        # 19 1 File format read version. 1 for legacy; 2 for WAL.
        ("format_read_version", c_byte),

        # 20 1 Bytes of unused "reserved" space at the end of each page. Usually 0.
        ("reserved_space", c_byte),

        # 21 1 Maximum embedded payload fraction. Must be 64.
        ("max_embedded_payload_fraction", c_byte),

        # 22 1 Maximum embedded payload fraction. Must be 64.
        ("min_embedded_payload_fraction", c_byte),

        # 23 1 Leaf payload fraction. Must be 32.
        ("leaf_payload_fraction", c_byte),

        # 24 4 File change counter.
        ("file_change_counter", c_int),

        # 28 4 Size of the database file in pages. The "in-header database size".
        ("database_size_in_pages", c_int),

        # 32 4 Page number of the first freelist trunk page.
        ("first_freelist_page", c_int),

        # 36 4 Total number of freelist pages.
        ("num_freelist_page", c_int),

        # 40 4 The schema cookie.
        ("schema_cookie", c_int),

        # 44 4 The schema format number. Supported schema formats are 1, 2, 3, and 4.
        ("schema_format_number", c_int),

        # 48 4 Default page cache size.
        ("default_page_cache_size", c_int),

        # 52 4 The page number of the largest root b-tree page when in auto-vacuum or incremental-vacuum modes, or zero otherwise.
        ("largest_root_b_tree_page_number", c_int),

        # 56 4 The database text encoding. A value of 1 means UTF-8. A value of 2 means UTF-16le. A value of 3 means UTF-16be.
        ("database_text_encoding", c_int),

        # 60 4 The "user version" as read and set by the user_version pragma.
        ("pragma_user_version", c_int),

        # 64 4 True (non-zero) for incremental-vacuum mode. False (zero) otherwise.
        ("incremental_vacuum_mode", c_int),

        # 68 4 The "Application ID" set by PRAGMA application_id.
        ("pragma_application_id", c_int),

        # 72 20 Reserved for expansion. Must be zero.
        ("reserved_for_expansion", 20 * c_byte),

        # 92 4 The version-valid-for number.
        ("version_valid_for_number", c_int),

        # 96 4 SQLITE_VERSION_NUMBER
        ("sqlite_version_number", c_int),
    ]
