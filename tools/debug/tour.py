"""Visual-QA tour: warp to every scene (regen.py), keep playing with circle mashed, sheet the frames that changed.

usage: python -X utf8 tools/debug/tour.py [--cue CUE] [--only a,b] [--jobs 3] [--frames 12000] [--out DIR]
Writes DIR/<scene>/f*.png and DIR/<scene>_sheet.png (+ _sheet_2.png ...), the input of
`qa_gate.py init work/qa/manifest.tsv DIR`. Default --out: work/qa/tour (build) or work/qa/tour_jp (original).
"""
import argparse
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import regen
from regen import ROOT, ORIG, SCENES, SKILL


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cue", default=str(ROOT / "build/nage_libre_en.cue"))
    ap.add_argument("--only")
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--frames", type=int, default=12000, help="frames after the warp lands")
    ap.add_argument("--out")
    a = ap.parse_args()
    orig = Path(a.cue).resolve() == ORIG.resolve()
    out = Path(a.out or ROOT / ("work/qa/tour_jp" if orig else "work/qa/tour")).resolve()  # warp.lua finds the repo from it
    r = argparse.Namespace(cue=a.cue, tree=str(ROOT / "work/disc/tree"), no_states=True, out=str(out),
                           edits=None if orig else str(ROOT / "work/build/files"),
                           extra=f"--var STAY={a.frames} "
                                 f"--script {(ROOT / 'tools/debug/tourshot.lua').as_posix()} --frames {30000 + a.frames} "
                                 f"--timeout 1200")
    names = a.only.split(",") if a.only else regen.scene_names(SCENES.read_text(encoding="utf-8"))
    with ThreadPoolExecutor(a.jobs) as ex:
        results = list(ex.map(lambda n: regen.run(n, r), names))
    for name, ok, why in results:
        print(f"{'ok  ' if ok else 'FAIL'} {name} {why}", flush=True)
        if ok:
            subprocess.run([sys.executable, "-X", "utf8", str(Path(SKILL) / "scripts/sheet.py"), str(out / name),
                            "--changed", "0.02", "--div", "1", "--cols", "4", "--max", "16",
                            "--out", str(out / f"{name}_sheet.png")], check=False, capture_output=True)
    failed = [n for n, ok, _ in results if not ok]
    print(f"{len(results) - len(failed)}/{len(results)} scenes ok")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
