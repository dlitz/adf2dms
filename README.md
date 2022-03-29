# adf2dms
Convert Amiga disk images from ADF to DMS (DiskMasher) format

## Note: Experimental software

This code is experiental and currently only implements the uncompressed
("NOCOMP") and RLE ("SIMPLE") compression modes.

## Usage

```
$ python3 -m adf2dms --help
usage: adf2dms [-h] [-0] [-a FILE] [-b FILE] [-f] [-o file.dms] [-s TRKNUM] [-e TRKNUM | -n COUNT] file.adf

Convert an ADF file to DMS (DiskMasher) format

positional arguments:
  file.adf              ADF file to read

optional arguments:
  -h, --help            show this help message and exit
  -0, --store           store tracks uncompressed
  -a FILE, --fileid FILE
                        attach FILE_ID.DIZ file
  -b FILE, --banner FILE
                        attach banner file
  -f, --force-overwrite
                        overwrite output file if it already exists
  -o file.dms, --output file.dms
                        DMS file to create instead of stdout
  -s TRKNUM, --low-track TRKNUM
                        first track, default: 0
  -e TRKNUM, --high-track TRKNUM
                        last track, default: determined by file length
  -n COUNT, --num-tracks COUNT
                        number of tracks to add, default: determined by file length

Input files ending in .adz or .gz will automatically be un-gzipped.
```

## Building adf2dms

```
git clone https://github.com/dlitz/adf2dms
python3 -m build adf2dms
```
