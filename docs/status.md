# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 5 (engine spike + marker build) in progress 2026-10-30: VWF, insert pipeline, dialogue boxes
  measured, paging, marker build all done; menu/list field widths left (see Next). `build.py --markers` = marker
  build; plain `build.py` = VWF engine + any `en` rows.
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
  - Phase 5 (docs/re/vwf.md): `tools/insert.py` (script/ en or `[id]` markers -> MAPDAT/EXE/records/SYSDATA names
    under work/build/files; never writes work/disc/tree), `build.py` points a layout copy (work/build/layout.xml)
    at them, `--qa ID=TEXT` overrides one row. VWF: `tools/asm/vwf.asm` (armips, code in the unused half-width kana
    glyphs at 0x8008A0F4) + `tools/font.py` (game's own ASCII glyphs trimmed, advances; English = plain ASCII);
    tests/test_vwf.py runs it in unicorn. Boxes (`tools/boxes.py`): face 144 px x 4 lines, face3 144 x 3 (MAP85,
    MAP86), plain 224 x 4 (after op 17); rule = last op 16/17, matched 484/484 lines seen in a tour
    (`debug/winlog.lua` + `debug/winscan.py`). Wrap to width-1 px, pages joined by `%k%p` (button wait + clear;
    verified 4 pages in-game). Lines of exactly 143/223 px fully visible (work/qa/mk/edge.png, plain.png).
    `tools/lint.py` in check.py (no glyph, colour codes, field bytes, word wider than box; --warn: pages).
    Limits found: SYSDATA buffer 0xC000 (names may grow 1,863 bytes in all; 10-byte name markers hung New Game),
    EXE in-place room = own bytes + alignment only (`extract.exe_room`; filling $gp-area zeros hung the load).
    Lengthened scripts play and grown MAPDATs load (MAP24 502 KB). Marker build = `[map.slot.off]` + filler
    filling each box to its last line; fixed fields `E00BE8MMM` / `I03nameMMM` (wide M to the field's bytes);
    names `N000MM`.
- **Next (phase 5, to meet its done-when = the width gate for menus/labels):**
  - Measure every non-dialogue text place from marker shots and record budgets (px, and lines) beside
    `boxes.BOXES` (add a `FIELDS` table: row-id pattern -> px, measured/guess + shot): battle command menu
    (EXE/00BE8-00C68), battle VS box (name / club / school lines, ~96 px: work/qa/menutour/vs.png, measure exactly),
    battle messages (EXE/01B6C-01D1C, composed `name + string`), item / magic names and descriptions (ITEM/MAGIC
    records: dressup, item use), club names (CLUB, EXE/013A0-01448, 809FC-80A4C), status labels (EXE/80AC0-80BB8,
    02B38), memory-card / save texts (EXE/01E6C-02B24: save, load, save_after_m80 scenes), dressup lines
    (EXE/02510-0255C), level-up texts (EXE/02458-024B8). Shots so far: work/qa/menutour/<scene>/ (battle, dressup,
    club_select, save, load, gameover, birthday, credits, menu); `--qa ID=TEXT` for a long line in one field.
    Then make lint.py check those rows against their budgets (warn "no measured budget" for any row without one).
  - Marker build (sha1 102a2225…, 2026-10-30): smoke ok, cold-boot regen 83/83 scenes ok
    (`regen.py --cue build/nage_libre_en.cue --no-states --out work/qa/marker`). Rerun after engine changes.
  - Then phase 6 (translate): translators get box budgets from boxes.py (face 143 px x 4, face3 x 3, plain 223 x 4;
    pages beyond are automatic but soft-limited), plain ASCII only, no `\` or bare `%`.
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
  Phase 5 (platform-ps1.md): a file's RAM budget can come from a {addr, size} memory-area table in the EXE, far
  tighter than the gap to the next known load address (SYSDATA: 0xC000, not 0x18000); grep the EXE for the load
  address as a 32-bit word before growing a file. Zero runs after strings in a $gp data area are variables, not
  free room. armips warns on a load-delay hazard (`lw t9` then `bne t9`): R3000 needs the nop.
- **Waiting on the user:** GUI keyboard input in `tools/pcsx/` is not proven (synthetic keystrokes did not reach the
  pad); owner asked for headless-only runs, so left; check by hand when playtesting. Non-blocking.
