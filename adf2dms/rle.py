# dlitz 2022
from struct import pack
import re

# value is 0x90:
#   0: BYTE 0x90
#   1: BYTE 0x00
# run length 1 and value is not 0x90:
#   0: BYTE <value>
# run length less than 255:
#   0: BYTE 0x90
#   1: BYTE <run_length>
#   2: BYTE <value>
# run length less than 65536:
#   0: BYTE 0x90
#   1: BYTE 0xff
#   2: BYTE <value>
#   3: WORD <run_length>

_rle_compress_regex = re.compile(rb'\x90{1,65535}|([^\x90])\1{2,65534}', re.S)

def rle_compress(inbuf):
    def replacement(m):
        value = m[0][0]
        run_length = len(m[0])
        if run_length == 1 and value == 0x90:
            return b'\x90\x00'
        elif run_length < 255:
            return bytes((0x90, run_length, value))
        else:
            return pack("!BBBH", 0x90, 0xff, value, run_length)
    return _rle_compress_regex.sub(replacement, inbuf)

_rle_decompress_regex = re.compile(rb'(\x90\x00)|\x90\xff(.)(..)|\x90([^\xff\x00])(.)', re.S)

def rle_decompress(inbuf):
    def replacement(m):
        if m[1]:
            return b'\x90'
        elif m[2]:
            value = m[2]
            a, b = m[3]
            run_length = (a << 8) | b
            return value * run_length
        elif m[4]:
            (run_length,) = m[4]
            value = m[5]
            return value * run_length
        else:
            assert 0, "BUG"
    return _rle_decompress_regex.sub(replacement, inbuf)
