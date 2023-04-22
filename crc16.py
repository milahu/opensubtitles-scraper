# https://stackoverflow.com/questions/35205702/calculating-crc16-in-python
# some crc16 variants in python
# expected values: https://crccalc.com/

test_data = [
  b"123456789",
]

def test(name, fn):
  for x in test_data:
    res = fn(x)
    print(f"{repr(x)} -> dec {res} = hex 0x{res:04X} # {name}")

# CRC-16/CCITT-FALSE
def crc16_ccitt_false(data : bytearray, offset , length):
    if data is None or offset < 0 or offset > len(data)- 1 and offset+length > len(data):
        return 0
    crc = 0xFFFF
    for i in range(0, length):
        crc ^= data[offset + i] << 8
        for j in range(0,8):
            if (crc & 0x8000) > 0:
                crc =(crc << 1) ^ 0x1021
            else:
                crc = crc << 1
    return crc & 0xFFFF
def wrapfn(fn):
    def wrapped(x):
        return fn(x, 0, len(x))
    return wrapped
test("CRC-16/CCITT-FALSE", wrapfn(crc16_ccitt_false))

# CRC-16/BUYPASS, CRC-16-ANSI, CRC-16-IBM
def crc16_buypass(data: bytes):
    xor_in = 0x0000  # initial value
    xor_out = 0x0000  # final XOR value
    poly = 0x8005  # generator polinom (normal form)
    reg = xor_in
    for octet in data:
        # reflect in
        for i in range(8):
            topbit = reg & 0x8000
            if octet & (0x80 >> i):
                topbit ^= 0x8000
            reg <<= 1
            if topbit:
                reg ^= poly
        reg &= 0xFFFF
        # reflect out
    return reg ^ xor_out
test("CRC-16/BUYPASS", crc16_buypass)

# https://docs.python.org/3/library/binascii.html
import binascii
def crc16_xmodem(data: bytes):
  return binascii.crc_hqx(data, 0)
test("CRC-16/XMODEM = binascii.crc_hqx", crc16_xmodem)

def crc16_modbus(data : bytearray, offset, length):
    if data is None or offset < 0 or offset > len(data) - 1 and offset + length > len(data):
        return 0
    #print("uzunluk=", len(data))
    #print(data)
    crc = 0xFFFF
    for i in range(length):
        crc ^= data[offset + i]
        for j in range(8):
            #print(crc)
            if ((crc & 0x1) == 1):
                #print("bb1=", crc)
                crc = int((crc / 2)) ^ 40961
                #print("bb2=", crc)
            else:
                crc = int(crc / 2)
    return crc & 0xFFFF
def wrapfn(fn):
    def wrapped(x):
        return fn(x, 0, len(x))
    return wrapped
test("CRC-16/MODBUS", wrapfn(crc16_modbus))

# CRC32 ...

import binascii
def crc32(data: bytes):
  return binascii.crc32(data, 0)
#test("binascii.crc32 = CRC-32", crc32)

# https://docs.python.org/3/library/zlib.html
import zlib
def crc32(data: bytes):
  return zlib.crc32(data, 0)
#test("zlib.crc32 = CRC-32", crc32)
