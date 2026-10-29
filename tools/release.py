"""release.py: check -> build -> boot smoke -> leftover Japanese -> visual-QA gate -> xdelta3 patch -> re-apply and
compare -> README + zip.

    python -X utf8 tools/release.py VERSION [--force] [--no-qa]     (e.g. 1.0) -> release/NageLibre_EN_vVERSION.zip

The patch is against the .bin in rom/ (rom.sha1); the zip holds the patch and README.txt only (no .cue: players keep
their own). --no-qa skips the visual-QA gate for test packages; the publish guard still requires it. Release dirs
stay local (gitignored); publishing is the user's call. The playable image stays in build/. The debug tool
(tools/debug/*.lua) runs only inside the emulator and is never part of the image.
"""
import argparse
import hashlib
import shutil
import subprocess
import sys
import zipfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from skill import SKILL  # noqa: E402

SCRIPTS = Path(SKILL) / "scripts"
ROM = ROOT / "rom/Nage Libre - Rasen no Soukoku (Japan).bin"
BUILT = ROOT / "build/nage_libre_en.bin"
QA = ROOT / "work/qa"


def run(*cmd, **kw):
    p = subprocess.run([str(c) for c in cmd], cwd=ROOT, **kw)
    if p.returncode:
        sys.exit(f"failed: {' '.join(map(str, cmd))}")
    return p


def hashes(p):
    md5, sha1, crc = hashlib.md5(), hashlib.sha1(), 0
    with open(p, "rb") as f:
        while b := f.read(1 << 22):
            crc = zlib.crc32(b, crc)
            md5.update(b)
            sha1.update(b)
    return {"size": p.stat().st_size, "crc32": f"{crc:08x}", "md5": md5.hexdigest(), "sha1": sha1.hexdigest()}


def leftover():
    """Japanese runs the build left unchanged in NAGE.EXE and SYSDATA.BIN (jp_left.py --orig). MAPDAT dialogue is
    covered by check.py: lint fails a Japanese row with no English, and tests/test_extract.py finds no MAPDAT text
    outside the extracted lines (a raw scan there only hits map data that decodes as katakana)."""
    bad = []
    for name in ("NAGE.EXE", "SYSDATA.BIN"):
        f, orig = ROOT / "work/build/files" / name, ROOT / "work/disc/tree" / name
        p = subprocess.run([sys.executable, "-X", "utf8", str(SCRIPTS / "jp_left.py"), str(f), "--orig", str(orig),
                            "--sjis"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
        if not p.stdout.rstrip().endswith("0 Japanese runs, 0 bytes (unchanged from original)"):
            bad.append(f"{name}:\n{p.stdout}{p.stderr}")
    return bad


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("version")
    ap.add_argument("--force", action="store_true", help="overwrite this version's existing release files")
    ap.add_argument("--no-qa", action="store_true", help="skip the visual-QA gate (test packages only)")
    a = ap.parse_args()
    rel, z = ROOT / "release" / f"v{a.version}", ROOT / "release" / f"NageLibre_EN_v{a.version}.zip"
    if (rel.exists() or z.exists()) and not a.force:
        sys.exit(f"{rel} exists; pass --force to overwrite")

    run(sys.executable, "-X", "utf8", "tools/check.py")
    run(sys.executable, "-X", "utf8", "tools/build.py")
    run(sys.executable, "-X", "utf8", SCRIPTS / "emu.py", BUILT.with_suffix(".cue"), "--out", QA / "release_smoke",
        "--route", "tools/routes/boot.txt", "--smoke")
    if bad := leftover():
        sys.exit("Japanese left in the build:\n" + "\n".join(bad))
    if not a.no_qa:
        run(sys.executable, "-X", "utf8", SCRIPTS / "qa_gate.py", "check", QA / "manifest.tsv", QA / "verdicts")

    shutil.rmtree(rel, ignore_errors=True)
    rel.mkdir(parents=True)
    patch = rel / f"NageLibre_EN_v{a.version}.xdelta"
    run("xdelta3", "-e", "-9", "-f", "-s", ROM, BUILT, patch)
    test = ROOT / "work/release_reapplied.bin"
    run("xdelta3", "-d", "-f", "-s", ROM, patch, test)
    o, b = hashes(ROM), hashes(BUILT)
    if hashes(test)["sha1"] != b["sha1"]:
        sys.exit("re-applied patch differs from the build")
    test.unlink()
    info = (f"{ROM.name}\n  size {o['size']}  CRC32 {o['crc32']}\n  MD5 {o['md5']}\n  SHA-1 {o['sha1']}\n"
            f"  Redump: http://redump.org/discs/quicksearch/{o['sha1']}\n"
            f"Patched .bin: size {b['size']}  CRC32 {b['crc32']}  SHA-1 {b['sha1']}")
    readme = (ROOT / "docs/README.template.txt").read_text(encoding="utf-8")
    (rel / "README.txt").write_text(readme.replace("{VERSION}", a.version).replace("{HASHES}", info)
                                    .replace("{PATCH}", patch.name), encoding="utf-8", newline="\r\n")
    with zipfile.ZipFile(z, "w", zipfile.ZIP_STORED) as zf:
        for f in sorted(rel.iterdir()):
            zf.write(f, f.name)
    print(z, f"patch sha1 {hashes(patch)['sha1']}")


if __name__ == "__main__":
    main()
