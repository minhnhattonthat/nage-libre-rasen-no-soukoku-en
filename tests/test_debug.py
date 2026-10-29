"""Scene list sanity for the debug warp (tools/debug/scenes.lua); the disc check skips when work/disc is absent."""
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "debug"))

import regen  # noqa: E402

TEXT = (ROOT / "tools/debug/scenes.lua").read_text(encoding="utf-8")
MAPS = ROOT / "work/disc/tree/MAP01_06"


def test_scene_names_unique_and_complete():
    names = regen.scene_names(TEXT)
    assert len(names) == len(set(names))
    assert {"title", "battle", "gameover", "credits", "menu", "save", "load", "birthday", "dressup"} <= set(names)
    assert sum(n.startswith("wm") for n in names) == 25          # one per area card (0x8008D178)
    assert "then_after" not in names and "t" not in names


@pytest.mark.skipif(not MAPS.exists(), reason="work/disc not unpacked")
def test_every_map_folder_has_a_scene():
    dirs = set(re.findall(r'dir = "(MAP\w+)"', TEXT))
    on_disc = {p.name for p in MAPS.iterdir() if (p / "MAPDAT.BIN").exists()}
    assert on_disc == dirs, (on_disc - dirs, dirs - on_disc)
