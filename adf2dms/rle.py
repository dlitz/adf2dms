# dlitz 2022
from struct import pack

def _rle_decompress(inp):
    # RLE marker is 90 FF
    it = iter(inp)
    for a in it:
        if a != 0x90:
            yield a
            continue

        try:
            b = next(it)
        except StopIteration:
            yield a
            break

        if b != 0xff:
            yield a
            yield b
            continue

        # Got 90 FF.  Next 3 bytes are: value, run_length
        try:
            v = next(it)
            c = next(it)
            d = next(it)
        except StopIteration:
            raise EOFError
        run_length = (c << 8) | d

        yield from [v] * run_length

RLE_ESCAPE = object()   # sentinel

def _rle_escape(inp):
    it = iter(inp)
    for a in it:
        if a != 0x90:
            yield a
            continue
        try:
            b = next(it)
        except StopIteration:
            yield a
            break
        if b != 0xff:
            yield a
            yield b
            continue
        yield RLE_ESCAPE

def _rle_counts(inp):
    it = iter(inp)
    prev = None
    prev_count = 0
    def flush():
        nonlocal prev, prev_count
        if prev_count:
            yield (prev, prev_count)
            prev = None
            prev_count = 0
    for a in it:
        if a is RLE_ESCAPE:
            yield from flush()
            yield (RLE_ESCAPE, 1)
        elif a == prev:
            prev_count += 1
        else:
            yield from flush()
            prev = a
            prev_count = 1
    yield from flush()

def _rle_compress(inp):
    it = iter(_rle_counts(_rle_escape(inp)))
    for a, n in it:
        if a is RLE_ESCAPE:
            assert n == 1
            yield from pack("!HBH", 0x90ff, 0x90, 1)
            yield 0xff
        elif n < 6:
            yield from [a] * n
        else:
            yield from pack("!HBH", 0x90ff, a, n)

def rle_compress(buf):
    return bytes(_rle_compress(buf))

def rle_decompress(buf):
    return bytes(_rle_decompress(buf))
