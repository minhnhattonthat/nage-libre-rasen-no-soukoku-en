"""Warp to every scene in tools/debug/scenes.lua from a cold boot, check it, save its state, sheet the shots.

usage: python -X utf8 tools/debug/regen.py [--cue CUE] [--tree DIR] [--only a,b] [--jobs 3] [--no-states]
  --cue    disc to boot (default: the original; pass build/nage_libre_en.cue for the build)
  --tree   unpacked disc tree whose MAPDAT files the map checks compare against (default work/disc/tree;
           pass the build's tree for a build)
Writes work/qa/warp/<scene>/<scene>.png + log.txt, work/states/<scene>.sstate, work/qa/warp/all*.png.
Exit 1 if any scene fails its check or the run errors/times out. Run after engine, font or graphics changes:
states keep the old code and VRAM.
"""
import argparse
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from skill import SKILL  # noqa: E402

SCENES = ROOT / "tools/debug/scenes.lua"
ORIG = ROOT / "rom/Nage Libre - Rasen no Soukoku (Japan).cue"


def scene_names(text):
    body = text[text.index("\nreturn {"):]
    return re.findall(r"(?m)(?:^  |, )(\w+) = (?:\{|wm\()", body)   # 2-space indent or after ", " (wm lines)


def run(name, a):
    out = ROOT / "work/qa/warp" / name
    cmd = [sys.executable, "-X", "utf8", str(Path(SKILL) / "scripts/emu.py"), str(a.cue), "--out", str(out),
           "--script", str(ROOT / "tools/debug/warp.lua"), "--var", f"SCENE='{name}'",
           "--var", f"DISC_TREE=[[{Path(a.tree).resolve().as_posix()}]]", "--frames", "30000", "--timeout", "600"]
    if not a.no_states:
        cmd += ["--state-out", str(ROOT / "work/states" / f"{name}.sstate")]
    p = subprocess.run(cmd, capture_output=True, text=True)
    log = (out / "log.txt").read_text(encoding="utf-8", errors="replace") if (out / "log.txt").exists() else ""
    ok = p.returncode == 0 and "CHECK ok" in log
    why = "" if ok else (re.findall(r"CHECK FAIL.*", log + p.stdout + p.stderr) or [f"exit {p.returncode}, no CHECK"])[0]
    return name, ok, why


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cue", default=str(ORIG))
    ap.add_argument("--tree", default=str(ROOT / "work/disc/tree"))
    ap.add_argument("--only", help="comma-separated scene names")
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--no-states", action="store_true")
    a = ap.parse_args()
    names = scene_names(SCENES.read_text(encoding="utf-8"))
    assert len(names) == len(set(names)), "duplicate scene names"
    if a.only:
        want = a.only.split(",")
        bad = [n for n in want if n not in names]
        if bad:
            sys.exit(f"unknown scenes: {bad}")
        names = want
    with ThreadPoolExecutor(a.jobs) as ex:
        results = list(ex.map(lambda n: run(n, a), names))
    for name, ok, why in results:
        print(f"{'ok  ' if ok else 'FAIL'} {name} {why}")
    shots = [str(ROOT / "work/qa/warp" / n / f"{n}.png") for n, ok, _ in results if ok]
    if shots:
        subprocess.run([sys.executable, "-X", "utf8", str(Path(SKILL) / "scripts/sheet.py"), *shots, "--cols", "6",
                        "--max", "24", "--out", str(ROOT / "work/qa/warp/all.png")], check=False)
    failed = [n for n, ok, _ in results if not ok]
    print(f"{len(results) - len(failed)}/{len(results)} scenes ok")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
