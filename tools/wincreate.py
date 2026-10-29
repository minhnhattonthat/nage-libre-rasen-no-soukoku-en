"""List every call to the window create 0x8003DB60(x, y, w, h, ...) with the constant args set before it
(docs/re/vwf.md §Fields; the budgets in boxes.FIELDS).

    python -X utf8 tools/wincreate.py
None = the arg comes from a register (computed).
"""
import struct

import mips

CREATE = 0x8003DB60
REG = {4: "a0", 5: "a1", 6: "a2", 7: "a3"}


def creates(code, base):
    """[(call address, {a0..a3: constant or None})]."""
    w = struct.unpack_from(f"<{len(code) // 4}I", code)
    out = []
    for i, x in enumerate(w):
        if x >> 26 != 3 or ((x & 0x3FFFFFF) << 2 | 0x80000000) != CREATE:
            continue
        args = {}
        for j in range(i + 1, i - 16, -1):  # delay slot first, then back to the previous call
            v = w[j]
            op, rs, rt, imm = v >> 26, v >> 21 & 31, v >> 16 & 31, v & 0xFFFF
            if op in (0x09, 0x0D) and rs == 0 and rt in REG and REG[rt] not in args:
                args[REG[rt]] = imm - 0x10000 if imm & 0x8000 and op == 9 else imm
            if j < i and op in (2, 3):
                break
        out.append((base + i * 4, {k: args.get(k) for k in REG.values()}))
    return out


if __name__ == "__main__":
    for addr, a in creates(*mips.load()):
        print(f"{addr:08X}  x {a['a0']}  y {a['a1']}  w {a['a2']}  h {a['a3']}")
