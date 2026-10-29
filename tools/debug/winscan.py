"""Map winlog.lua MSG lines from a scene tour to script rows: which box (width px, lines) each shown line used.

usage: python -X utf8 tools/debug/winscan.py [TOUR_DIR=work/qa/wintour] [--files work/build/files] [--json OUT]
A message pointer is resolved against the MAPDAT the scene loads (mapNN[r] -> MAPNN[R]) and MAP86 (the New Game
intro every warp plays first). Prints variant counts; --json writes {row id: [wpx, lines, W, x, y]}.
"""
import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import script as sc  # noqa: E402

MAPDAT_RAM = 0x80170000
MSG = re.compile(r"MSG f(\d+) run \d+ ptr ([0-9A-F]+) win (\d+) x (-?\d+) y (-?\d+) wpx (-?\d+) hpx (-?\d+) W (-?\d+) "
                 r"lines (-?\d+)")


def strings_by_ptr(path):
    """{RAM address of the text: row id} for one MAPDAT (a rebuilt one: ids use the original offsets, matched by
    string order, which a rebuild keeps)."""
    d, t, scripts = sc.scripts(path)
    name = path.parent.name
    _, _, orig = sc.scripts(ROOT / "work/disc/tree/MAP01_06" / name / "MAPDAT.BIN")
    out = {}
    for slot, b in scripts.items():
        new = sorted(sc.strings_of(b).items())
        old = sorted(sc.strings_of(orig[slot]))
        assert len(new) == len(old), f"{name}/{slot}: string count differs from the original"
        for (off, (_, kind, _)), o in zip(new, old):
            out[MAPDAT_RAM + t[slot] + off + (2 if kind == "inline" else 0)] = f"{name}/{slot}/{o:04X}"
    return out


def mapdat(name, files):
    for base in (Path(files), ROOT / "work/disc/tree"):
        p = base / "MAP01_06" / name / "MAPDAT.BIN"
        if p.exists():
            return p
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tour", nargs="?", default=str(ROOT / "work/qa/wintour"))
    ap.add_argument("--files", default=str(ROOT / "work/build/files"))
    ap.add_argument("--json")
    a = ap.parse_args()
    rows, unknown, cache = {}, Counter(), {}
    for log in sorted(Path(a.tour).glob("*/log.txt")):
        scene = log.parent.name
        m = re.fullmatch(r"map(\d\d)(r?)", scene)
        dirs = ["MAP86"] + ([f"MAP{m[1]}{m[2].upper()}"] if m else [])
        for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
            g = MSG.search(line)
            if not g:
                continue
            ptr = int(g[2], 16)
            rid = None
            for dname in reversed(dirs):
                if dname not in cache:
                    p = mapdat(dname, a.files)
                    cache[dname] = strings_by_ptr(p) if p else {}
                rid = cache[dname].get(ptr) or rid
                if rid:
                    break
            if not rid:  # other scenes (world map, battle, cutscenes): accept a pointer only one MAPDAT explains
                if "*" not in cache:
                    cache["*"] = {}
                    for p in sorted((ROOT / "work/disc/tree/MAP01_06").glob("*/MAPDAT.BIN")):
                        for k, v in strings_by_ptr(mapdat(p.parent.name, a.files)).items():
                            cache["*"].setdefault(k, []).append(v)
                hits = cache["*"].get(ptr, [])
                rid = hits[0] if len(hits) == 1 else None
            box = [int(g[6]), int(g[9]), int(g[8]), int(g[4]), int(g[5])]
            if rid:
                rows.setdefault(rid, box)
            else:
                unknown[(scene, tuple(box))] += 1
    variants = Counter((b[0], b[1], b[2], b[3], b[4]) for b in rows.values())
    print(f"{len(rows)} rows seen")
    for (wpx, lines, w, x, y), n in variants.most_common():
        print(f"  {n:5d}  wpx {wpx} lines {lines} W {w} at {x},{y}  e.g. "
              f"{next(r for r, b in rows.items() if b == [wpx, lines, w, x, y])}")
    for (scene, box), n in unknown.most_common(15):
        print(f"  unresolved {scene} {box} x{n}")
    if a.json:
        Path(a.json).write_text(json.dumps(rows, indent=0), encoding="utf-8")


if __name__ == "__main__":
    main()
