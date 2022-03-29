from enum import IntEnum, IntFlag

# Ref: http://fileformats.archiveteam.org/wiki/Disk_Masher_System
# Ref: http://lclevy.free.fr/amiga/DMS.txt

class Cmode(IntEnum):
    """Compression mode"""
    NOCOMP  = 0     # no compression
    SIMPLE  = 1     # RLE
    QUICK   = 2
    MEDIUM  = 3
    DEEP    = 4
    HEAVY1  = 5
    HEAVY2  = 6
    HEAVY3  = 7
    HEAVY4  = 8
    HEAVY5  = 9

class InfoBits(IntFlag):
    NOZERO          = 1
    ENCRYPT         = 2
    APPENDS         = 4
    BANNER          = 8
    HIGHDENSITY     = 16
    PC              = 32
    DMS_DEVICE_FIX  = 64
    FILE_ID_DIZ     = 256

class MachineCPU(IntEnum):
    M68000      = 0
    M68010      = 1
    M68020      = 2
    M68030      = 3
    M68040      = 4
    M68060      = 5
    I8086       = 6
    I8088       = 7
    I80188      = 8
    I80186      = 9
    I80286      = 10
    I80386SX    = 11
    I80386      = 12
    I80486      = 13
    I80586      = 14

class CPUCopro(IntEnum):
    NONE        = 0
    M68881      = 1
    M68882      = 2
    I8087       = 3
    I80287SX    = 4
    I80387      = 5

class MachineType(IntEnum):
    UNKNOWN	= 0
    AMIGA	= 1
    PC_CLONE	= 2
    ATARI	= 3
    MACINTOSH	= 4

class DisketteType(IntEnum):
    UNKNOWN                     = 0
    AMIGA_OS1_OFS               = 1
    AMIGA_OS1_FFS               = 2
    AMIGA_OS3_INTERNATIONAL     = 3
    AMIGA_OS3_FFS_INTERNATIONAL = 4
    AMIGA_OS3_DIRCACHE          = 5
    AMIGA_OS3_FFS_DIRCACHE      = 6
    File_Masher_System          = 7

# OS Version
AMIGA_AGA_COMPUTER = 0x8000

class SpecialTrackNum(IntEnum):
    FILE_ID_DIZ                 = 80
    BANNER                      = 0xffff
