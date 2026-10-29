import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import check_rom  # noqa: E402


def test_rom_sha1_listed():
    lines = [l for l in (ROOT / "rom.sha1").read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
    assert lines and all(len(l.split(None, 1)[0]) == 40 for l in lines)


@pytest.mark.skipif(not (ROOT / "rom").is_dir(), reason="no rom/ dump")
def test_rom_matches():
    check_rom.check()
