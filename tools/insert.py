"""Insert script/ text into copies of the game files (docs/text-format.md, docs/re/text.md).

    python -X utf8 tools/insert.py [--markers] [--out work/build/files]

Reads the untouched unpacked tree (work/disc/tree, never written) and writes every changed file under --out at its
disc path. Rows with `en` are inserted; with --markers every row gets `[id] marker text` instead (phase 5 marker
build). build.py calls build_files() and points mkpsxiso at the results.
"""
import argparse
import json
import os
import struct
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import boxes  # noqa: E402
import extract  # noqa: E402
import font  # noqa: E402
import script as sc  # noqa: E402
import text  # noqa: E402
from sweep_packed import table  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "script"
ARMIPS = ROOT / "tools/armips/armips.exe"
ASM = [ROOT / "tools/asm/vwf.asm"]
MAPDAT_MAX = 0x801FFF00 - 0x80170000  # loaded at 0x80170000, stack below 0x801FFF00 (docs/re/files.md)
# SYSDATA's buffer: memory-area table at 0x80089798 = {0x80130000, 0xC000}; the original file is 47,289 bytes, so the
# whole names block may grow by ~1.8 KB. Over it, New Game hangs on its loading screen (10-byte name markers did).
SYSDATA_MAX = 0xC000
NAME_ROOM = 6  # marker length for SYSDATA names: 696 names x 8 bytes stays inside SYSDATA_MAX
FILLER ="The quick brown fox jumps over the lazy dog. Pack my box with five dozen liquor jugs."


def marker(rid, room=None, box=None):
    """Marker text for a row: its short id plus filler, cut to `room` bytes for fixed fields, or filling a dialogue
    box = (width px, lines) to its last line."""
    if room is not None:  # E00BE8MMM, I03descMMM, N123: id, then wide glyphs to the field's bytes (shows clipping)
        return (rid[0] + rid.split("/", 1)[-1].replace("/", "")).ljust(room, "M")[:room]
    s = f"[{rid.replace('MAP', '').replace('/', '.')}]"
    if box is None:
        return f"{s} {FILLER}"[:56]
    width, lines = box
    words = (FILLER + " ") * 4
    for w in words.split():  # fill the box to its last line, never past it
        if len(font.wrap(f"{s} {w}", width)) > lines:
            break
        s = f"{s} {w}"
    return s


def encode(s):
    """English (or kept Japanese) text -> game bytes. ASCII draws from the half-width font."""
    return text.encode(s)


QA = {}  # id -> text overriding marker/en for one build (build.py --qa ID=text): stress lines, torture line
SKIPPED = []  # EXE rows whose English is over the in-place room: Japanese kept (build.py prints them)


def row_text(row, markers, room=None, box=None):
    """New bytes for a row, or None to keep the original. box = (width px, lines): wrap to that width."""
    if row["id"] in QA:
        s = fit_field(row["id"], QA[row["id"]])
    elif markers:
        if row["id"] == "MEMCARD":
            return None  # BIOS card manager: full-width SJIS only
        s = marker(row["id"], room, box)
    elif row.get("en"):
        s = fit_field(row["id"], row["en"])
    else:
        return None
    if box:
        s = paginate(font.wrap(s, box[0]), box[1])
    return encode(s)


def fit_field(rid, s):
    """English for a menu/label row laid out for its field (boxes.FIELDS): a trailing \\n for menu items that ended
    by auto-wrap, word wrap for multi-line windows."""
    how, f = boxes.fit(rid), boxes.field(rid)
    if how == "nl" and not s.endswith("\n"):
        return s + "\n"
    if how == "wrap" and f and f[1] > 1:
        return "\n".join(font.wrap(s, f[0] - boxes.MARGIN))
    return s


def paginate(lines, per_page):
    """Join wrapped lines; past a full box, `%k%p` waits for the button (the arrow op 14 shows) and clears the box,
    so long English pages inside one message (docs/re/vwf.md §Paging)."""
    return PAGE.join("\n".join(lines[i:i + per_page]) for i in range(0, len(lines), per_page))


PAGE = "%k%p"


def load_rows(name):
    return json.loads((SCRIPT / name).read_text(encoding="utf-8"))


def build_maps(tree, markers):
    out = {}
    for path in extract.map_files(tree):
        name = path.parent.name
        rows = {r["id"]: r for r in load_rows(f"maps/{name}.json")}
        if not markers:  # revisit lines take their base line's English
            for r in rows.values():
                if r.get("same") and not r.get("en"):
                    base = load_rows(f"maps/{r['same'].split('/')[0]}.json")
                    r["en"] = next(b["en"] for b in base if b["id"] == r["same"])
        d, _, scripts = sc.scripts(path)
        new = {}
        for slot, b in scripts.items():
            texts, box = {}, boxes.classify(name, b)
            for off in sc.strings_of(b):
                t = row_text(rows[f"{name}/{slot}/{off:04X}"], markers, box=boxes.budget(box[off]))
                if t is not None:
                    texts[off] = t
            if texts:
                new[slot] = sc.rebuild(b, texts)
        if new:
            data = sc.rebuild_mapdat(d, new)
            if len(data) > MAPDAT_MAX:
                raise ValueError(f"{name}/MAPDAT.BIN is {len(data)} bytes, over the RAM limit {MAPDAT_MAX}")
            out[path.relative_to(tree).as_posix()] = data
    return out


def put(buf, o, raw, room, rid):
    """Write raw + NUL at o, zero-filling the rest of a `room`-byte field (room excludes the NUL)."""
    if len(raw) > room:
        raise ValueError(f"{rid}: {len(raw)} bytes, field holds {room}")
    buf[o:o + room + 1] = raw + bytes(room + 1 - len(raw))


def patch_exe(exe):
    """Engine changes: VWF font data (font.py) and code (tools/asm/vwf.asm, armips)."""
    font.apply(exe)
    tmp = ROOT / "work/build/asm/NAGE.EXE"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_bytes(exe)
    for asm in ASM:
        subprocess.run([str(ARMIPS), str(asm), "-strequ", "EXE", str(tmp)], check=True, cwd=ROOT)
    exe[:] = tmp.read_bytes()


def build_exe(tree, markers):
    exe = bytearray(Path(tree, "NAGE.EXE").read_bytes())
    orig = bytes(exe)
    patch_exe(exe)
    for r in load_rows("exe.json"):
        t = row_text(r, markers, r["max"])
        if t is not None and len(t) > r["max"]:  # shortcut: kept Japanese until phase 7 relocates long strings
            SKIPPED.append(r["id"])
        elif t is not None:
            put(exe, int(r["id"].split("/")[1], 16), t, r["max"], r["id"])
    tables = {name: (base, size, {f: off for f, off, _ in fields}) for name, base, size, _, fields in extract.TABLES}
    for r in load_rows("records.json"):
        t = row_text(r, markers, r["max"])
        if t is None:
            continue
        if r["id"] == "MEMCARD":
            o, n = extract.MEMCARD
            exe[o:o + n] = t.ljust(n, b"\0")[:n]
            continue
        name, i, field = r["id"].split("/")
        base, size, offs = tables[name]
        # only the string and its NUL: the bytes after it in the field may be flags (docs/re/text.md)
        o = base + int(i) * size + offs[field]
        if len(t) > r["max"]:
            raise ValueError(f"{r['id']}: {len(t)} bytes, field holds {r['max']}")
        exe[o:o + len(t) + 1] = t + b"\0"
    return {"NAGE.EXE": bytes(exe)} if exe != orig else {}


def build_names(tree, markers):
    d = Path(tree, "SYSDATA.BIN").read_bytes()
    t = table(d)
    block = d[t[7]:t[8]]
    end = block.index(b"\xff\xff\xff\xff")
    lines = block[:end].split(b"\r\n")
    rows = load_rows("names.json")
    new = [row_text(r, markers, NAME_ROOM) or lines[i] for i, r in enumerate(rows)]
    if new == lines:
        return {}
    block = b"\r\n".join(new) + block[end:]
    n = t[0] // 4
    out = bytearray(d[:t[7]]) + block
    offs = list(t[:n])
    for e in range(8, n):  # later entries shift, each keeping its alignment mod 4
        while len(out) % 4 != t[e] % 4:
            out.append(0)
        offs[e] = len(out)
        out += d[t[e]:t[e + 1]]
    struct.pack_into(f"<{n}I", out, 0, *offs)
    if len(out) > SYSDATA_MAX:
        raise ValueError(f"SYSDATA.BIN is {len(out)} bytes, over {SYSDATA_MAX}")
    return {"SYSDATA.BIN": bytes(out)}


def build_files(tree, out, markers=False, qa=None):
    """Write every changed file under out; returns {disc path: written path}."""
    QA.clear()
    QA.update(qa or {})
    files = {**build_maps(tree, markers), **build_exe(tree, markers), **build_names(tree, markers)}
    written = {}
    for rel, data in files.items():
        p = Path(out, rel)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        written[rel] = p
    return written


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--markers", action="store_true")
    ap.add_argument("--tree", default=str(extract.TREE))
    ap.add_argument("--out", default=str(ROOT / "work/build/files"))
    a = ap.parse_args()
    for rel in build_files(a.tree, a.out, a.markers):
        print(rel)
