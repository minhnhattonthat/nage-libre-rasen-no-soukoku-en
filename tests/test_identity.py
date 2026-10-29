"""Identity build: a fresh dumpsxiso unpack repacked by mkpsxiso with no edits gives the original .bin bit for bit."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build  # noqa: E402


@pytest.mark.skipif(not build.CUE.exists() or not build.MKPSXISO.is_dir(), reason="needs rom/ and tools/mkpsxiso")
def test_identity(tmp_path):
    lines = (ROOT / "rom.sha1").read_text(encoding="utf-8").splitlines()
    want = next(l.split()[0] for l in lines if l.strip() and not l.startswith("#") and l.rstrip().endswith(".bin"))
    build.unpack(tmp_path / "disc")
    assert build.pack(tmp_path / "id.bin", tmp_path / "disc") == want
