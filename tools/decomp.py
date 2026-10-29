"""Decompress the game's packed blocks by running its own routine (NAGE.EXE 0x80030B78, decomp(src, dst)) in unicorn.

Packed blocks start with a byte then 00 (e.g. 40 00 10 88 80 98 88 0c 02 00 f0 37 ... for a packed TIM). This is the
reference decoder for recon and for testing a Python port later; it needs only NAGE.EXE.

usage: decomp.py FILE OFFSET [OUT]     decompress the block at OFFSET, print its size, optionally write it
       decomp.py --table FILE OUTDIR   decompress every entry of a u32 offset-table file that looks packed
"""
import os
import struct
import sys

from unicorn import UC_ARCH_MIPS, UC_HOOK_CODE, UC_MODE_LITTLE_ENDIAN, UC_MODE_MIPS32, Uc
from unicorn.mips_const import UC_MIPS_REG_29, UC_MIPS_REG_4, UC_MIPS_REG_5, UC_MIPS_REG_GP, UC_MIPS_REG_RA

EXE = os.path.join(os.path.dirname(__file__), "..", "work", "disc", "tree", "NAGE.EXE")
DECOMP, GP, OUTPTR = 0x80030B78, 0x800900EC, 0x800900EC + 0x3F8
SRC, DST, RET = 0x80100000, 0x80140000, 0x80000100  # src/dst scratch areas (game data regions, not code)

_uc = None


def machine():
    global _uc
    if _uc is None:
        e = open(EXE, "rb").read()
        base, size = struct.unpack_from("<I", e, 0x18)[0], struct.unpack_from("<I", e, 0x1C)[0]
        uc = Uc(UC_ARCH_MIPS, UC_MODE_MIPS32 + UC_MODE_LITTLE_ENDIAN)
        # unicorn translates kseg0 (0x80000000) to physical for fetches and data: map RAM at 0, use P() for host I/O
        uc.mem_map(0, 0x200000)
        uc.mem_write(P(base), e[0x800:0x800 + size])
        # emu_start's until-address doesn't stop after a MIPS jr+delay slot; stop on a hook instead
        uc.hook_add(UC_HOOK_CODE, lambda u, *_: u.emu_stop(), begin=RET, end=RET)
        _uc = (uc, uc.mem_read(0, 0x200000))
    uc, snapshot = _uc
    uc.mem_write(0, bytes(snapshot))
    return uc


def P(addr):
    return addr & 0x1FFFFFFF


def decompress(data):
    uc = machine()
    uc.mem_write(P(SRC), bytes(data[:0x40000]))
    uc.reg_write(UC_MIPS_REG_4, SRC)
    uc.reg_write(UC_MIPS_REG_5, DST)
    uc.reg_write(UC_MIPS_REG_GP, GP)
    uc.reg_write(UC_MIPS_REG_29, 0x801FFF00)
    uc.reg_write(UC_MIPS_REG_RA, RET)
    uc.emu_start(DECOMP, RET, count=200_000_000)
    end = struct.unpack("<I", uc.mem_read(P(OUTPTR), 4))[0]
    return bytes(uc.mem_read(P(DST), end - DST))


def packed(block):
    return len(block) > 12 and block[1] == 0 and block[2:6] == bytes.fromhex("10888098")


if __name__ == "__main__":
    if sys.argv[1] == "--table":
        path, outdir = sys.argv[2], sys.argv[3]
        os.makedirs(outdir, exist_ok=True)
        d = open(path, "rb").read()
        n = struct.unpack_from("<I", d, 0)[0] // 4
        offs = list(struct.unpack_from(f"<{n}I", d, 0)) + [len(d)]
        for i in range(n):
            blk = d[offs[i]:offs[i + 1]]
            if packed(blk):
                out = decompress(blk)
                open(os.path.join(outdir, f"{os.path.basename(path)}.{i:03d}.bin"), "wb").write(out)
                print(i, hex(offs[i]), len(blk), "->", len(out))
    else:
        d = open(sys.argv[1], "rb").read()
        out = decompress(d[int(sys.argv[2], 0):])
        print(len(out), out[:16].hex())
        if len(sys.argv) > 3:
            open(sys.argv[3], "wb").write(out)
