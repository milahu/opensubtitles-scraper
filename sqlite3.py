# This is a generated file! Please edit source .ksy file and use kaitai-struct-compiler to rebuild

import kaitaistruct
from kaitaistruct import KaitaiStruct, KaitaiStream, BytesIO
from enum import Enum


if getattr(kaitaistruct, 'API_VERSION', (0, 9)) < (0, 9):
    raise Exception("Incompatible Kaitai Struct Python API: 0.9 or later is required, but you have %s" % (kaitaistruct.__version__))

import vlq_base128_be
class Sqlite3(KaitaiStruct):
    """SQLite3 is a popular serverless SQL engine, implemented as a library
    to be used within other applications. It keeps its databases as
    regular disk files.
    
    Every database file is segmented into pages. First page (starting at
    the very beginning) is special: it contains a file-global header
    which specifies some data relevant to proper parsing (i.e. format
    versions, size of page, etc). After the header, normal contents of
    the first page follow.
    
    Each page would be of some type, and generally, they would be
    reached via the links starting from the first page. First page type
    (`root_page`) is always "btree_page".
    
    .. seealso::
       Source - https://www.sqlite.org/fileformat.html
    """

    class Versions(Enum):
        legacy = 1
        wal = 2

    class Encodings(Enum):
        utf_8 = 1
        utf_16le = 2
        utf_16be = 3
    def __init__(self, _io, _parent=None, _root=None):
        self._io = _io
        self._parent = _parent
        self._root = _root if _root else self
        self._read()

    def _read(self):
        self.magic = self._io.read_bytes(16)
        if not self.magic == b"\x53\x51\x4C\x69\x74\x65\x20\x66\x6F\x72\x6D\x61\x74\x20\x33\x00":
            raise kaitaistruct.ValidationNotEqualError(b"\x53\x51\x4C\x69\x74\x65\x20\x66\x6F\x72\x6D\x61\x74\x20\x33\x00", self.magic, self._io, u"/seq/0")
        self.len_page_mod = self._io.read_u2be()
        self.write_version = KaitaiStream.resolve_enum(Sqlite3.Versions, self._io.read_u1())
        self.read_version = KaitaiStream.resolve_enum(Sqlite3.Versions, self._io.read_u1())
        self.reserved_space = self._io.read_u1()
        self.max_payload_frac = self._io.read_u1()
        self.min_payload_frac = self._io.read_u1()
        self.leaf_payload_frac = self._io.read_u1()
        self.file_change_counter = self._io.read_u4be()
        self.num_pages = self._io.read_u4be()
        self.first_freelist_trunk_page = self._io.read_u4be()
        self.num_freelist_pages = self._io.read_u4be()
        self.schema_cookie = self._io.read_u4be()
        self.schema_format = self._io.read_u4be()
        self.def_page_cache_size = self._io.read_u4be()
        self.largest_root_page = self._io.read_u4be()
        self.text_encoding = KaitaiStream.resolve_enum(Sqlite3.Encodings, self._io.read_u4be())
        self.user_version = self._io.read_u4be()
        self.is_incremental_vacuum = self._io.read_u4be()
        self.application_id = self._io.read_u4be()
        self.reserved = self._io.read_bytes(20)
        self.version_valid_for = self._io.read_u4be()
        self.sqlite_version_number = self._io.read_u4be()
        self.root_page = Sqlite3.BtreePage(self._io, self, self._root)

    class Serial(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.code = vlq_base128_be.VlqBase128Be(self._io)

        @property
        def is_blob(self):
            if hasattr(self, '_m_is_blob'):
                return self._m_is_blob

            self._m_is_blob =  ((self.code.value >= 12) and ((self.code.value % 2) == 0)) 
            return getattr(self, '_m_is_blob', None)

        @property
        def is_string(self):
            if hasattr(self, '_m_is_string'):
                return self._m_is_string

            self._m_is_string =  ((self.code.value >= 13) and ((self.code.value % 2) == 1)) 
            return getattr(self, '_m_is_string', None)

        @property
        def len_content(self):
            if hasattr(self, '_m_len_content'):
                return self._m_len_content

            if self.code.value >= 12:
                self._m_len_content = (self.code.value - 12) // 2

            return getattr(self, '_m_len_content', None)


    class BtreePage(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.page_type = self._io.read_u1()
            self.first_freeblock = self._io.read_u2be()
            self.num_cells = self._io.read_u2be()
            self.ofs_cells = self._io.read_u2be()
            self.num_frag_free_bytes = self._io.read_u1()
            if  ((self.page_type == 2) or (self.page_type == 5)) :
                self.right_ptr = self._io.read_u4be()

            self.cells = []
            for i in range(self.num_cells):
                self.cells.append(Sqlite3.RefCell(self._io, self, self._root))



    class CellIndexLeaf(KaitaiStruct):
        """
        .. seealso::
           Source - https://www.sqlite.org/fileformat.html#b_tree_pages
        """
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.len_payload = vlq_base128_be.VlqBase128Be(self._io)
            self._raw_payload = self._io.read_bytes(self.len_payload.value)
            _io__raw_payload = KaitaiStream(BytesIO(self._raw_payload))
            self.payload = Sqlite3.CellPayload(_io__raw_payload, self, self._root)


    class Serials(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.entries = []
            i = 0
            while not self._io.is_eof():
                self.entries.append(vlq_base128_be.VlqBase128Be(self._io))
                i += 1



    class CellTableLeaf(KaitaiStruct):
        """
        .. seealso::
           Source - https://www.sqlite.org/fileformat.html#b_tree_pages
        """
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.len_payload = vlq_base128_be.VlqBase128Be(self._io)
            self.row_id = vlq_base128_be.VlqBase128Be(self._io)
            self._raw_payload = self._io.read_bytes(self.len_payload.value)
            _io__raw_payload = KaitaiStream(BytesIO(self._raw_payload))
            self.payload = Sqlite3.CellPayload(_io__raw_payload, self, self._root)


    class CellPayload(KaitaiStruct):
        """
        .. seealso::
           Source - https://sqlite.org/fileformat2.html#record_format
        """
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.len_header_and_len = vlq_base128_be.VlqBase128Be(self._io)
            self._raw_column_serials = self._io.read_bytes((self.len_header_and_len.value - 1))
            _io__raw_column_serials = KaitaiStream(BytesIO(self._raw_column_serials))
            self.column_serials = Sqlite3.Serials(_io__raw_column_serials, self, self._root)
            self.column_contents = []
            for i in range(len(self.column_serials.entries)):
                self.column_contents.append(Sqlite3.ColumnContent(self.column_serials.entries[i], self._io, self, self._root))



    class CellTableInterior(KaitaiStruct):
        """
        .. seealso::
           Source - https://www.sqlite.org/fileformat.html#b_tree_pages
        """
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.left_child_page = self._io.read_u4be()
            self.row_id = vlq_base128_be.VlqBase128Be(self._io)


    class CellIndexInterior(KaitaiStruct):
        """
        .. seealso::
           Source - https://www.sqlite.org/fileformat.html#b_tree_pages
        """
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.left_child_page = self._io.read_u4be()
            self.len_payload = vlq_base128_be.VlqBase128Be(self._io)
            self._raw_payload = self._io.read_bytes(self.len_payload.value)
            _io__raw_payload = KaitaiStream(BytesIO(self._raw_payload))
            self.payload = Sqlite3.CellPayload(_io__raw_payload, self, self._root)


    class ColumnContent(KaitaiStruct):
        def __init__(self, ser, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self.ser = ser
            self._read()

        def _read(self):
            if  ((self.serial_type.code.value >= 1) and (self.serial_type.code.value <= 6)) :
                _on = self.serial_type.code.value
                if _on == 4:
                    self.as_int = self._io.read_u4be()
                elif _on == 6:
                    self.as_int = self._io.read_u8be()
                elif _on == 1:
                    self.as_int = self._io.read_u1()
                elif _on == 3:
                    self.as_int = self._io.read_bits_int_be(24)
                elif _on == 5:
                    self.as_int = self._io.read_bits_int_be(48)
                elif _on == 2:
                    self.as_int = self._io.read_u2be()

            if self.serial_type.code.value == 7:
                self.as_float = self._io.read_f8be()

            if self.serial_type.is_blob:
                self.as_blob = self._io.read_bytes(self.serial_type.len_content)

            self.as_str = (self._io.read_bytes(self.serial_type.len_content)).decode(u"UTF-8")

        @property
        def serial_type(self):
            if hasattr(self, '_m_serial_type'):
                return self._m_serial_type

            self._m_serial_type = self.ser
            return getattr(self, '_m_serial_type', None)


    class RefCell(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.ofs_body = self._io.read_u2be()

        @property
        def body(self):
            if hasattr(self, '_m_body'):
                return self._m_body

            _pos = self._io.pos()
            self._io.seek(self.ofs_body)
            _on = self._parent.page_type
            if _on == 13:
                self._m_body = Sqlite3.CellTableLeaf(self._io, self, self._root)
            elif _on == 5:
                self._m_body = Sqlite3.CellTableInterior(self._io, self, self._root)
            elif _on == 10:
                self._m_body = Sqlite3.CellIndexLeaf(self._io, self, self._root)
            elif _on == 2:
                self._m_body = Sqlite3.CellIndexInterior(self._io, self, self._root)
            self._io.seek(_pos)
            return getattr(self, '_m_body', None)


    @property
    def len_page(self):
        if hasattr(self, '_m_len_page'):
            return self._m_len_page

        self._m_len_page = (65536 if self.len_page_mod == 1 else self.len_page_mod)
        return getattr(self, '_m_len_page', None)


