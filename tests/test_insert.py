"""English insertion: pixel wrap, paging, box rule, marker build (docs/re/vwf.md)."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import boxes  # noqa: E402
import font  # noqa: E402
import insert  # noqa: E402
import script as sc  # noqa: E402

TREE = ROOT / "work/disc/tree"
needs_disc = pytest.mark.skipif(not TREE.exists(), reason="needs work/disc")


@needs_disc
def test_wrap_fits_and_keeps_words():
    s = "The quick brown fox jumps over the lazy dog. " * 6
    lines = font.wrap(s.strip(), 143)
    assert all(font.advance(l) <= 143 for l in lines)
    assert " ".join(lines) == s.strip()
    assert font.wrap("a\nb", 143) == ["a", "b"]


@needs_disc
def test_advance():
    assert font.advance("i") == 2 and font.advance("m") == 8 and font.advance(" ") == 4
    assert font.advance("%c02ii%k%p") == 4  # control codes take no width


def test_paginate():
    assert insert.paginate(list("abcde"), 2) == "a\nb%k%pc\nd%k%pe"
    assert insert.paginate(["x"], 4) == "x"


@needs_disc
def test_box_rule_counts():
    rows = boxes.all_rows()
    assert len(rows) == 4088 and set(rows.values()) == {"face", "face3", "plain"}


@needs_disc
def test_marker_build(tmp_path):
    files = insert.build_files(TREE, tmp_path, markers=True)
    assert "NAGE.EXE" in files and "SYSDATA.BIN" in files
    for rel, p in files.items():
        if rel.endswith("MAPDAT.BIN"):
            _, _, scripts = sc.scripts(p)
            for b in scripts.values():
                assert sc.check_script(b) == []
                assert all(t.isascii() for t, _, _ in sc.strings_of(b).values())
