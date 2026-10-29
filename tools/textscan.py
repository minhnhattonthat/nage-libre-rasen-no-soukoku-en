"""Find game text in the unpacked disc: NUL-terminated Shift-JIS runs whose characters are all in the game font.

The font charset is SYSDATA.BIN section 4 (docs/re/text.md). A run may also hold ASCII '%h'/'%z' codes, '\\n' (0x0A),
CRLF and half-width katakana. Runs shorter than --min font characters are dropped, which filters out graphics noise.

usage: textscan.py TREE [--min 3] [--files GLOB] [--summary] [--tsv OUT]
"""
import argparse
import glob
import os
import struct


def charset(tree):
    d = open(os.path.join(tree, "SYSDATA.BIN"), "rb").read()
    a, b = struct.unpack_from("<2I", d, 4 * 4)
    return {d[i:i + 2] for i in range(a, b, 2)} | {"　".encode("cp932")}


def is_text(raw):
    """At least half the characters are kana or kanji (TIM colour words decode as symbols and Latin), and at least one
    is full-width kana (kanji-only runs are graphics noise)."""
    s = raw.decode("cp932", "replace")
    jp = sum(1 for c in s if "぀" <= c <= "ヿ" or "一" <= c <= "鿿" or "ｦ" <= c <= "ﾟ")
    full = sum(1 for c in s if ord(c) > 0x7f)
    return jp * 2 >= full and any("ぁ" <= c <= "ヾ" for c in s)


def scan(data, cs, minchars):
    """Yield (offset, raw bytes) for each text run."""
    i, n = 0, len(data)
    while i < n:
        j, chars = i, 0
        while j < n:
            c = data[j]
            if c >= 0x81 and j + 1 < n and data[j:j + 2] in cs:
                j += 2
                chars += 1
            elif c == 0x25 and j + 1 < n and data[j + 1] in b"hz":
                j += 2
            elif c in (0x0A, 0x0D) or 0xA1 <= c <= 0xDF or 0x20 <= c < 0x7F and chars:
                j += 1
            else:
                break
        if chars >= minchars and j < n and data[j] == 0 and is_text(data[i:j]):
            yield i, data[i:j]
            i = j
        else:
            i += 1 if j == i else (j - i)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("tree")
    ap.add_argument("--min", type=int, default=3)
    ap.add_argument("--files", default="**/*.*")
    ap.add_argument("--summary", action="store_true", help="one line per file: runs, bytes")
    ap.add_argument("--tsv", help="write file, offset, text rows")
    a = ap.parse_args()
    cs = charset(a.tree)
    out = open(a.tsv, "w", encoding="utf-8", newline="\n") if a.tsv else None
    for f in sorted(glob.glob(os.path.join(a.tree, a.files), recursive=True)):
        if not os.path.isfile(f) or os.path.getsize(f) > 4 << 20:
            continue
        rel = os.path.relpath(f, a.tree).replace("\\", "/")
        runs = list(scan(open(f, "rb").read(), cs, a.min))
        if not runs:
            continue
        if a.summary:
            print(f"{len(runs):6d} {sum(len(r) for _, r in runs):8d}  {rel}")
        for off, raw in runs:
            text = raw.decode("cp932", "replace").replace("\r\n", "\\r\\n").replace("\n", "\\n")
            if out:
                out.write(f"{rel}\t{off:#x}\t{text}\n")
            elif not a.summary:
                print(f"{rel}\t{off:#x}\t{text}")
