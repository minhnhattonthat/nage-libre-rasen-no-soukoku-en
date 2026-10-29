"""Static graphics sweep, packed part: decompress every offset-table entry that is not a raw TIM and keep the outputs
that parse as TIMs (tools/decomp.py runs the game's own decoder). Prints every skipped entry and why.

usage: sweep_packed.py TREE OUTDIR      writes OUTDIR/<file>.<entry>.png (one per unique image) + index.tsv
"""
import glob
import hashlib
import os
import struct
import sys

import decomp
import tim

# MAPDAT holds scripts and map blocks; decoding its 4 KB map blocks as "packed" runs for minutes and never yields a TIM
SKIP = ("MAPDAT", "BTLDAT", "MAPSTY", "ZOEN", "CD_SYS", "/BGM", "SE_", "SOUND", "SYSTEM.CNF", ".EXE", "SLPS")


def table(d):
    if len(d) < 8:
        return None
    h = struct.unpack_from("<I", d, 0)[0]
    if h % 4 or not 4 <= h <= 0x1000 or h > len(d):
        return None
    offs = list(struct.unpack_from(f"<{h // 4}I", d, 0))
    if offs[0] != h or any(b < a for a, b in zip(offs, offs[1:])) or offs[-1] > len(d):
        return None
    return offs + [len(d)]


if __name__ == "__main__":
    tree, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    idx = open(os.path.join(outdir, "index.tsv"), "w", encoding="utf-8", newline="\n")
    seen = {}
    for f in sorted(glob.glob(os.path.join(tree, "**", "*.*"), recursive=True)):
        if not os.path.isfile(f) or f.endswith("3MIN.BIN"):
            continue
        rel = os.path.relpath(f, tree).replace("\\", "/")
        if any(k in rel for k in SKIP):
            print("skip file (script/sound/map data, no images):", rel)
            continue
        d = open(f, "rb").read()
        offs = table(d)
        if not offs:
            print("skip file (no offset table):", rel)
            continue
        for i in range(len(offs) - 1):
            blk = d[offs[i]:offs[i + 1]]
            if len(blk) < 16 or tim.parse(blk, 0) or blk[1] != 0:
                continue  # raw TIMs are covered by tim.py; packed blocks start with "xx 00"
            try:
                out = decomp.decompress(blk)
            except Exception as e:  # noqa: BLE001 - report and go on
                print(f"skip {rel}#{i}: decoder error {e}")
                continue
            t = tim.parse(out, 0) if out else None
            if not t:
                print(f"skip {rel}#{i}: {len(blk)} -> {len(out)} bytes, not a TIM ({out[:8].hex()})")
                continue
            key = hashlib.sha1(t["pix"]).hexdigest()[:12]
            desc = f"{rel}\t{i}\t{offs[i]:#x}\t{t['bpp']}bpp\t{t['w']}x{t['h']}"
            if key in seen:
                idx.write(f"{desc}\tdup {seen[key]}\n")
                continue
            name = f"p{len(seen):04d}.png"
            seen[key] = name
            tim.to_image(t).save(os.path.join(outdir, name))
            idx.write(f"{desc}\t{name}\n")
    print(len(seen), "unique packed TIMs")
