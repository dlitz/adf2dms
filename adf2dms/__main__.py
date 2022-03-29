#!/usr/bin/env python3
# dlitz 2022
from argparse import ArgumentParser
from io import BytesIO
from itertools import count
from pathlib import Path
from struct import pack, unpack
from time import time, monotonic
import gzip
import os
import sys

from .checksum import crc16, checksum
from .enums import Cmode, InfoBits, MachineCPU, CPUCopro, MachineType, DisketteType, SpecialTrackNum
from .rle import rle_compress, rle_decompress

# Ref: http://lclevy.free.fr/amiga/DMS.txt
# Ref: http://fileformats.archiveteam.org/wiki/Disk_Masher_System

track_length = 11264
file_header_length = 0x38

def pack_trackheader(tracknumber, cmode_packed_length, runtime_packed_length, unpacked_length, cflag, cmode, usum, dcrc):
    unused = 0
    th = pack("!2sHHHHHBBHH", b'TR', tracknumber, unused, cmode_packed_length,
              runtime_packed_length, unpacked_length, cflag, cmode, usum, dcrc)
    hcrc = crc16(th)
    return th + pack("!H", hcrc)

def pack_track(unpacked_data, track_num, *, cmode):
    usum = checksum(unpacked_data)
    ulength = len(unpacked_data)

    if cmode == Cmode.NOCOMP:
        packed_data = unpacked_data
    elif cmode == Cmode.SIMPLE:
        packed_data = rle_compress(unpacked_data)
    else:
        raise NotImplementedError(f"Compression mode: {cmode!r}")

    plength = len(packed_data)
    if plength >= ulength:
        cmode = Cmode.NOCOMP
        packed_data = unpacked_data
        plength = ulength

    dcrc = crc16(packed_data)
    track_header = pack_trackheader(track_num, plength, plength, ulength, 0, cmode, usum, dcrc)
    return track_header, packed_data

def parse_args():
    parser = ArgumentParser(description='Convert an ADF file to DMS (DiskMasher) format')
    g = parser.add_mutually_exclusive_group()
    g.add_argument('-0', '--store', action='store_true', help='store tracks uncompressed')
    parser.add_argument('-a', '--fileid', metavar='FILE', type=Path, help='attach FILE_ID.DIZ file')
    parser.add_argument('-b', '--banner', metavar='FILE', type=Path, help='attach banner file')
    parser.add_argument('-f', '--force-overwrite', action='store_true', help='overwrite output file if it already exists')
    parser.add_argument('-o', '--output', dest='outfile', metavar='file.dms', type=Path, help='DMS file to create instead of stdout')
    parser.add_argument('infile', metavar='file.adf', type=Path, help='ADF file to read')
    parser.epilog = "Input files ending in .adz or .gz will automatically be un-gzipped."

    args = parser.parse_args()
    args.cmode = Cmode.NOCOMP if args.store else Cmode.SIMPLE
    #if args.outfile is None:
    #    args.outfile = args.infile.with_suffix('.dms')
    args.gunzip = args.infile.suffix.lower() in ('.adz', '.gz')
    return args, parser

def main():
    args, parser = parse_args()

    if args.gunzip:
        infile = gzip.open(args.infile, 'rb')
    else:
        infile = open(args.infile, 'rb')
    with infile:
        if args.outfile is None:
            outfile = open(sys.stdout.fileno(), 'wb')
        else:
            outfile = open(args.outfile, 'wb' if args.force_overwrite else 'xb')
        try:
            with outfile:
                process_file(infile, outfile, args=args, parser=parser)
        except:
            # Remove output file when there is an error
            if args.outfile is not None:
                args.outfile.unlink()
            raise

def process_file(infile, outfile, *, args, parser):
    time_start = monotonic()

    # Get file creation date
    st = os.fstat(infile.fileno())
    date = int(st.st_mtime)

    total_unpacked_size = 0
    total_packed_size = 0
    num_tracks = 0

    with BytesIO() as outstream:
        for track_num in count():
            unpacked_data = infile.read(track_length)
            if not unpacked_data:
                break
            assert len(unpacked_data) == track_length

            track_header, packed_data = pack_track(unpacked_data, track_num, cmode=args.cmode)
            outstream.write(track_header)
            outstream.write(packed_data)

            total_unpacked_size += len(unpacked_data)
            total_packed_size += len(packed_data)
            num_tracks += 1

        outpayload = outstream.getvalue()

    time_end = monotonic()
    timecreate = int(time_end - time_start)  # seconds needed to create archive

    assert total_unpacked_size == num_tracks * track_length

    lowtrack = 0
    hightrack = num_tracks - 1

    ## Make file header
    header = {
        'info_bits': InfoBits(0),
        'date': date,
        'os_version': 0,
        'os_revision': 0,
        'machine_cpu': MachineCPU.M68000,
        'cpu_copro': CPUCopro.NONE,
        'machine_type': MachineType.UNKNOWN,
        'diskette_type2': DisketteType.UNKNOWN,
        'diskette_type': DisketteType.AMIGA_OS1_OFS,
        'cpu_speed': 0,     # increments of 10 kHz, e.g. 2500 = 25.00 MHz
        'time_elapsed': timecreate,
        'version_creator': 112,     # 1.12
        'version_needed': 111,      # 1.11
        'compression_mode': args.cmode,
    }

    with BytesIO() as infohdr:
        infohdr.write(b"\0\0\0\0")  # header (?)
        infohdr.write(pack("!L", header['info_bits']))
        infohdr.write(pack("!L", header['date']))
        infohdr.write(pack("!H", lowtrack))
        infohdr.write(pack("!H", hightrack))
        infohdr.write(pack("!L", total_packed_size))
        infohdr.write(pack("!L", total_unpacked_size))

        infohdr.write(pack("!H", header['os_version']))
        infohdr.write(pack("!H", header['os_revision']))
        infohdr.write(pack("!H", header['machine_cpu']))
        infohdr.write(pack("!H", header['cpu_copro']))
        infohdr.write(pack("!H", header['machine_type']))
        infohdr.write(pack("!H", header['diskette_type2']))
        infohdr.write(pack("!H", header['cpu_speed']))    # int(speed_in_mhz * 100)

        infohdr.write(pack("!L", header['time_elapsed']))   # Timecreate

        infohdr.write(pack("!H", header['version_creator']))
        infohdr.write(pack("!H", header['version_needed']))
        infohdr.write(pack("!H", header['diskette_type']))
        infohdr.write(pack("!H", header['compression_mode']))

        ih = infohdr.getvalue()

    file_header = b"DMS!" + ih + pack("!H", crc16(ih))
    assert len(file_header) == file_header_length

    if os.isatty(outfile.fileno()):
        parser.error("Cowardly refusing to write binary data to a terminal")

    outfile.write(file_header)

    if args.banner is not None:
        with open(args.banner, "rb") as txtfile:
            track_header, packed_data = pack_track(txtfile.read(), SpecialTrackNum.BANNER, cmode=Cmode.NOCOMP)
            outfile.write(track_header)
            outfile.write(packed_data)

    outfile.write(outpayload)

    if args.fileid is not None:
        with open(args.fileid, "rb") as txtfile:
            track_header, packed_data = pack_track(txtfile.read(), SpecialTrackNum.FILE_ID_DIZ, cmode=Cmode.NOCOMP)
            outfile.write(track_header)
            outfile.write(packed_data)

if __name__ == '__main__':
    main()
