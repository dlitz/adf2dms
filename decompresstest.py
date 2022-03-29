#!/usr/bin/env python
# dlitz 2022
from adf2dms.rle import rle_decompress, rle_compress
from adf2dms.checksum import crc16, checksum
from collections import namedtuple
from struct import unpack

track_length = 11264

TrackHeader = namedtuple('TrackHeader', 'HeaderID1 Tracknumber UNUSED CMODE_Packed RuntimePacked Unpacklength Cflag_ CmodeTrk Usum_ Dcrc_ Hcrc_')

def read_file_header(infile):
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


def unpack_trackheader(data):
    return TrackHeader(*unpack("!2sHHHHHBBHHH", data))

def main():

    with open("samples/3713.dms", "rb") as infile, open("out.adf", "wb") as outfile:
        #infoheader = infile.read(0x38)
        #assert crc16(infoheader[4:-2]) == unpack("!H", infoheader[-2:])[0]
        infoheader = read_file_header(infile)

        while True:
            track_header_raw = infile.read(0x14)
            if not track_header_raw:
                break
            track_header = unpack_trackheader(track_header_raw)
            print(track_header)
            assert crc16(track_header_raw[:-2]) == track_header.Hcrc_
            packed_data = infile.read(track_header.CMODE_Packed)
            assert crc16(packed_data) == track_header.Dcrc_
            if track_header.CmodeTrk == 0:      # NOCOMP - no compression
                unpacked_data = packed_data
            elif track_header.CmodeTrk == 1:    # SIMPLE - RLE
                unpacked_data = rle_decompress(packed_data)
            else:
                raise NotImplementedError(trackheader.CmodeTrk)
            outfile.write(unpacked_data)
            #assert track_header.Unpacklength == track_length, (track_header.Unpacklength, track_length)
            assert len(unpacked_data) == track_header.Unpacklength, (len(unpacked_data), track_header.Unpacklength)
            assert checksum(unpacked_data) == track_header.Usum_, (hex(checksum(unpacked_data)), hex(track_header.Usum_))

if __name__ == '__main__':
    main()
