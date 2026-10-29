"""build.py: unpack the disc (once) and repack it to build/nage_libre_en.bin + .cue.

    python -X utf8 tools/build.py [--markers] [--qa ID=TEXT]..

Checks the dump against rom.sha1 first. The unpacked tree and its mkpsxiso layout live in work/disc/ (dumpsxiso,
made on first run, never written after). insert.py writes the changed files to work/build/files/ and a layout copy
in work/build/ points mkpsxiso at them. With no edits the output is byte-identical to the original
(tests/test_identity.py)."""
import argparse
import hashlib
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import check_rom  # noqa: E402
import insert  # noqa: E402

MKPSXISO = ROOT / "tools/mkpsxiso/mkpsxiso-2.30-win64"
CUE = ROOT / "rom/Nage Libre - Rasen no Soukoku (Japan).cue"
DISC = ROOT / "work/disc"
OUT = ROOT / "build/nage_libre_en.bin"
WORK = ROOT / "work/build"


def unpack(disc=DISC, cue=CUE):
    """dumpsxiso the original into disc/tree + disc/layout.xml (the layout's paths are relative to disc/)."""
    if (disc / "layout.xml").exists():
        return
    disc.mkdir(parents=True, exist_ok=True)
    subprocess.run([str(MKPSXISO / "dumpsxiso.exe"), "-x", "tree", "-s", "layout.xml", str(cue)],
                   cwd=disc, check=True, stdout=subprocess.DEVNULL)


def edited_layout(edits, disc=DISC, work=WORK):
    """Copy of disc/layout.xml with absolute paths, each disc path in edits {rel: file} pointing at its new file.
    The unpacked tree stays untouched (tests read it)."""
    tree = ET.parse(disc / "layout.xml")
    root = tree.getroot()
    root.find(".//license").set("file", str((disc / root.find(".//license").get("file")).resolve()))
    dt = root.find(".//directory_tree")
    dt.set("source", str((disc / dt.get("source")).resolve()))
    left = dict(edits)

    def walk(node, path):
        for child in node:
            if child.tag == "dir":
                walk(child, path + [child.get("name")])
            elif child.tag == "file":
                rel = "/".join(path + [child.get("name")])
                if rel in left:
                    child.set("source", str(Path(left.pop(rel)).resolve()))
    walk(dt, [])
    if left:
        raise ValueError(f"not in the layout: {sorted(left)}")
    work.mkdir(parents=True, exist_ok=True)
    tree.write(work / "layout.xml")
    return work


def pack(out=OUT, disc=DISC):
    """mkpsxiso disc/layout.xml to out (.bin) and its .cue; returns the .bin's SHA-1."""
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([str(MKPSXISO / "mkpsxiso.exe"), "-q", "-y", "-o", str(out), "-c", str(out.with_suffix(".cue")),
                    "layout.xml"], cwd=disc, check=True)
    with open(out, "rb") as f:
        return hashlib.file_digest(f, "sha1").hexdigest()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--markers", action="store_true", help="every line becomes [id] marker text (phase 5)")
    ap.add_argument("--qa", action="append", default=[], metavar="ID=TEXT",
                    help="override one row's text for this build (stress lines, glyph torture line)")
    a = ap.parse_args()
    check_rom.check()
    unpack()
    files = WORK / "files"
    shutil.rmtree(files, ignore_errors=True)
    edits = insert.build_files(DISC / "tree", files, a.markers, dict(q.split("=", 1) for q in a.qa))
    sha1 = pack(OUT, edited_layout(edits))
    print(f"{len(edits)} files changed; {OUT.relative_to(ROOT)} sha1 {sha1}")
