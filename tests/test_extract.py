"""Phase 4: every extracted string re-encodes to the original bytes (roundtrip), the text ranges are fully covered,
and the event-script re-encoder keeps every script's program intact when strings change length."""
import struct
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import extract  # noqa: E402
import script as sc  # noqa: E402
import text  # noqa: E402
import textscan  # noqa: E402
from sweep_packed import table  # noqa: E402

TREE = extract.TREE
pytestmark = pytest.mark.skipif(not (TREE / "NAGE.EXE").exists(), reason="needs the unpacked disc (tools/build.py)")


@pytest.fixture(scope="module")
def committed():
    return {p.relative_to(extract.OUT).as_posix(): extract.load(p) for p in extract.OUT.rglob("*.json")}


@pytest.fixture(scope="module")
def exe():
    return (TREE / "NAGE.EXE").read_bytes()


def test_codec_roundtrip_all_bytes():
    raw = bytes(range(256)) + "漢字かなカナ％\n[".encode("cp932") + b"\x87\x40\xed\x40\xfa\x40"
    assert text.encode(text.decode(raw)) == raw


def test_script_files_match_disc(committed):
    """script/ holds exactly what the extractor gets from the disc (ids and jp); en is the translators'."""
    fresh = extract.extract_all(TREE)
    assert set(committed) == set(fresh)
    for rel, rows in fresh.items():
        assert [(r["id"], r["jp"]) for r in committed[rel]] == [(r["id"], r["jp"]) for r in rows], rel


def test_maps_roundtrip(committed):
    """Re-encode every jp line through the script re-encoder: each MAPDAT comes back byte for byte."""
    for path in extract.map_files(TREE):
        d, _, scripts = sc.scripts(path)
        texts = {}
        for r in committed[f"maps/{path.parent.name}.json"]:
            _, slot, off = r["id"].split("/")
            texts.setdefault(int(slot), {})[int(off, 16)] = text.encode(r["jp"])
        new = {s: sc.rebuild(b, texts.get(s, {})) for s, b in scripts.items()}
        assert sc.rebuild_mapdat(d, new) == d, path


def test_scripts_parse_cover_and_stretch():
    """Every script parses from offset 0, no Japanese is left in bytes the parser does not account for, and a
    rebuild with every string made longer gives the same program with all jump/string/data offsets remapped."""
    bad = []
    for path in extract.map_files(TREE):
        for slot, b in sc.scripts(path)[2].items():
            bad += [f"{path.parent.name}/{slot}: {p}" for p in sc.check_script(b)]
    assert not bad


def test_mapdat_text_only_in_scripts(committed):
    """Cross-check with the charset scanner: every text run it finds in a MAPDAT is inside an extracted line."""
    cs = textscan.charset(str(TREE))
    for path in extract.map_files(TREE):
        d, t, scripts = sc.scripts(path)
        spans = []
        for slot, b in scripts.items():
            for off, (raw, kind, _) in sc.strings_of(b).items():
                s = t[slot] + off + (2 if kind == "inline" else 0)
                spans.append((s, s + len(raw)))
        for off, raw in textscan.scan(d, cs, 2):
            s = raw.decode("cp932", "replace")
            if off < t[sc.FIRST]:  # map blocks: graphics bytes that happen to decode; never real words
                assert sum("ぁ" <= c <= "ん" or "一" <= c <= "鿿" for c in s) <= 1, f"{path.parent.name} {off:#x} {s}"
            else:
                assert any(a <= off < e for a, e in spans), f"{path.parent.name} {off:#x} {s}"


def test_exe_strings_roundtrip(committed, exe):
    for r in committed["exe.json"]:
        o = int(r["id"].split("/")[1], 16)
        raw = text.encode(r["jp"])
        assert exe[o:o + len(raw) + 1] == raw + b"\0", r["id"]
        assert len(raw) <= r["max"]


def test_exe_regions_covered(exe):
    """Each run in the EXE text regions is either an extracted string or a reviewed data run (EXE_DATA)."""
    pieces = extract.exe_pieces(exe)
    assert {s for s, _, is_text, _ in pieces if not is_text} == set(extract.EXE_DATA)
    for s, raw, is_text, refs in pieces:
        assert not is_text or refs, f"{s:#x} has no code reference"


def test_no_exe_text_outside_known_places(exe):
    """No NUL-bounded run of 3+ font characters anywhere in NAGE.EXE outside the string regions, tables and
    memory-card title (2-character runs are common in MIPS code)."""
    cs = {c for c in textscan.charset(str(TREE)) if 0x81 <= c[0] <= 0xFC}  # the charset list is padded with 00/FF
    known = list(extract.EXE_REGIONS) + [(b, b + size * n) for _, b, size, n, _ in extract.TABLES]
    known += [(extract.MEMCARD[0], extract.MEMCARD[0] + extract.MEMCARD[1]), (0x7B6E8, 0x7B6FC)]  # + digit glyph list
    i = 0
    while i < len(exe):
        j, wide = i, 0
        while j + 1 < len(exe) and exe[j:j + 2] in cs:
            j += 2
            wide += 1
        if wide >= 3 and exe[i - 1] == 0 and exe[j] == 0 and not any(a <= i < b for a, b in known):
            pytest.fail(f"font text at {i:#x}: {exe[i:j].decode('cp932', 'replace')}")
        i = j + 1 if j > i else i + 1


def test_records_roundtrip(committed, exe):
    rows = {r["id"]: r for r in committed["records.json"]}
    for name, base, size, count, fields in extract.TABLES:
        for i in range(count):
            for field, off, n in fields:
                o = base + i * size + off
                r = rows.get(f"{name}/{i:02d}/{field}")
                raw = text.encode(r["jp"]) if r else b""
                assert exe[o:o + len(raw)] == raw and not any(exe[o + len(raw):o + n]), f"{name}/{i}/{field}"
    o, n = extract.MEMCARD
    assert exe[o:o + n] == text.encode(rows["MEMCARD"]["jp"])


def test_names_roundtrip(committed):
    block = extract.names_block(TREE)
    joined = b"\r\n".join(text.encode(r["jp"]) for r in committed["names.json"])
    assert block[:len(joined)] == joined and block[len(joined):] == b"\xff\xff\xff\xff\x1a\0\0"


def test_rebuild_remaps_offsets():
    """Synthetic script: a goto over a longer inline string still lands on its target, and odd text gets padded."""
    msg = "あい".encode("cp932")
    b = struct.pack("<HH", 0x01, 0x0C) + struct.pack("<H", 0x1D) + msg + b"\0\0" + struct.pack("<HH", 0x0B, 0x0B)
    parsed = sc.parse(b)
    assert sorted(parsed[0]) == [0, 4, 0x0C, 0x0E]
    out = sc.rebuild(b, {4: b"abc"})
    assert out == struct.pack("<HH", 0x01, 0x0A) + struct.pack("<H", 0x1D) + b"abc\0" + struct.pack("<HH", 0x0B, 0x0B)
    assert sc.parse(out)[0][4].text == b"abc"


def test_rebuild_mapdat_shifts_table():
    d = bytearray(struct.pack(f"<{217}I", *([217 * 4] * 186 + [217 * 4 + 4 * k for k in range(31)])))
    d += b"\x1a\0\0\0" * 31
    new = sc.rebuild_mapdat(bytes(d), {186: b"\x0b\0\x0b\0\x0b\0\x0b\0"})
    t = table(new)
    assert new[t[186]:t[187]] == b"\x0b\0" * 4 and t[187] == t[186] + 8 and new[t[187]:t[188]] == b"\x1a\0\0\0"
