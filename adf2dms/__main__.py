#!/usr/bin/env python3
# dlitz 2022
from crccheck.crc import Crc16Arc
from enum import IntEnum
from io import BytesIO
from itertools import count
from pathlib import Path
from .rle import rle_compress, rle_decompress
from struct import pack, unpack
from time import time, monotonic
import os

crc16 = Crc16Arc.calc

# Ref: http://lclevy.free.fr/amiga/DMS.txt
# Ref: http://fileformats.archiveteam.org/wiki/Disk_Masher_System

class Cmode(IntEnum):
    NOCOMP  = 0     # no compression
    SIMPLE  = 1     # RLE
    #QUICK   = 2
    #MEDIUM  = 3
    #DEEP    = 4
    #HEAVY1  = 5
    #HEAVY2  = 6
    #HEAVY3  = 7
    #HEAVY4  = 8
    #HEAVY5  = 9

def pack_trackheader(tracknumber, cmode_packed_length, runtime_packed_length, unpacked_length, cflag, cmode, usum, dcrc):
    unused = 0
    th = pack("!2sHHHHHBBHH", b'TR', tracknumber, unused, cmode_packed_length,
              runtime_packed_length, unpacked_length, cflag, cmode, usum, dcrc)
    hcrc = crc16(th)
    return th + pack("!H", hcrc)

track_length = 11264

#with open("samples/3713.adf", "rb") as infile, open("out.dms", "wb") as outfile:
#    # Get file creation date
#    st = os.fstat(infile.fileno())
#    timecreate = int(st.st_mtime)
#
#    unpackedsize = st.st_size
#    assert unpackedsize % track_length == 0, (unpackedsize, divmod(unpackedsize, track_length))
#    num_tracks = unpackedsize // track_length
#
#    infobits = 0
#    lowtrack = 0
#    hightrack = num_tracks - 1
#
#    outfile.write(b"DMS!")      # IDENTIFIER
#    outfile.write(b"\0\0\0\0")  # header (?)
#    outfile.write(pack("!L", infobits))  # Infobits (?)
#    outfile.write(pack("!L", timecreate))
#    outfile.write(pack("!H", lowtrack))
#    outfile.write(pack("!H", hightrack))
#    outfile.write(pack("!L", packedsize))
#    outfile.write(pack("!L", unpackedsize))
#
#    outfile.write(pack("!I", 0))
#    outfile.write(pack("!I", 0))

def read_info_header(infile):
    magic = infile.read(4)
    if magic != b'DMS!':
        raise ValueError("not a DMS file")
    ih = infile.read(0x32)
    ihcrc = infile.read(2)
    (expected_crc,) = unpack("!H", ihcrc)
    computed_crc = crc16(ih)
    if expected_crc != computed_crc:
        raise ValueError(f"header CRC error: {expected_crc=:04X} computed: {computed_crc=:04X}")
    return magic + ih + ihcrc

time_start = monotonic()
with open("samples/3713.adf", "rb") as infile:
    total_unpacked_size = 0

    with BytesIO() as outstream:
        for track_num in count():
            unpacked_data = infile.read(track_length)
            if not unpacked_data:
                break
            assert len(unpacked_data) == track_length


            packed_data = rle_compress(unpacked_data)
            usum = crc16(unpacked_data)
            dcrc = crc16(packed_data)
            ulength = len(unpacked_data)
            plength = len(packed_data)
            if plength > ulength:
                track_header = pack_trackheader(track_num, ulength, ulength, ulength, 0, Cmode.NOCOMP, usum, usum)
                outstream.write(track_header)
                outstream.write(unpacked_data)
            else:
                track_header = pack_trackheader(track_num, plength, plength, ulength, 0, Cmode.SIMPLE, usum, dcrc)
                outstream.write(track_header)
                outstream.write(packed_data)
            total_unpacked_size += ulength

        outpayload = outstream.getvalue()
        total_packed_size = len(outpayload)

    ## Make file header

    # Get file creation date
    st = os.fstat(infile.fileno())
    date = int(st.st_mtime)

    assert total_unpacked_size % track_length == 0, (total_unpacked_size, divmod(total_unpacked_size, track_length))
    num_tracks = total_unpacked_size // track_length

    infobits = 0
    lowtrack = 0
    hightrack = num_tracks - 1

    file_header_length = 0x38

    with open("out.dms", "wb") as outfile:
        outfile.seek(file_header_length)
        outfile.write(outpayload)
        outfile.seek(0)
        outfile.flush()
        #os.fdatasync(outfile.fileno())

        time_end = monotonic()
        timecreate = int(time_end - time_start)     # seconds needed to create archive

        with BytesIO() as infohdr:
            infohdr = BytesIO()
            infohdr.write(b"\0\0\0\0")  # header (?)
            infohdr.write(pack("!L", infobits))  # Infobits (?)
            infohdr.write(pack("!L", date))
            infohdr.write(pack("!H", lowtrack))
            infohdr.write(pack("!H", hightrack))
            infohdr.write(pack("!L", total_packed_size))        # TODO
            infohdr.write(pack("!L", total_unpacked_size))

            infohdr.write(pack("!H", 0))    # OS_Version
            infohdr.write(pack("!H", 0))    # OS_REVISION
            infohdr.write(pack("!H", 4))    # MachineCPU    # XXX
            infohdr.write(pack("!H", 2))    # CPUcopro      # XXX
            infohdr.write(pack("!H", 1))    # MachineType   # XXX
            infohdr.write(pack("!H", 0))    # DisketteType2
            infohdr.write(pack("!H", 0))    # CPUmhz

            infohdr.write(pack("!L", timecreate))   # Timecreate

            infohdr.write(pack("!H", 0x70))            # VersionCreator #XXX
            infohdr.write(pack("!H", 0x6f))            # VersionNeeded     # XXX
            infohdr.write(pack("!H", 1))               # DisketteType  # XXX
            infohdr.write(pack("!H", Cmode.SIMPLE))    # CompressionMode

            ih = infohdr.getvalue()

        outfile.write(b"DMS!")      # IDENTIFIER
        outfile.write(ih)
        outfile.write(pack("!H", crc16(ih)))
        assert outfile.tell() == file_header_length, outfile.tell()
