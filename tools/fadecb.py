"""List every function NAGE.EXE queues as the fade-out callback ($gp+0xB74, docs/re/state.md).

usage: python tools/fadecb.py
Finds `jal 0x80043CD4|0x80043CE8` (the two setters) and the lui/addiu pair that built $a0 just before it.
"""
import struct

SETTERS = (0x80043CD4, 0x80043CE8)


def load(path="work/disc/tree/NAGE.EXE"):  # same as tools/mips.py load()
    d = open(path, "rb").read()
    return d[0x800:], struct.unpack_from("<I", d, 0x18)[0]


def main():
    code, base = load()
    words = struct.unpack_from(f"<{len(code) // 4}I", code)
    for i, w in enumerate(words):
        if w >> 26 != 3 or ((w & 0x3FFFFFF) << 2 | (base + i * 4) & 0xF0000000) not in SETTERS:
            continue
        hi = lo = None
        for j in range(i + 1, max(i - 12, 0), -1):  # delay slot first, then backwards
            v = words[j]
            rt, rs, op = v >> 16 & 31, v >> 21 & 31, v >> 26
            if op == 0x09 and rt == 4 and rs == 4 and lo is None:  # addiu a0, a0, lo
                lo = v & 0xFFFF
            elif op == 0x0F and rt == 4 and hi is None:  # lui a0, hi
                hi = v & 0xFFFF
        tgt = None if hi is None else ((hi << 16) + (lo - 0x10000 if lo and lo >= 0x8000 else lo or 0)) & 0xFFFFFFFF
        setter = (w & 0x3FFFFFF) << 2 | 0x80000000
        print(f"{base + i * 4:08X}  {setter:08X}  a0={tgt:08X}" if tgt and tgt >> 28 == 8 else
              f"{base + i * 4:08X}  {setter:08X}  a0=? (not a lui/addiu pair)")


if __name__ == "__main__":
    main()
