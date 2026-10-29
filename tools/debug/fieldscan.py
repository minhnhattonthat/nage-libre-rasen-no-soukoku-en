"""Map fieldlog.lua STR lines from a marker-build tour to EXE / record / name rows: where each row's text starts on
screen and how many px it has before the next field or the window's wrap edge (budgets for boxes.FIELDS).

usage: python -X utf8 tools/debug/fieldscan.py TOUR_DIR [TOUR_DIR..] [--json work/qa/fields_seen.json] [--all]
A row is found by its pointer (the string in NAGE.EXE, record field in place) or, in a composed buffer, by its
marker text (insert.marker: E00BE8MMM, I03nameMMM, N123MM). Room = next placed field's pen x on the same line in
the same window (another print in the same frame that does not start where the previous one ended), else the wrap
edge 8*W; minus the row's start x. Marker text that overflows shifts later fields: read the room with the shot. Prints the tightest
observation per row; --all prints every observation.
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import extract  # noqa: E402
import font  # noqa: E402
import text  # noqa: E402

STR = re.compile(r"STR f(\d+) (\w+) ptr ([0-9A-F]+) win (\d+) x (-?\d+) y (-?\d+) wpx (-?\d+) hpx (-?\d+) W (-?\d+) "
                 r"lines (-?\d+) penx (-?\d+) peny (-?\d+) hex (\w*)")
MARK = re.compile(r"E([0-9A-F]{5})|N(\d{3})|([CIM])(\d\d)(name|desc)")
TABLE = {"C": "CLUB", "I": "ITEM", "M": "MAGIC"}


def ranges():
    """[(ram lo, ram hi, row id)] for every EXE string and record field."""
    out = []
    for r in json.loads((ROOT / "script/exe.json").read_text(encoding="utf-8")):
        lo = int(r["id"][4:], 16) + extract.EXE_BASE
        out.append((lo, lo + len(text.encode(r["jp"])) + 1, r["id"]))
    for name, base, size, count, fields in extract.TABLES:
        for i in range(count):
            for field, off, n in fields:
                lo = base + i * size + off + extract.EXE_BASE
                out.append((lo, lo + n, f"{name}/{i:02d}/{field}"))
    return out


def layout(s, x, y, w):
    """[(x, y)] before each char of decoded text s, wrapping like the engine (after a glyph, x >= 8*W)."""
    pos, half, i = [], False, 0
    while i < len(s):
        pos.append((x, y))
        m = font.CTRL.match(s, i)
        if m:
            half = {"%h": True, "%z": False}.get(m[0], half)
            if m[0] == "%p":
                x = y = 0
            pos += [(x, y)] * (len(m[0]) - 1)
            i += len(m[0])
            continue
        c = s[i]
        if c == "\n":
            x, y = 0, y + 16
        else:
            x += font.advance(c) if " " <= c <= "~" else 8 if half else 16
            if w > 0 and x >= 8 * w:
                x, y = 0, y + 16
        i += 1
    pos.append((x, y))
    return pos


def scan(tours):
    rng = ranges()
    obs = {}
    for tour in tours:
        for log in sorted(Path(tour).glob("**/log.txt")):
            scene = log.parent.name
            ents = [g for g in map(STR.search, log.read_text(encoding="utf-8", errors="replace").splitlines()) if g]
            pos_of, ends, placed = {}, {}, set()
            for g in ents:  # a print that starts where the window's last one ended continues it, else it is placed
                s = text.decode(bytes.fromhex(g[13]))
                pos_of[id(g)] = pos = layout(s, int(g[11]), int(g[12]), int(g[9]))
                if ends.get(g[4]) != (int(g[11]), int(g[12])):
                    placed.add(id(g))
                ends[g[4]] = pos[-1]
            for g in ents:
                f, ptr, win, w, lines = int(g[1]), int(g[3], 16), int(g[4]), int(g[9]), int(g[10])
                s = text.decode(bytes.fromhex(g[13]))
                pos = pos_of[id(g)]
                marks = [(m.start(), f"EXE/{m[1]}" if m[1] else f"NAME/{m[2]}" if m[2] else
                          f"{TABLE[m[3]]}/{m[4]}/{m[5]}") for m in MARK.finditer(s)]
                # the pointer names the row unless a marker at the start says otherwise (a record run past its field)
                hits = marks if marks and marks[0][0] == 0 else [(0, rid) for lo, hi, rid in rng if lo <= ptr < hi]
                hits += [h for h in marks if h not in hits]
                for k, rid in hits:
                    sx, sy = pos[k]
                    nxt = [int(h[11]) for h in ents if h is not g and id(h) in placed and int(h[1]) == f
                           and int(h[4]) == win and int(h[12]) == sy and int(h[11]) > sx]
                    edge = min(nxt) if nxt else 8 * w
                    line = sy // 16
                    obs.setdefault(rid, []).append({
                        "scene": scene, "f": f, "kind": g[2], "win": win, "box": [int(g[5]), int(g[6]), int(g[7]),
                                                                                    int(g[8]), w, lines],
                        "x": sx, "y": sy, "room": edge - sx, "lines": max(lines - line, 1),
                        "used": max(x for x, y in pos[k:] if y == sy) - sx,
                        "next": bool(nxt), "text": s})
    return obs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tours", nargs="+")
    ap.add_argument("--json")
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    obs = scan(a.tours)
    for rid in sorted(obs):
        os_ = sorted(obs[rid], key=lambda o: o["room"])
        for o in os_ if a.all else os_[:1]:
            print(f"{rid:16} room {o['room']:4d} px used {o['used']:3d} x {o['x']:3d} y {o['y']:3d} lines {o['lines']:2d} "
                  f"{'next' if o['next'] else 'edge'} win {o['win']} {o['box']} {o['scene']} {o['kind']} "
                  f"{o['text'][:40]!r}")
    print(f"{len(obs)} rows seen")
    if a.json:
        Path(a.json).write_text(json.dumps(obs, indent=0), encoding="utf-8")


if __name__ == "__main__":
    main()
