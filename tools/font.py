"""English VWF font: the game's own half-width ASCII glyphs (NAGE.EXE 0x80089B5C, 8x13, 1bpp), trimmed to their ink
and given per-glyph advances (docs/re/vwf.md).

    python -X utf8 tools/font.py [--png work/qa/vwf_font.png]   preview sheet + width list

Glyph index = position in the SYSDATA #5 single-byte table, which the game's lookup (0x8003F26C) returns: ASCII
0x21-0x7D -> 0-92, '~' -> 94, space -> 277. The VWF keeps glyphs 0-95 at the original address (rows re-encoded
LSB = leftmost pixel); 95 is a box for any other index (Japanese left in an English line), space draws index 93.
"""
import argparse
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

EXE_BASE = 0x80010000 - 0x800
FONT = 0x80089B5C          # original half-width font, 13 bytes per glyph
WIDTH = 0x8008A03C         # 96 advances (bytes), right after glyph 95
COUNT = 96
SPACE, MISSING = 93, 95    # glyph slots the VWF code maps index 277 / indices >= 96 to
SPACE_ADV = 4
ROWS = 13
# trimmed ink widths that look too tight/loose with a plain 1-px gap: extra advance in px
EXTRA = {}


def ascii_index(ch):
    """Glyph index the game's lookup returns for an ASCII character."""
    if ch == " ":
        return SPACE
    if ch == "~":
        return 94
    c = ord(ch)
    if not 0x21 <= c <= 0x7D:
        raise ValueError(f"no glyph for {ch!r}")
    return c - 0x21


def original(exe, g):
    """13 rows of 7 pixels (the game draws bits 7..1 of each byte; bit 0 is never shown)."""
    o = FONT - EXE_BASE + g * ROWS
    return [[(exe[o + r] >> (7 - c)) & 1 for c in range(7)] for r in range(ROWS)]


def glyphs(exe):
    """[(rows as pixel lists, advance)] for the 96 VWF slots."""
    out = []
    for g in range(COUNT):
        if g == SPACE:
            out.append(([[0] * 7 for _ in range(ROWS)], SPACE_ADV))
            continue
        if g == MISSING:
            box = [[1] * 5] + [[1, 0, 0, 0, 1] for _ in range(9)] + [[1] * 5] + [[0] * 5] * 2
            out.append((box, 6))
            continue
        px = original(exe, g)
        cols = [c for c in range(7) if any(r[c] for r in px)]
        if not cols:
            out.append((px, SPACE_ADV))
            continue
        lo, hi = cols[0], cols[-1]
        rows = [r[lo:hi + 1] for r in px]
        out.append((rows, hi - lo + 2 + EXTRA.get(g, 0)))
    return out


_widths = None
CTRL = re.compile(r"%[hzpk]|%[ct]\d\d")


def advance(text, exe=None):
    """Pixel width of an ASCII string in the VWF (control codes take no width)."""
    global _widths
    if _widths is None or exe is not None:
        exe = exe or open(Path(__file__).resolve().parents[1] / "work/disc/tree/NAGE.EXE", "rb").read()
        _widths = [a for _, a in glyphs(exe)]
    return sum(_widths[ascii_index(c)] for c in CTRL.sub("", text))


def wrap(text, width):
    """Greedy word wrap to `width` px; explicit newlines are kept. Returns the lines (a word wider than the box
    stays on its own line: the lint reports it)."""
    out = []
    for para in text.split("\n"):
        line = ""
        for word in para.split(" "):
            cand = f"{line} {word}" if line else word
            if line and advance(cand) > width:
                out.append(line)
                line = word
            else:
                line = cand
        out.append(line)
    return out


def balanced_wrap(text, width):
    """wrap() per paragraph at the narrowest width that keeps its line count, so the last line isn't a one-word
    widow ("...get them back for" / "you.")."""
    out = []
    for para in text.split("\n"):
        n, lo, hi = len(wrap(para, width)), 1, width
        while lo < hi:  # smallest width with the same number of lines
            mid = (lo + hi) // 2
            lo, hi = (lo, mid) if len(wrap(para, mid)) <= n else (mid + 1, hi)
        out += wrap(para, lo)
    return out


def encode(exe):
    """(font bytes for slots 0-95, width bytes): rows LSB = leftmost pixel."""
    font, width = bytearray(), bytearray()
    for rows, adv in glyphs(exe):
        assert 1 <= adv <= 9 and all(len(r) <= 8 for r in rows), "VWF glyphs: ink <= 8 px, advance <= 9"
        for r in rows:
            font.append(sum(bit << c for c, bit in enumerate(r)))
        width.append(adv)
    assert len(font) == COUNT * ROWS and FONT + len(font) == WIDTH
    return bytes(font), bytes(width)


def apply(exe):
    """Write the VWF font and width table into a NAGE.EXE bytearray."""
    font, width = encode(exe)
    exe[FONT - EXE_BASE:FONT - EXE_BASE + len(font)] = font
    exe[WIDTH - EXE_BASE:WIDTH - EXE_BASE + len(width)] = width


def preview(exe, path, text=None):
    from PIL import Image
    gl = glyphs(exe)
    text = text or "".join(chr(0x21 + i) for i in range(93)) + "~ The quick brown fox jumps over the lazy dog."
    w = sum(gl[ascii_index(c)][1] for c in text)
    img = Image.new("L", (w + 4, ROWS + 4), 30)
    x = 2
    for c in text:
        rows, adv = gl[ascii_index(c)]
        for y, r in enumerate(rows):
            for cx, bit in enumerate(r):
                if bit:
                    img.putpixel((x + cx, y + 2), 255)
        x += adv
    img.resize((img.width * 4, img.height * 4), Image.NEAREST).save(path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", default="work/disc/tree/NAGE.EXE")
    ap.add_argument("--png", default="work/qa/vwf_font.png")
    ap.add_argument("--text")
    a = ap.parse_args()
    exe = open(a.exe, "rb").read()
    preview(exe, a.png, a.text)
    print(" ".join(f"{chr(0x21 + i) if i < 93 else i}:{adv}" for i, (_, adv) in enumerate(glyphs(exe))))
