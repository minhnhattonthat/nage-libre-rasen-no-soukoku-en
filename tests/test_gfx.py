"""Graphics text redraws (tools/gfx.py): every element builds, every area card has its English, each edit lands."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import extract  # noqa: E402
import gfx  # noqa: E402


def test_areas_cover_every_card():
    assert len(gfx.AREAS) == 25  # OPTION7.BIN cards 0x3D6A0 + n * 0x1620


def test_build_changes_every_element():
    files, previews = gfx.build_gfx(extract.TREE)
    assert len(previews) == len(gfx.ELEMENTS)
    for name, before, after in previews:
        assert before.tobytes() != after.tobytes(), f"{name}: no pixel changed"
    assert all(len(files[r]) == (extract.TREE / r).stat().st_size for r in files)  # in-place edits only
