"""MIPS recon helpers for NAGE.EXE (capstone).

usage:
  mips.py dis ADDR [COUNT]      disassemble COUNT (default 40) instructions at a RAM address
  mips.py xref ADDR             find lui/addiu|ori|lw|sw|lb.. pairs that build ADDR (+-0x10 window not included)
  mips.py words ADDR [COUNT]    dump COUNT 32-bit words (jump tables)
EXE path: work/disc/tree/NAGE.EXE (PS-X EXE; load address from its header).
"""
import struct
import sys

from capstone import CS_ARCH_MIPS, CS_MODE_LITTLE_ENDIAN, CS_MODE_MIPS32, Cs

EXE = "work/disc/tree/NAGE.EXE"


def load(path=EXE):
    d = open(path, "rb").read()
    base = struct.unpack_from("<I", d, 0x18)[0]
    return d[0x800:], base


def dis(code, base, addr, count):
    md = Cs(CS_ARCH_MIPS, CS_MODE_MIPS32 + CS_MODE_LITTLE_ENDIAN)
    off = addr - base
    for ins in md.disasm(code[off:off + count * 4], addr):
        print(f"{ins.address:08X}  {ins.mnemonic:8s} {ins.op_str}")


def xref(code, base, target):
    hi, lo = (target + 0x8000) >> 16, target & 0xFFFF
    words = struct.unpack_from(f"<{len(code) // 4}I", code)
    for i, w in enumerate(words):
        if w >> 26 == 0x0F and w & 0xFFFF == hi:  # lui rt, hi
            rt = w >> 16 & 31
            for j in range(i + 1, min(i + 24, len(words))):
                v = words[j]
                op = v >> 26
                if (v >> 21 & 31) == rt and v & 0xFFFF == lo and op in (0x09, 0x0D, 0x20, 0x21, 0x23, 0x24, 0x25,
                                                                         0x28, 0x29, 0x2B):
                    print(f"{base + i * 4:08X} lui / {base + j * 4:08X}")
                    break


LOADS = (0x09, 0x20, 0x21, 0x23, 0x24, 0x25, 0x28, 0x29, 0x2B)  # addiu, lb, lh, lw, lbu, lhu, sb, sh, sw
GP = 0x800900EC


def refs(code, base, lo, hi):
    """{RAM target in [lo, hi): [sites]} from lui+imm pairs ('lui:ADDR' = the imm instruction), $gp-relative
    accesses ('gp:ADDR') and plain 32-bit words ('word:ADDR')."""
    out = {}
    words = struct.unpack_from(f"<{len(code) // 4}I", code)
    sx = lambda v: v - 0x10000 if v & 0x8000 else v  # noqa: E731
    for i, w in enumerate(words):
        op = w >> 26
        if op == 0x0F:
            rt = w >> 16 & 31
            for j in range(i + 1, min(i + 40, len(words))):
                v = words[j]
                if (v >> 21 & 31) == rt and v >> 26 in LOADS:
                    t = ((w & 0xFFFF) << 16) + sx(v & 0xFFFF) & 0xFFFFFFFF
                    if lo <= t < hi:
                        out.setdefault(t, []).append(f"lui:{base + j * 4:08X}")
                if (v >> 16 & 31) == rt and v >> 26 in (0x0F, 0x09, 0x23):  # rt overwritten
                    break
        elif op in LOADS and (w >> 21 & 31) == 28:
            t = GP + sx(w & 0xFFFF) & 0xFFFFFFFF
            if lo <= t < hi:
                out.setdefault(t, []).append(f"gp:{base + i * 4:08X}")
        if lo <= w < hi:
            out.setdefault(w, []).append(f"word:{base + i * 4:08X}")
    return out


if __name__ == "__main__":
    cmd, a = sys.argv[1], int(sys.argv[2], 16)
    code, base = load()
    if cmd == "dis":
        dis(code, base, a, int(sys.argv[3]) if len(sys.argv) > 3 else 40)
    elif cmd == "xref":
        xref(code, base, a)
    elif cmd == "words":
        n = int(sys.argv[3]) if len(sys.argv) > 3 else 16
        for i in range(n):
            print(f"{a + 4 * i:08X}  {struct.unpack_from('<I', code, a - base + 4 * i)[0]:08X}")
