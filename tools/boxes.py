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
import re
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


# Non-dialogue text (script/exe.json, records.json, names.json): (row ids, px per line, lines, how measured).
# Row ids: a regex, or ("EXE", lo, hi) = every EXE/xxxxx row with lo <= offset <= hi. First match wins.
# insert.fit_field: rows in NEWLINE get a trailing \n (menus whose items end by auto-wrap at the window edge);
# multi-line rows that start a window (WRAP) are wrapped to px - MARGIN. Other rows keep the translator's \n.
# Windows come from the create calls 0x8003DB60(x, y, w, h) (static list in docs/re/vwf.md §Fields) and the
# fieldlog tour (tools/debug/fieldlog.lua + fieldscan.py; work/qa/ft = marker build, work/qa/fo = original).
# "measured" = seen in a tour at that window/position; "window" = the window its code creates, not reached yet;
# "guess" = window and layout both inferred. px is for the row's own text; "shared" rows sit on a line after a
# name or another row, so their px already leaves room for it (NAME_PX for a one-part name).
NAME_PX = 48  # room kept for a one-part name (NAME/*) in front of a composed battle/field message
FIELDS = [
    (("EXE", 0xBE8, 0xC34), 40, 1, "measured: field command menu, window 40x80 at 24,48 (0x8002E8B0), one item "
     "per line by auto-wrap: insert ends each item with \\n (work/qa/ft/cmd/stateat.png)"),
    (("EXE", 0xC40, 0xC5C), 40, 1, "measured: field その他 sub-menu, window 40x80 at 56,72 (0x8002EAA8), one item "
     "per line (work/qa/ft/y0)"),
    (("EXE", 0xC68, 0xC68), 40, 2, "measured: last sub-menu item, two lines in the original (ステータス/セーブ)"),
    (("EXE", 0x13A0, 0x1448), 96, 1, "measured: VS box line (96x48 at 16,168 / 144,168, 0x8004C588) and status box "
     "(144x64): school / club on its own line"),
    (("EXE", 0x809FC, 0x80A4C), 96, 1, "measured: club part of the VS / status club line (E013C0-style lines)"),
    (("EXE", 0x1B6C, 0x1CD8), 224 - 2 * NAME_PX, 1, "measured: battle message line, window 224x16 at 16,27 "
     "(0x8004B898), shared: actor name + text (+ a target or magic name): px leaves 2 names (gameover log)"),
    (("EXE", 0x80A90, 0x80AA4), 224 - 2 * NAME_PX, 1, "measured: battle message pieces, same line as above"),
    (("EXE", 0x1CEC, 0x1D1C), 144 - NAME_PX, 4, "measured: battle result box 144x64 at 96,152 (0x8004C134), "
     "shared: name + text (gameover)"),
    (("EXE", 0x80AAC, 0x80AAC), 144 - NAME_PX, 4, "window: spacer printed into the battle result box (0x8004C1E4)"),
    (("EXE", 0x1E6C, 0x1EB0), 224, 1, "measured: field header window 224x16 at 16,24 (0x8002EBE0) (work/qa/ft/y1, y3)"),
    (("EXE", 0x1EBC, 0x1EC8), 80, 1, "window: field label 80x16 at 152,24 (0x8002EC54)"),
    (("EXE", 0x2080, 0x2080), 128, 1, "window: field yes/no (as 028C0): 'No' must start 64 px in"),
    (("EXE", 0x1ED8, 0x2090), 224, 4, "window: field message box 224x64 at 16,152 (0x8002EBBC); insert wraps"),
    (("EXE", 0x20A4, 0x21CC), 144 - NAME_PX, 4, "guess: club change / item use messages, shared with a name, "
     "face-box width 144x64 (0x8002ECF4) as the narrower field box"),
    (("EXE", 0x2440, 0x2440), 224, 1, "debug message (not faund no.), never shown in play"),
    (("EXE", 0x2458, 0x24B8), 224 - NAME_PX, 4, "window: level-up box 224x64 (0x8005F528), shared with a name"),
    (("EXE", 0x24C8, 0x24F8), 96, 1, "measured: birthday screen name, x 16 up to the stone plate at x 112 "
     "(work/qa/ft/z_birthday.png)"),
    (("EXE", 0x2510, 0x2718), 224, 4, "window: dress-up message box 224x64 at 16,152 (0x8006947C); insert wraps"),
    (("EXE", 0x295C, 0x295C), 96, 1, "measured: save/load file label, the file number follows, date/なし at x 112 "
     "(work/qa/ft/z_load.png)"),
    (("EXE", 0x28C0, 0x28C0), 128, 1, "measured: save yes/no at x 96 in the 224x160 window; the cursor sits where "
     "the Japanese いいえ began, 64 px in: pad 'Yes' with spaces (4 px each) so 'No' starts at 64 px "
     "(work/qa/fq/s1.png)"),
    (("EXE", 0x2760, 0x2B24), 224, 10, "measured: save/load window 224x160 at 16,56 (0x8006AA2C); insert wraps"),
    (("EXE", 0x2B38, 0x2B38), 48, 5, "measured: club-select stat labels, window 104x80 at 128,18 (0x8006C8C0), "
     "numbers at x 48"),
    (("EXE", 0x80AB4, 0x80AB8), 16, 1, "guess: battle UI separators (one glyph)"),
    (("EXE", 0x80AC0, 0x80AF4), 48, 1, "window: battle status labels in 224x64 at 16,154 (0x80051618), numbers "
     "follow: keep the original width"),
    (("EXE", 0x80B10, 0x80B64), 32, 1, "measured: status box labels (LV/MLV/HP/AT..) between numbers in 144x64 "
     "(work/qa/ft/y3): keep the original width"),
    (("EXE", 0x80B68, 0x80B70), 224, 1, "window: field header / message piece"),
    (("EXE", 0x80B94, 0x80BB8), 48, 2, "window: level-up stat labels between numbers (224x64 box)"),
    (("EXE", 0x80BCC, 0x80BCC), 16, 1, "guess: save list unit after a number (面)"),
    (("EXE", 0x80BD0, 0x80BD0), 12, 1, "measured: birthday month mark, day digits 12 px later"),
    (("EXE", 0x80BD4, 0x80BD4), 16, 1, "measured: birthday day mark at x 232, window edge 248"),
    (("EXE", 0x80BE8, 0x80BE8), 112, 1, "measured: save list 'none', x 112 to the window edge"),
    (r"CLUB/\d\d/name", 112, 1, "guess: club choice list (0x80055FD4) in the 224x64 field box, two columns"),
    (r"ITEM/\d\d/name|MAGIC/\d\d/name", 128, 1, "guess: item/magic list in 224x64 at 16,152 (work/qa/ft/z_sub3.png, "
     "empty); the longest Japanese name is 128 px"),
    (r"ITEM/\d\d/desc|MAGIC/\d\d/desc", 224, 1, "measured: description line, window 224x16 (gameover log: MAGIC "
     "desc in 224x16 at 16,27)"),
    (r"NAME/\d{3}", NAME_PX, 1, "measured: VS / status box line 1 = surname + given name, 96 px for both"),
    (r"MEMCARD", 0, 0, "BIOS memory-card manager title: full-width Shift-JIS, bytes only (insert keeps Japanese)"),
]
NEWLINE = [("EXE", 0xBE8, 0xC5C)]
WRAP = [("EXE", 0x1ED8, 0x2090), ("EXE", 0x2510, 0x2718), ("EXE", 0x2760, 0x2B24)]


def _match(key, rid):
    if isinstance(key, tuple):
        pre, lo, hi = key
        return rid.startswith(pre + "/") and lo <= int(rid.split("/")[1], 16) <= hi
    return re.fullmatch(key, rid) is not None


def field(rid):
    """(px, lines, how) for a non-dialogue row, or None if no budget is known."""
    return next(((px, lines, how) for key, px, lines, how in FIELDS if _match(key, rid)), None)


def fit(rid):
    """'nl', 'wrap' or '' : how insert fits a non-dialogue row (see NEWLINE, WRAP)."""
    return "nl" if any(_match(k, rid) for k in NEWLINE) else "wrap" if any(_match(k, rid) for k in WRAP) else ""


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
