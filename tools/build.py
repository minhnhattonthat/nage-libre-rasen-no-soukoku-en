"""build.py: unpack the disc (once) and repack it to build/nage_libre_en.bin + .cue.

    python -X utf8 tools/build.py

Checks the dump against rom.sha1 first. The unpacked tree and its mkpsxiso layout live in work/disc/ (dumpsxiso,
made on first run). With no edits the output is byte-identical to the original (tests/test_identity.py)."""
import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import check_rom  # noqa: E402

MKPSXISO = ROOT / "tools/mkpsxiso/mkpsxiso-2.30-win64"
CUE = ROOT / "rom/Nage Libre - Rasen no Soukoku (Japan).cue"
DISC = ROOT / "work/disc"
OUT = ROOT / "build/nage_libre_en.bin"


def unpack(disc=DISC, cue=CUE):
    """dumpsxiso the original into disc/tree + disc/layout.xml (the layout's paths are relative to disc/)."""
    if (disc / "layout.xml").exists():
        return
    disc.mkdir(parents=True, exist_ok=True)
    subprocess.run([str(MKPSXISO / "dumpsxiso.exe"), "-x", "tree", "-s", "layout.xml", str(cue)],
                   cwd=disc, check=True, stdout=subprocess.DEVNULL)


def pack(out=OUT, disc=DISC):
    """mkpsxiso disc/layout.xml to out (.bin) and its .cue; returns the .bin's SHA-1."""
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([str(MKPSXISO / "mkpsxiso.exe"), "-q", "-y", "-o", str(out), "-c", str(out.with_suffix(".cue")),
                    "layout.xml"], cwd=disc, check=True)
    with open(out, "rb") as f:
        return hashlib.file_digest(f, "sha1").hexdigest()


if __name__ == "__main__":
    check_rom.check()
    unpack()
    sha1 = pack()
    print(f"{OUT.relative_to(ROOT)} sha1 {sha1}")
