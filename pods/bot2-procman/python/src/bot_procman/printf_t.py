"""LCM type definitions
This file automatically generated by lcm.
DO NOT MODIFY BY HAND!!!!
"""

import cStringIO as StringIO
import struct

class printf_t(object):
    __slots__ = ["utime", "deputy_name", "sheriff_id", "text"]

    def __init__(self):
        self.utime = 0
        self.deputy_name = ""
        self.sheriff_id = 0
        self.text = ""

    def encode(self):
        buf = StringIO.StringIO()
        buf.write(printf_t._get_packed_fingerprint())
        self._encode_one(buf)
        return buf.getvalue()

    def _encode_one(self, buf):
        buf.write(struct.pack(">q", self.utime))
        __deputy_name_encoded = self.deputy_name.encode('utf-8')
        buf.write(struct.pack('>I', len(__deputy_name_encoded)+1))
        buf.write(__deputy_name_encoded)
        buf.write("\0")
        buf.write(struct.pack(">i", self.sheriff_id))
        __text_encoded = self.text.encode('utf-8')
        buf.write(struct.pack('>I', len(__text_encoded)+1))
        buf.write(__text_encoded)
        buf.write("\0")

    def decode(data):
        if hasattr(data, 'read'):
            buf = data
        else:
            buf = StringIO.StringIO(data)
        if buf.read(8) != printf_t._get_packed_fingerprint():
            raise ValueError("Decode error")
        return printf_t._decode_one(buf)
    decode = staticmethod(decode)

    def _decode_one(buf):
        self = printf_t()
        self.utime = struct.unpack(">q", buf.read(8))[0]
        __deputy_name_len = struct.unpack('>I', buf.read(4))[0]
        self.deputy_name = buf.read(__deputy_name_len)[:-1].decode('utf-8')
        self.sheriff_id = struct.unpack(">i", buf.read(4))[0]
        __text_len = struct.unpack('>I', buf.read(4))[0]
        self.text = buf.read(__text_len)[:-1].decode('utf-8')
        return self
    _decode_one = staticmethod(_decode_one)

    _hash = None
    def _get_hash_recursive(parents):
        if printf_t in parents: return 0
        newparents = parents + [printf_t]
        tmphash = (0x855d6226c71d3dd6) & 0xffffffffffffffff
        tmphash  = (((tmphash<<1)&0xffffffffffffffff)  + (tmphash>>63)) & 0xffffffffffffffff 
        return tmphash
    _get_hash_recursive = staticmethod(_get_hash_recursive)
    _packed_fingerprint = None
    
    def _get_packed_fingerprint():
        if printf_t._packed_fingerprint is None:
            printf_t._packed_fingerprint = struct.pack(">Q", printf_t._get_hash_recursive([]))
        return printf_t._packed_fingerprint
    _get_packed_fingerprint = staticmethod(_get_packed_fingerprint)
