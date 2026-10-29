"""VWF hook (tools/asm/vwf.asm) run in unicorn: a string drawn glyph by glyph through the game's draw routine
0x8003C778, with LoadImage stubbed into a VRAM dict, must give the pixels font.py lays out, at every pixel shift."""
import struct
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import font  # noqa: E402
import insert  # noqa: E402

EXE = ROOT / "work/disc/tree/NAGE.EXE"
pytestmark = pytest.mark.skipif(not EXE.exists() or not insert.ARMIPS.exists(), reason="needs work/disc and armips")

DRAW, LOADIMAGE, RET, GP = 0x8003C778, 0x800750C4, 0x80000100, 0x800900EC


@pytest.fixture(scope="module")
def run():
    from unicorn import UC_ARCH_MIPS, UC_HOOK_CODE, UC_MODE_LITTLE_ENDIAN, UC_MODE_MIPS32, Uc
    from unicorn.mips_const import (UC_MIPS_REG_4, UC_MIPS_REG_5, UC_MIPS_REG_6, UC_MIPS_REG_7, UC_MIPS_REG_29,
                                    UC_MIPS_REG_2, UC_MIPS_REG_GP, UC_MIPS_REG_PC, UC_MIPS_REG_RA)
    orig = EXE.read_bytes()
    exe = bytearray(orig)
    insert.patch_exe(exe)
    base, size = struct.unpack_from("<II", exe, 0x18)
    uc = Uc(UC_ARCH_MIPS, UC_MODE_MIPS32 + UC_MODE_LITTLE_ENDIAN)
    uc.mem_map(0, 0x200000)  # kseg0 addresses are translated to physical (tools/decomp.py)
    uc.mem_write(base & 0x1FFFFFFF, bytes(exe[0x800:0x800 + size]))
    vram, calls = {}, []

    def loadimage(u, addr, *_):
        sp = u.reg_read(UC_MIPS_REG_4)
        x, y, w, h = struct.unpack("<4h", u.mem_read(sp & 0x1FFFFFFF, 8))
        data = u.mem_read(u.reg_read(UC_MIPS_REG_5) & 0x1FFFFFFF, w * h * 2)
        calls.append((x, y, w, h))
        for r in range(h):
            for c in range(w):
                vram[(x + c, y + r)] = struct.unpack_from("<H", data, (r * w + c) * 2)[0]
        u.reg_write(UC_MIPS_REG_PC, u.reg_read(UC_MIPS_REG_RA))

    uc.hook_add(UC_HOOK_CODE, loadimage, begin=LOADIMAGE, end=LOADIMAGE)
    uc.hook_add(UC_HOOK_CODE, lambda u, *_: u.emu_stop(), begin=RET, end=RET)

    def draw(glyph, x, y, colour):
        for reg, v in ((UC_MIPS_REG_4, glyph), (UC_MIPS_REG_5, x), (UC_MIPS_REG_6, y), (UC_MIPS_REG_7, colour),
                       (UC_MIPS_REG_GP, GP), (UC_MIPS_REG_29, 0x801FFF00), (UC_MIPS_REG_RA, RET)):
            uc.reg_write(reg, v)
        uc.emu_start(DRAW, RET, count=100_000)
        assert uc.reg_read(UC_MIPS_REG_PC) == RET
        return struct.unpack("<i", struct.pack("<I", uc.reg_read(UC_MIPS_REG_2)))[0]

    return draw, vram, calls, bytes(orig)


INK = 1  # vwf.asm draws each glyph 1 px right of the pen (left bearing)


def pixel(vram, x, y):
    return vram.get((0x280 + x // 4, 0x100 + y), 0) >> (x % 4 * 4) & 0xF


@pytest.mark.parametrize("x0", [0, 1, 2, 3])
def test_string_pixels(run, x0):
    draw, vram, calls, orig = run
    vram.clear()
    s, y, colour = "Wave, Mi! jumps|lazy", 20 + x0 * 16, 7
    gl = font.glyphs(orig)
    want, x = {}, x0
    for ch in s:
        rows, adv = gl[font.ascii_index(ch)]
        for r, row in enumerate(rows):
            for c, bit in enumerate(row):
                if bit:
                    want[(x + INK + c, r)] = colour
        g = 277 if ch == " " else font.ascii_index(ch)
        assert draw(g, x, y, colour) == -adv
        x += adv
    got = {(px, r): pixel(vram, px, y + r) for px in range(x0, x + INK + 4) for r in range(13)}
    assert {k: v for k, v in got.items() if v} == want
    assert all(w <= 3 and h == 13 for _, _, w, h in calls)


def test_full_width_still_16(run):
    draw, vram, calls, orig = run
    assert draw(500 + 10, 0, 100, 1) == 1  # full-width path untouched (caller adds 16)


def test_carry_not_across_rows(run):
    draw, vram, calls, orig = run
    vram.clear()
    draw(font.ascii_index("M"), 1, 60, 3)
    draw(font.ascii_index("i"), 0, 60, 3)  # new message on the same row, at/left of the last glyph: no stale merge
    assert not any(pixel(vram, px, 60 + r) for px in range(1 + INK, 4) for r in range(13))  # unit 0: 'i' only
    assert any(pixel(vram, INK, 60 + r) for r in range(13))
