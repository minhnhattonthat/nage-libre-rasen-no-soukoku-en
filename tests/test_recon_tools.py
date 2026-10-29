"""Self-checks for the phase-1 recon tools (synthetic data; the disc-based checks skip when work/disc is absent)."""
import struct
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import tim  # noqa: E402
import textscan  # noqa: E402

TREE = ROOT / "work" / "disc" / "tree"


def make_tim(w=2, h=2):
    clut = struct.pack("<I4H", 12 + 16 * 2, 0, 480, 16, 1) + bytes(32)
    img = struct.pack("<I4H", 12 + w * h * 2, 0, 0, w, h) + bytes(range(w * h * 2))
    return struct.pack("<II", 0x10, 8) + clut + img


def test_tim_parse_and_scan_skip_garbage(tmp_path):
    t = make_tim()
    blob = b"\x10\x00\x00\x00junk" + t + b"\x10\x00\x00\x00\x09"
    p = tmp_path / "x.bin"
    p.write_bytes(blob)
    found = tim.scan(str(p))
    assert [x["off"] for x in found] == [8]
    assert (found[0]["bpp"], found[0]["w"], found[0]["h"]) == (4, 2, 2)
    assert tim.to_image(found[0]).size == (8, 2)


def test_textscan_needs_nul_and_kana():
    cs = {c.encode("cp932") for c in "あいう漢字"}
    data = b"\x01" + "あいう".encode("cp932") + b"\x00" + "漢字漢字".encode("cp932") + b"\x00" + "あいう".encode("cp932")
    runs = list(textscan.scan(data, cs, 2))
    assert [(o, r.decode("cp932")) for o, r in runs] == [(1, "あいう")]  # kanji-only and unterminated runs dropped


def test_textscan_codes_in_run():
    cs = {c.encode("cp932") for c in "樹いつき"}
    raw = "樹%h".encode("cp932") + "いつき".encode("cp932") + b"%z\n" + "樹".encode("cp932")
    assert list(textscan.scan(raw + b"\x00", cs, 2)) == [(0, raw)]


@pytest.mark.skipif(not (TREE / "NAGE.EXE").exists(), reason="needs the unpacked disc (work/disc/tree)")
def test_decomp_packed_tim_matches_game():
    import decomp
    d = (TREE / "OPENDATA.BIN").read_bytes()
    out = decomp.decompress(d[0x34:])
    t = tim.parse(out, 0)
    assert t and (t["bpp"], t["w"], t["h"], len(out)) == (8, 128, 256, 66080)
