"""Extract every game string from the unpacked disc into script/*.json (docs/re/text.md, docs/text-format.md).

    python -X utf8 tools/extract.py [--tree work/disc/tree] [--force]

Writes script/maps/MAPnn.json (event dialogue), script/exe.json (NAGE.EXE system text), script/records.json (club,
item and magic tables, memory-card title) and script/names.json (SYSDATA #7 name list). Existing files are left alone;
--force rewrites them but carries over every non-jp field (en, notes, status) by id, so English is never lost.
"""
import argparse
import json
import os
import struct
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import re as _stdre  # noqa: E402
import mips  # noqa: E402
import script as sc  # noqa: E402
import text  # noqa: E402
from sweep_packed import table  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TREE = ROOT / "work/disc/tree"
OUT = ROOT / "script"
EXE_BASE = 0x80010000 - 0x800  # RAM = file offset + EXE_BASE

# NAGE.EXE file ranges that hold free-standing strings (found by tools/textscan.py and a kanji-only scan of the
# whole EXE; no other run of font characters exists outside these and the tables below)
EXE_REGIONS = [(0xBE8, 0xC80), (0x13A0, 0x1458), (0x1B6C, 0x2B58), (0x809E8, 0x80C10)]
GP_AREA = 0x809E8  # file offset where the $gp data area starts: strings there sit between variables
# Non-text runs inside those ranges, by file offset (reviewed by eye; the coverage test fails if the classifier's
# data runs ever differ from this list)
EXE_DATA = {
    **dict.fromkeys([0x1D34, 0x1D5C, 0x1D95, 0x1DB4, 0x1DD4, 0x1DFC, 0x1E14, 0x1E2C, 0x1E44, 0x21DC, 0x21F4, 0x220C,
                     0x222C, 0x224C, 0x2264, 0x227C, 0x22A4, 0x22A9, 0x22BC, 0x22D0, 0x22F0, 0x2310, 0x2330, 0x2350,
                     0x2370, 0x2390, 0x23B8, 0x23D8, 0x23F8], "pointer table"),
    0x2418: "pointer table + debug printf 'not faund no. = %d'", 0x2504: "byte table",
    0x2948: "file name cdrom:\\NAGE.EXE;1", 0x809E8: "printf '%s'", 0x80C08: "memory-card file name prefix 'bu00:'",
    **dict.fromkeys([0x80A54, 0x80A58, 0x80A5C, 0x80A60, 0x80A64, 0x80A6C, 0x80A74, 0x80A76, 0x80A78, 0x80A80,
                     0x80A81, 0x80A84, 0x80B06, 0x80B75, 0x80B7D, 0x80B85, 0x80B8E, 0x80B90, 0x80BCA, 0x80BE1,
                     0x80BFD, 0x80C04], "variables ($gp area)"),
    **dict.fromkeys([0x80A9C, 0x80AA0, 0x80AB0, 0x80AD4, 0x80AD8, 0x80B14, 0x80B18, 0x80B30, 0x80B38, 0x80B40,
                     0x80B44, 0x80B48, 0x80B50, 0x80B5C, 0x80BE4, 0x80BF0, 0x80BF4],
                    "layout piece: quote+%h/%z, ???, %p, %c01:, / : spaces, newline"),
}
CTRL = _stdre.compile(r"%[hzpk]|%[ct]\d\d")
# Fixed-field tables: (name, file offset of record 0, record size, count, [(field, offset, size)])
TABLES = [
    ("CLUB", 0x7BAC4, 0x20, 11, [("name", 0, 0x20)]),
    ("ITEM", 0x7BC68, 0x47, 25, [("name", 0, 0x14), ("desc", 0x17, 0x30)]),
    ("MAGIC", 0x7C358, 0x4C, 56, [("name", 0, 0x14), ("desc", 0x1B, 0x31)]),
]
MEMCARD = (0x7DA1C, 64)  # save title shown by the BIOS memory-card manager: Shift-JIS only, 64 bytes, no NUL needed


def cstr(b, o, limit=None):
    e = b.index(b"\0", o)
    return bytes(b[o:e if limit is None else min(e, limit)])


def map_files(tree):
    return sorted(Path(tree, "MAP01_06").glob("*/MAPDAT.BIN"))


def extract_maps(tree):
    out, by_pos = {}, {}
    for path in map_files(tree):
        name = path.parent.name
        _, _, scripts = sc.scripts(path)
        rows = []
        for slot, b in scripts.items():
            for off, (raw, kind, dead) in sorted(sc.strings_of(b).items()):
                row = {"id": f"{name}/{slot}/{off:04X}", "jp": text.decode(raw), "en": ""}
                if kind == "ref":
                    row["ref"] = True
                if dead:
                    row["dead"] = True  # skipped by a goto: never shown, translated for completeness
                base = by_pos.get((name.rstrip("R"), slot, off))
                if name.endswith("R") and base and base["jp"] == row["jp"]:
                    row["same"] = base["id"]  # revisit map: same line, translate once
                by_pos.setdefault((name, slot, off), row)
                rows.append(row)
        out[name] = rows
    return out


def exe_pieces(exe):
    """[(file offset, bytes, is_text, refs)] for every NUL-free run in EXE_REGIONS, split at referenced addresses."""
    code = exe[0x800:]
    lo, hi = min(a for a, _ in EXE_REGIONS) + EXE_BASE, max(b for _, b in EXE_REGIONS) + EXE_BASE
    refs = mips.refs(code, 0x80010000, lo, hi)
    pieces = []
    for a, b in EXE_REGIONS:
        starts = {o for o in range(a, b) if exe[o] and (o == a or exe[o - 1] == 0)}
        starts |= {t - EXE_BASE for t in refs if a <= t - EXE_BASE < b and exe[t - EXE_BASE]}
        starts = sorted(starts)
        for s, nxt in zip(starts, starts[1:] + [b]):
            e = s
            while e < nxt and exe[e]:
                e += 1
            raw = bytes(exe[s:e])
            jp = text.decode(raw)
            words = CTRL.sub("", jp)
            is_text = s not in EXE_DATA and text.clean(jp) and (any(ord(c) > 0x7F for c in words) or (
                s + EXE_BASE in refs and sum(c.isalpha() for c in words) >= 2))
            pieces.append((s, raw, is_text, sorted(refs.get(s + EXE_BASE, []))))
    return pieces


def exe_room(exe, s, raw):
    """Bytes a string may use in place: its own, its NUL and, outside the $gp area, the zeros up to the next word
    boundary (alignment). Longer zero runs are not free: in the $gp area they are variables (filling them hung the
    game on its loading screen), so longer English is relocated (phase 7)."""
    e = s + len(raw) + 1
    if s < GP_AREA:
        while e % 4 and e < len(exe) and exe[e] == 0:
            e += 1
    return e - s


def extract_exe(tree):
    exe = Path(tree, "NAGE.EXE").read_bytes()
    rows = []
    for s, raw, is_text, refs in exe_pieces(exe):
        if is_text:
            rows.append({"id": f"EXE/{s:05X}", "jp": text.decode(raw), "en": "", "max": exe_room(exe, s, raw) - 1,
                         "refs": refs})
    return rows


def extract_records(tree):
    exe = Path(tree, "NAGE.EXE").read_bytes()
    rows = []
    for name, base, size, count, fields in TABLES:
        for i in range(count):
            for field, off, n in fields:
                o = base + i * size + off
                raw = cstr(exe, o, o + n)
                if raw:
                    rows.append({"id": f"{name}/{i:02d}/{field}", "jp": text.decode(raw), "en": "", "max": n - 1})
    o, n = MEMCARD
    rows.append({"id": "MEMCARD", "jp": text.decode(cstr(exe, o, o + n)), "en": "", "max": n,
                 "notes": "BIOS memory-card manager title: full-width Shift-JIS only"})
    return rows


def names_block(tree):
    d = Path(tree, "SYSDATA.BIN").read_bytes()
    t = table(d)
    return d[t[7]:t[8]]


def extract_names(tree):
    b = names_block(tree)
    end = b.index(b"\xff\xff\xff\xff")  # list ends FF FF FF FF 1A 00 00
    return [{"id": f"NAME/{i:03d}", "jp": text.decode(line), "en": ""} for i, line in enumerate(b[:end].split(b"\r\n"))]


def extract_all(tree=TREE):
    files = {f"maps/{k}.json": v for k, v in extract_maps(tree).items()}
    files["exe.json"] = extract_exe(tree)
    files["records.json"] = extract_records(tree)
    files["names.json"] = extract_names(tree)
    return files


def dump(rows):
    return json.dumps(rows, ensure_ascii=False, indent=1) + "\n"


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tree", default=str(TREE))
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    wrote = kept = 0
    for rel, rows in extract_all(a.tree).items():
        path = OUT / rel
        if path.exists():
            if not a.force:
                kept += 1
                continue
            old = {r["id"]: r for r in load(path)}
            for r in rows:
                for k, v in old.get(r["id"], {}).items():
                    if k not in ("id", "jp", "max", "refs", "dead", "same", "ref"):
                        r[k] = v
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(dump(rows), encoding="utf-8", newline="\n")
        wrote += 1
    print(f"wrote {wrote} files, kept {kept} existing (use --force to refresh jp and keep en)")


if __name__ == "__main__":
    main()
