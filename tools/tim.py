"""Find and render PS1 TIM images inside the unpacked disc files.

usage: tim.py scan TREE [--files GLOB]              list valid TIMs: file, offset, bpp, w x h, clut count
       tim.py render TREE OUTDIR [--files GLOB]      write one PNG per unique TIM (dedup by pixel hash) + index.tsv
A TIM is: u32 0x10, u32 flags (bpp 0-3, bit 3 = has CLUT), [CLUT block], image block; each block is
u32 length, u16 x, y, w, h, data. Width in the image block is in 16-bit words.
"""
import argparse
import glob
import hashlib
import os
import struct

from PIL import Image

BPP = {0: 4, 1: 8, 2: 16, 3: 24}


def parse(d, off):
    """Return a dict for a valid TIM at off, else None."""
    if off + 20 > len(d) or struct.unpack_from("<I", d, off)[0] != 0x10:
        return None
    flags = struct.unpack_from("<I", d, off + 4)[0]
    if flags & ~0xB or (flags & 3) == 3:
        return None
    p, clut = off + 8, None
    if flags & 8:
        ln, cx, cy, cw, ch = struct.unpack_from("<I4H", d, p)
        if ln != 12 + cw * ch * 2 or not 0 < cw <= 256 or not 0 < ch <= 512 or p + ln > len(d):
            return None
        clut = (cw, ch, d[p + 12:p + ln])
        p += ln
    elif flags & 3 < 2:
        return None
    if p + 12 > len(d):
        return None
    ln, x, y, w, h = struct.unpack_from("<I4H", d, p)
    if ln != 12 + w * h * 2 or not 0 < w <= 1024 or not 0 < h <= 512 or p + ln > len(d):
        return None
    return dict(off=off, end=p + ln, bpp=BPP[flags & 3], w=w, h=h, x=x, y=y, clut=clut, pix=d[p + 12:p + ln])


def rgb(c):
    return ((c & 31) << 3, (c >> 5 & 31) << 3, (c >> 10 & 31) << 3, 0 if c == 0 else 255)


def to_image(t, pal=0):
    bpp, w, pix = t["bpp"], t["w"], t["pix"]
    if bpp == 16:
        pw = w
        cols = [rgb(struct.unpack_from("<H", pix, i)[0]) for i in range(0, len(pix), 2)]
    else:
        cw, ch, cd = t["clut"]
        pal = min(pal, ch - 1)
        table = [rgb(struct.unpack_from("<H", cd, (pal * cw + i) * 2)[0]) for i in range(cw)]
        if bpp == 4:
            pw = w * 4
            idx = [b >> s & 15 for b in pix for s in (0, 4)]
        else:
            pw = w * 2
            idx = list(pix)
        cols = [table[i] if i < len(table) else (255, 0, 255, 255) for i in idx]
    im = Image.new("RGBA", (pw, t["h"]))
    im.putdata(cols[:pw * t["h"]])
    return im


def scan(path):
    d = open(path, "rb").read()
    i, out = 0, []
    while True:
        i = d.find(b"\x10\x00\x00\x00", i)
        if i < 0:
            return out
        t = parse(d, i)
        if t:
            out.append(t)
            i = t["end"]
        else:
            i += 1


def files(tree, pattern):
    return [f for f in sorted(glob.glob(os.path.join(tree, pattern), recursive=True))
            if os.path.isfile(f) and not f.endswith("3MIN.BIN")]


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=("scan", "render"))
    ap.add_argument("tree")
    ap.add_argument("outdir", nargs="?")
    ap.add_argument("--files", default="**/*.*")
    a = ap.parse_args()
    seen = {}
    if a.cmd == "render":
        os.makedirs(a.outdir, exist_ok=True)
        idx = open(os.path.join(a.outdir, "index.tsv"), "w", encoding="utf-8", newline="\n")
    for f in files(a.tree, a.files):
        rel = os.path.relpath(f, a.tree).replace("\\", "/")
        for t in scan(f):
            desc = f"{rel}\t{t['off']:#x}\t{t['bpp']}bpp\t{t['w']}x{t['h']}\tvram {t['x']},{t['y']}"
            if a.cmd == "scan":
                print(desc)
                continue
            key = hashlib.sha1(t["pix"]).hexdigest()[:12]
            if key in seen:
                idx.write(f"{desc}\tdup {seen[key]}\n")
                continue
            name = f"{len(seen):05d}.png"
            seen[key] = name
            to_image(t).save(os.path.join(a.outdir, name))
            idx.write(f"{desc}\t{name}\n")
    if a.cmd == "render":
        print(len(seen), "unique TIMs ->", a.outdir)
