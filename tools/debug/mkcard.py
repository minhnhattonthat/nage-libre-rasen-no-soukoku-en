"""Write a formatted, empty PS1 memory card image (128 KiB raw .mcd)."""
import sys


def frame(b):
    b = bytearray(b.ljust(128, b"\0"))
    x = 0
    for c in b[:127]:
        x ^= c
    b[127] = x
    return bytes(b)


blk0 = [frame(b"MC")]
blk0 += [frame(b"\xa0\0\0\0" + b"\0" * 4 + b"\xff\xff") for _ in range(15)]           # free directory entries
blk0 += [frame(b"\xff\xff\xff\xff" + b"\0" * 4 + b"\xff\xff") for _ in range(20)]     # broken-sector list: none
blk0 += [frame(b"\xff\xff\xff\xff" + b"\0" * 4 + b"\xff\xff") for _ in range(27)]     # replacement frames
blk0 += [frame(b"MC")]                                                              # write-test frame
assert len(blk0) == 64
card = b"".join(blk0) + bytes(128 * 1024 - 64 * 128)
open(sys.argv[1], "wb").write(card)
