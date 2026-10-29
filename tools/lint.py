"""Text lint for script/ English (docs/text-format.md, docs/re/vwf.md). Exit 1 on any error; warnings print only.

    python -X utf8 tools/lint.py [--warn]

Errors: a character with no glyph (non-ASCII, `\\`), a fixed field over its bytes (records), a colour code `%cNN`
of the Japanese missing, a word wider than its box. Warnings (--warn lists them): a dialogue line that needs more
than one box page (it still works: insert.py pages it with %k%p), an EXE string over its in-place room (phase 7
relocates it).
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

ROOT = Path(__file__).resolve().parents[1]
COLOUR = re.compile(r"%c\d\d")


def check_row(r, box=None, fixed=False):
    """([errors], [warnings]) for one row."""
    en, err, warn = r.get("en", ""), [], []
    if not en:
        return err, warn
    bad = sorted({c for c in font.CTRL.sub("", en) if c != "\n" and not (" " <= c <= "~") or c == "\\"})
    if bad:
        err.append(f"no glyph for {''.join(bad)!r}")
    if sorted(COLOUR.findall(en)) != sorted(COLOUR.findall(r["jp"])):
        err.append(f"colour codes {COLOUR.findall(r['jp'])} not kept")
    if "max" in r and len(en.encode("ascii", "replace")) > r["max"]:
        (err if fixed else warn).append(f"{len(en)} bytes, room {r['max']}")
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
            err, warn = check_row(r, box_of.get(r["id"]), fixed=path.endswith("records.json"))
            for e in err:
                print(f"ERROR {r['id']}: {e}")
            if a.warn:
                for w in warn:
                    print(f"warn  {r['id']}: {w}")
            errors += len(err)
            warnings += len(warn)
    print(f"lint: {errors} errors, {warnings} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
