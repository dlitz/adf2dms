# dlitz 2022
from crccheck.crc import Crc16Arc as _Crc16Arc

def checksum(data):
    it = iter(data)
    result = 0
    while True:
        try:
            a = next(it)
        except StopIteration:
            break
        result = (result + a) & 0xffff
    return result

crc16 = _Crc16Arc.calc
