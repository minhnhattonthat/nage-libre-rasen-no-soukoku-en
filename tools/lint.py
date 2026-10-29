"""Text lint for script/ English (docs/text-format.md, docs/re/vwf.md). Exit 1 on any error; warnings print only.

    python -X utf8 tools/lint.py [--warn]

Errors: a character with no glyph (non-ASCII, `\\`), a fixed field over its bytes (records), a colour code `%cNN`
of the Japanese missing, a word wider than its box. Warnings (--warn lists them): a dialogue line that needs more
than one box page (it still works: insert.py pages it with %k%p), an EXE string over its in-place room (phase 7
relocates it). Also: all English names together over SYSDATA's 0xC000-byte buffer.
"""
import argparse
import glob
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import boxes  # noqa: E402
import font  # noqa: E402
import insert  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FIELD_ROWS = set()  # non-dialogue row ids (exe, records, names): checked against boxes.FIELDS
COLOUR = re.compile(r"%c\d\d")
NAMES_SLACK = 0xC000 - 47289  # SYSDATA buffer minus the original file (insert.SYSDATA_MAX)


def check_row(r, box=None, fixed=False):
    """([errors], [warnings]) for one row."""
    en, err, warn = r.get("en", ""), [], []
    if not en:
        return err, warn
    bad = sorted({c for c in font.CTRL.sub("", en) if c != "\n" and not (" " <= c <= "~") or c == "\\"})
    if bad:
        err.append(f"no glyph for {''.join(bad)!r}")
    if re.search(r"%(?![hzpk]|[ct]\d\d)", en):
        err.append("bare '%' (the renderer reads it as a control code and never draws it)")
    if sorted(COLOUR.findall(en)) != sorted(COLOUR.findall(r["jp"])):
        err.append(f"colour codes {COLOUR.findall(r['jp'])} not kept")
    if box is None and r["id"] in FIELD_ROWS:
        en = insert.fit_field(r["id"], en)
    if "max" in r and len(en.encode("ascii", "replace")) > r["max"]:
        (err if fixed else warn).append(f"{len(en)} bytes, room {r['max']}")
    f = boxes.field(r["id"]) if box is None and r["id"] in FIELD_ROWS else None
    if f and f[0] and not bad:
        px, lines, _ = f
        for page in en.removesuffix("\n").split("%p"):
            ls = page.split("\n")
            wide = [s for s in ls if font.advance(s) > px]
            if wide:
                err.append(f"{font.advance(wide[0])} px in a {px}-px field: {wide[0]!r}")
            if len(ls) > lines:
                err.append(f"{len(ls)} lines in a {lines}-line field")
    if box and not bad:
        width, lines = boxes.budget(box)
        wrapped = font.wrap(en, width)
        wide = [w for w in wrapped if font.advance(w) > width]
        if wide:
            err.append(f"word wider than the {box} box ({width} px): {wide[0]!r}")
        elif len(wrapped) > lines:
            warn.append(f"{len(wrapped)} lines in a {lines}-line {box} box: pages")
    return err, warn


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--warn", action="store_true")
    a = ap.parse_args()
    box_of = boxes.all_rows()
    errors = warnings = 0
    files = sorted(glob.glob(str(ROOT / "script/maps/*.json"))) + [str(ROOT / f"script/{n}.json") for n in
                                                                   ("exe", "records", "names")]
    for path in files:
        for r in json.loads(Path(path).read_text(encoding="utf-8")):
            if "maps" not in Path(path).parts:
                FIELD_ROWS.add(r["id"])
                if boxes.field(r["id"]) is None:
                    print(f"warn  {r['id']}: no measured budget (add it to boxes.FIELDS)")
                    warnings += 1
            err, warn = check_row(r, box_of.get(r["id"]), fixed=path.endswith("records.json"))
            for e in err:
                print(f"ERROR {r['id']}: {e}")
            if a.warn:
                for w in warn:
                    print(f"warn  {r['id']}: {w}")
            errors += len(err)
            warnings += len(warn)
    names = json.loads((ROOT / "script/names.json").read_text(encoding="utf-8"))
    grow = sum(len(r["en"]) - len(r["jp"].encode("cp932")) for r in names if r.get("en"))
    if grow > NAMES_SLACK:
        print(f"ERROR names: English names add {grow} bytes to SYSDATA, room {NAMES_SLACK} (docs/re/vwf.md)")
        errors += 1
    print(f"lint: {errors} errors, {warnings} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
