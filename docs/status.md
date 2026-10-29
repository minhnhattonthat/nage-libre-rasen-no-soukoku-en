# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 2 (debug tool) done 2026-10-30. Next: phase 3 (identity build). No build yet.
- **Done:**
  - Step 0: dump pinned (`rom.sha1`), tools in `tools/`, headless smoke on the original, pre-commit check, guard hook.
  - Phase 1 (notes in `docs/re/`): Shift-JIS text; own font in SYSDATA.BIN (1,386 cells, 16x13, charset list);
    control codes `\n`, `%h`/`%z` (half-width), `%c02`; dialogue = inline strings in MAPDAT event scripts
    (entries 186-216, jump targets are u16 offsets from script start, 80-opcode table at 0x8008CD74); system text,
    item/magic records (0x47 bytes) in NAGE.EXE; names in SYSDATA #7; offset-table containers; packed-block codec
    run via `tools/decomp.py` (unicorn); graphics survey of 28 Japanese image elements (`docs/re/graphics.md`).
  - Phase 2: `tools/debug/warp.lua` + `scenes.lua` (83 scenes) + `regen.py` (all scenes from cold boot, checks,
    states in `work/states/`, sheet `work/qa/warp/all*.png`). RAM map in `docs/re/state.md`: map byte 0x80090276,
    entry 0x80090277, mode 0x80090B28, fade callback 0x80090C60 (the warp swaps New Game's next-map callback for a
    loader). Scenes: title, birthday entry, load, between-stage menu, club select, dress-up, save (menu and mode 6),
    cutscene after MAP24, ending + credits, battle, game over (Ann at 1 HP), 25 world-map area cards, all 46 MAPnn
    folders (MAPDAT in RAM checked against the file). `GOD=1` pins party HP.
- **Next (phase 3, identity build):** `dumpsxiso`/`mkpsxiso` layout in `work/disc/layout.xml`; `tools/build.py`
  repacks with no edits and a test proves the .bin is byte-identical (check `rom.sha1` first). Then phase 4 needs an
  opcode length table from the 80 handlers (0x8005E49C..0x80060854) to re-encode scripts.
- **Debug-tool limits (grow when needed):** map scenes play each map's first event with new-game story flags; the
  later events of a map (other script slots 186-216, flag-dependent branches) are not forced yet. For phase 8,
  add per-script warps: set the script base `$gp`+0x52C / PC `$gp`+0x2A2 (docs/re/text.md) or the story flags at
  0x80105B54.. (docs/re/state.md, guessed). The battle scene is the first MAP02 fight (defend turn); battles on
  other maps need the same `mash_until` on their map.
- **Open bugs:** none.
- **Gotchas found (for the skill):** PCSX-Redux nightly 29942 `PCSX.GPU.getVRAM()` returns 2 MB, not 1 MB (first 1 MB
  is VRAM; pcsx_lib.lua comment says 1 MB). Unicorn MIPS translates kseg0 0x80000000 to physical for fetch and data:
  map RAM at 0 and stop on a code hook (the `until` address is missed after jr + delay slot). PCSX-Redux Lua has
  stock `io.open` (read disc files from a warp script); `L.finish()` from a script ends the run before emu.py's
  own final shot, so emu.py reports `final NO` (harmless).
- **Waiting on the user:** GUI keyboard input in `tools/pcsx/` is not proven (synthetic keystrokes did not reach the
  pad); owner asked for headless-only runs, so left; check by hand when playtesting. Non-blocking.
