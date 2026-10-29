"""Render a PS1 VRAM dump (1024x512 16-bit, from L.dump_ppu) as PNGs for recon.

usage: vram.py DUMP.vram.bin OUTPREFIX [--crop x,y,w,h]
  OUTPREFIX_16.png  15-bit colour view (VRAM words as pixels)
  OUTPREFIX_4.png   4bpp view: each word as 4 grey pixels (index*17), 4096x512; fonts and CLUT textures show here
  OUTPREFIX_8.png   8bpp view: each word as 2 grey pixels, 2048x512
--crop is in VRAM word coordinates and applies to all three views.
"""
import argparse

from PIL import Image


def load(path):
    d = open(path, "rb").read()
    # PCSX-Redux nightly 29942 getVRAM() returns 2 MB; the first 1 MB is the 1024x512 VRAM
    assert len(d) in (1 << 20, 2 << 20), len(d)
    return d[:1 << 20]


def render(d, x, y, w, h):
    rgb = Image.new("RGB", (w, h))
    g4 = Image.new("L", (w * 4, h))
    g8 = Image.new("L", (w * 2, h))
    p16, p4, p8 = rgb.load(), g4.load(), g8.load()
    for j in range(h):
        row = (y + j) * 2048
        for i in range(w):
            o = row + (x + i) * 2
            v = d[o] | d[o + 1] << 8
            p16[i, j] = ((v & 31) << 3, (v >> 5 & 31) << 3, (v >> 10 & 31) << 3)
            for k in range(4):
                p4[i * 4 + k, j] = (v >> (4 * k) & 15) * 17
            p8[i * 2, j] = d[o]
            p8[i * 2 + 1, j] = d[o + 1]
    return rgb, g4, g8


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dump")
    ap.add_argument("out")
    ap.add_argument("--crop", default="0,0,1024,512")
    a = ap.parse_args()
    x, y, w, h = map(int, a.crop.split(","))
    for name, im in zip(("16", "4", "8"), render(load(a.dump), x, y, w, h)):
        im.save(f"{a.out}_{name}.png")
