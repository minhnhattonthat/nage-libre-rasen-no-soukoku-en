"""Graphics text redraws (tools/gfx.py): every element builds, every area card has its English, each edit lands."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import extract  # noqa: E402
import gfx  # noqa: E402


def test_rle_decodes_with_the_games_routine():
    import decomp
    for data in (bytes(300) + b"\x01\x02\x02\x02\xff\xff" + bytes(range(256)) * 2 + b"\x07" * 129, b"\xff" * 5, b"ab"):
        assert decomp.decompress(gfx.rle(data)[2:], 0x80031388) == data


def test_no_packed_block_looks_like_rle():
    """rle.asm routes a block whose second byte is 'R' to the RLE decoder: no original packed block may have it."""
    for rel, p in gfx.tree_files(extract.TREE):
        d = p.read_bytes()
        try:
            blocks = gfx.entries(d)
        except Exception:
            continue
        if any(b[:1] and b[1:2] == b"\x00" and b[2:6] == bytes.fromhex("10888098") for b in blocks):  # has packed
            assert not any(b[1:2] == b"R" for b in blocks), rel


def test_areas_cover_every_card():
    assert len(gfx.AREAS) == 25  # OPTION7.BIN cards 0x3D6A0 + n * 0x1620


def test_build_changes_every_element():
    files, previews = gfx.build_gfx(extract.TREE)
    assert len(previews) == len(gfx.ELEMENTS)
    for name, before, after in previews:
        assert before.tobytes() != after.tobytes(), f"{name}: no pixel changed"
    packed = {rel for _, rel, off, _ in gfx.ELEMENTS if isinstance(off, tuple)}
    for r in files:  # raw TIMs are edited in place; re-encoded entries keep their file inside its RAM area
        assert len(files[r]) <= gfx.AREA if r in packed else len(files[r]) == (extract.TREE / r).stat().st_size, r
