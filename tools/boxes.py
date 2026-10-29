"""Dialogue box variants and their measured budgets (docs/re/vwf.md §Boxes), and which variant each script line uses.

    python -X utf8 tools/boxes.py [--check work/qa/boxes_seen.json]   counts per variant; --check compares the
                                                                       static rule with a tour (debug/winscan.py)

Rule (from op 17's handler 0x8005F4AC and the tour): op 16 (speaker + face) opens the face box, whose text area
is 144 px; op 17 opens a box with no face, 224 px. A line takes the box of the last 16/17 before it in script
order. MAP85 and MAP86 (New Game intro) run in mode 3 ($80090C58), where the box has 3 lines instead of 4.
"""
import argparse
import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract  # noqa: E402
import script as sc  # noqa: E402

# name: (text width px, lines, how measured)
BOXES = {
    "face": (144, 4, "measured: winlog W=18 lines=4, work/qa/wintour (MAP02/186/0024 ...)"),
    "face3": (144, 3, "measured: winlog W=18 lines=3, MAP85 + MAP86 intro (MAP86/186/0016)"),
    "plain": (224, 4, "measured: winlog W=28 lines=4, MAP14R/187/01DA"),
}
THREE_LINE_MAPS = {"MAP85", "MAP86"}  # seen 3-line in the tour; every other map seen was 4-line
# the engine wraps by itself once the pen reaches the box width (x >= 8*W after a glyph), so a line must end short
# of it: wrapped lines take at most width - MARGIN px of advance
MARGIN = 1


def budget(box):
    """(wrap width px, lines) for a box name."""
    width, lines, _ = BOXES[box]
    return width - MARGIN, lines


def classify(name, b):
    """{string offset: box name} for one script."""
    parsed = sc.parse(b)
    code = parsed[0]
    face_box = "face3" if name in THREE_LINE_MAPS else "face"
    out, face = {}, True  # before any 16/17: assume the face box (narrower, safe)
    for o in sorted(code):
        ins = code[o]
        if ins.op == 0x16:
            face = True
        elif ins.op == 0x17:
            face = False
        if ins.text is not None:
            out[o] = face_box if face else "plain"
    for o in sc.strings_of(b, parsed):  # strings by offset (none on this disc): the face box
        out.setdefault(o, face_box)
    return out


def all_rows(tree=extract.TREE):
    """{row id: box name} for every dialogue line."""
    out = {}
    for path in extract.map_files(tree):
        name = path.parent.name
        _, _, scripts = sc.scripts(path)
        for slot, b in scripts.items():
            for o, box in classify(name, b).items():
                out[f"{name}/{slot}/{o:04X}"] = box
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--check")
    a = ap.parse_args()
    rows = all_rows()
    print(Counter(rows.values()))
    if a.check:
        seen = json.load(open(a.check, encoding="utf-8"))
        bad = 0
        for rid, (wpx, lines, *_) in seen.items():
            want = BOXES[rows[rid]][:2]
            if (wpx, lines) != want:
                bad += 1
                print(f"MISMATCH {rid}: rule {rows[rid]} {want}, seen {wpx}x{lines}")
        print(f"{len(seen) - bad}/{len(seen)} seen lines match the rule")
        sys.exit(1 if bad else 0)
