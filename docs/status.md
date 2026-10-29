# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 4 (extract) done 2026-10-30. Next: phase 5 (engine spike + marker build). Build = untouched repack
  (sha1 7ccae6f0…, same as the dump), smoke ok.
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
  - Phase 3: `tools/build.py` (check_rom, `unpack()` = dumpsxiso into `work/disc/` on first run, `pack()` = mkpsxiso
    `work/disc/layout.xml` -> `build/nage_libre_en.bin/.cue`). `tests/test_identity.py` unpacks into a temp dir and
    repacks: sha1 equals `rom.sha1` (~2 s, runs in the pre-commit check). mkpsxiso 2.30 rebuilds EDC/ECC and the
    150-sector trailing dummy exactly; no layout tweaks needed.
  - Phase 4: `tools/script.py` (opcode length table from all 80 handlers, flow parse from offset 0 + dead-code pass,
    `rebuild()` remaps every jump/string/data offset, `rebuild_mapdat()` shifts the offset table), `tools/text.py`
    (byte-exact SJIS codec, control codes as ASCII), `tools/extract.py` -> `script/` (format `docs/text-format.md`):
    4,088 dialogue lines in 46 map files (731 marked `same` in revisit maps, 69 `dead`), 178 EXE system strings
    (each with its code refs), 146 table fields (10 clubs, 25 items x name/desc at 0x47 stride, 56 magic/effects at
    0x4C, memory-card title), 696 names. `tests/test_extract.py` (12 tests, ~4 s): codec over all bytes, script/ ==
    fresh extraction, every MAPDAT rebuilt byte-exact from jp, all 802 scripts parse/cover/stretch-rebuild, textscan
    finds no MAPDAT text outside lines, EXE regions = strings + reviewed `EXE_DATA`, no other font text in NAGE.EXE,
    records and names roundtrip. `tools/re.py` renamed `tools/mips.py` (shadowed stdlib `re`; adds `refs()`).
- **Next (phase 5, engine spike + marker build):**
  - build.py edit step: write edited files into a copy (never `work/disc/tree`, which tests read) and give mkpsxiso a
    layout copy pointing at them; an insert step that takes `script/` en (or markers) through `text.py`/`script.py`.
  - Font decision: 1,386-cell 16x13 SJIS font in SYSDATA #3; English needs narrow Latin glyphs or a VWF in the
    renderer (0x8003BFF4..; `%h` half-width mode already draws at half advance: test it with ASCII first).
    Auto line wrap by box width (face box 9 full-width chars x 3 lines).
  - Marker build: every line `[id]` text; prove a lengthened script plays (offset remap, no outside pointer into
    scripts) and that a grown MAPDAT loads (RAM ceiling ~589 KB, docs/re/files.md). EXE strings grow only by
    relocation through their `refs` (lui pairs / words; `gp:` refs can't move). Records have fixed fields (`max`).
  - Then a text lint in `tools/check.py` (control codes kept, `max` bytes, leading/trailing blanks) once the English
    encoder exists.
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
  own final shot, so emu.py reports `final NO` (harmless). A repo helper named `tools/re.py` shadows stdlib `re`
  for any script run from `tools/` (renamed `mips.py`): template/skill helper names should avoid stdlib names.
- **Waiting on the user:** GUI keyboard input in `tools/pcsx/` is not proven (synthetic keystrokes did not reach the
  pad); owner asked for headless-only runs, so left; check by hand when playtesting. Non-blocking.
