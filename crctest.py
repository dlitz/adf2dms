#!/usr/bin/env python3
# dlitz 2022
from struct import pack, unpack
from crccheck.crc import identify

with open("samples/3713.dms", "rb") as infile:
    magic = infile.read(4)
    infoheader = infile.read(0x32)
    (infoheader_crc,) = unpack("!H", infile.read(2))
    print(hex(infoheader_crc))
    print(identify(infoheader, infoheader_crc))
