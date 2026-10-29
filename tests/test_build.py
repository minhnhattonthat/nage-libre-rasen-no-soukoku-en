"""Insert build checks (pipeline §Checks): every NAGE.EXE byte that changes comes from a logged write or an asm
hook site (romdiff --writes), each logged write found the original bytes it expected, every row with English
was written, and every relocated string's refs point at it."""
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import insert  # noqa: E402
import romdiff  # noqa: E402

TREE = ROOT / "work/disc/tree"
pytestmark = pytest.mark.skipif(not (TREE / "NAGE.EXE").exists() or not insert.ARMIPS.exists(),
                                reason="needs work/disc and armips")
CODE_AREA = (0x80089B5C, insert.STRPOOL[0])  # half-width font rows, widths, VWF + names.asm code


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    out = tmp_path_factory.mktemp("files")
    files = insert.build_files(TREE, out)
    return files, list(insert.WRITES), dict(insert.RELOCATED)


def asm_sites():
    """File offsets the asm may change: 8 bytes at each hook .org below the font, and the code area."""
    ok = set(range(CODE_AREA[0] - insert.RAM, CODE_AREA[1] - insert.RAM))
    for asm in insert.ASM:
        for m in re.finditer(r"^\.org (0x[0-9A-Fa-f]+)", asm.read_text(encoding="utf-8"), re.M):
            a = int(m.group(1), 16)
            if a < CODE_AREA[0]:
                ok.update(range(a - insert.RAM, a - insert.RAM + 8))
            elif a >= insert.STRPOOL[1]:  # rle.asm's hook after the string pool, up to the data at 0x8008A97C
                ok.update(range(a - insert.RAM, 0x8008A97C - insert.RAM))
    return ok


def test_exe_changes_are_logged_or_asm(built):
    files, writes, _ = built
    orig = (TREE / "NAGE.EXE").read_bytes()
    new = Path(files["NAGE.EXE"]).read_bytes()
    log = [(o, a, b, by) for f, o, a, b, by in writes if f == "NAGE.EXE"]
    errs, _ = romdiff.check(orig, new, asm_sites(), log)
    assert errs == []


def test_every_english_row_is_written(built):
    _, writes, _ = built
    by = {w[4] for w in writes}
    for name in ("exe.json", "records.json"):
        missing = [r["id"] for r in insert.load_rows(name) if r.get("en") and r["id"] not in by]
        assert missing == [], f"{name}: rows with English not written"


SJIS_JP = re.compile(rb"(?:\x82[\x9f-\xf1]|\x83[\x40-\x96]|[\x88-\x9f\xe0-\xea][\x40-\xfc]){2,}")  # kana, kanji


def test_no_japanese_left_in_exe_text(built):
    """jp_left for the EXE's text areas (string regions, record tables): only keep_jp.txt rows may stay."""
    import extract
    files, _, _ = built
    new = Path(files["NAGE.EXE"]).read_bytes()
    keep = {l.split()[0] for l in (ROOT / "script/keep_jp.txt").read_text(encoding="utf-8").splitlines()
            if l.strip() and not l.startswith("#")}
    kept = set()
    for r in insert.load_rows("exe.json"):
        if r["id"] in keep:
            o = int(r["id"].split("/")[1], 16)
            kept.update(range(o, o + r["max"] + 1))
    o, n = extract.MEMCARD
    kept.update(range(o, o + n))
    spans = list(extract.EXE_REGIONS) + [(base, base + size * count) for _, base, size, count, _ in extract.TABLES]
    left = [(hex(lo + m.start()), m.group().decode("cp932", "replace")) for lo, hi in spans
            for m in SJIS_JP.finditer(new[lo:hi]) if lo + m.start() not in kept]
    assert left == []


def test_relocated_refs_point_at_the_english(built):
    files, _, moved = built
    new = Path(files["NAGE.EXE"]).read_bytes()
    rows = {r["id"]: r for r in insert.load_rows("exe.json")}
    assert moved
    for rid, addr in moved.items():
        o = addr - insert.RAM
        want = insert.encode(insert.fit_field(rid, rows[rid]["en"]))
        assert new[o:o + len(want) + 1] == want + b"\0", rid
        for ref in rows[rid]["refs"]:
            site = int(ref.split(":")[1], 16) - insert.RAM
            assert int.from_bytes(new[site:site + 2], "little") == addr & 0xFFFF, (rid, ref)
