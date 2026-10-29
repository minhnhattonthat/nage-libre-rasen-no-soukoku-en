# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 6 done 2026-10-30 (all 22 batches check 0 errors, reviewed, Critical/Important fixed, merged into
  `script/`; glossary updated). Next: phase 7 (insert, fit, check). `build.py --markers` = marker build; plain
  `build.py` = VWF engine + `en` rows.
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
  - Phase 5 fields (docs/re/vwf.md §Fields): `boxes.FIELDS` = px/lines per EXE/record/name row range, each
    marked measured / window / guess with its evidence; `boxes.fit()` + `insert.fit_field()` add the trailing `\n`
    menu items need (items end by auto-wrap at 40 px) and word-wrap multi-line windows; lint errors on px/lines
    over, warns on a row with no budget; tests/test_insert.py (every row has a budget, fit_field). Tools:
    `tools/wincreate.py` (all 38 window creates), `tools/debug/fieldlog.lua` + `fieldscan.py` (print log -> rows,
    start x, room), `tools/debug/stateat.lua` (state at a string's first print: menu routes), warp.lua `STAY=1`.
    Verified in-game with English (`--qa`, work/qa/fq): command menu + sub-menu, birthday name/date, save/load list,
    yes/no.
  - Phase 6 (translate): `tools/batches.py` (split -> work/tl/bNNN.tsv with speaker from op 16/2B face ids
    1-5 = Ann/Itsuki/Makoto/Shinobu/Mio, check, merge, pairs for reviewers; escapes `\n`, `\s`, `=JP`), briefs
    `docs/{translator,reviewer}-brief.md`, `docs/style-reference.md`, `docs/synopsis.md`, glossary (~130 rows,
    check-enforced, honorifics kept). Pilot b001 (intro + MAP01) by the controller, seen in-game. 21 batches by 6
    translator agents (opus), 7 reviewer passes (sonnet): no Critical; Important fixed per batch (puns, split
    sentences, per-girl voices, term drift grimoire/spellbook etc.). All 3,357 dialogue rows, 177 EXE, 145
    records, 695 names translated. Minor review notes not applied (polish pass later; reports were returned in
    session, only Important ones kept in work/review/fixes_*.md, gitignored).
- **Next (phase 7, insert, fit, check):**
  - 65 field rows carry `long` (full English wider than its FIELDS budget; `en` empty so the build keeps
    Japanese; `lint --warn` lists them): 49+9 NAME rows over 48 px (Matsunaga 56, Kurosawa 50, Monster A-I 54 ..
    Kazamatsuri 64), EXE/013E0 Student Council President (136 px in 96), 013F8 Super Go-Home Club, 01BB4/01C50
    Randoma Card + birthstone bonus (128 px), 024E0 Makoto Matsunaga (98 in 96). Engine first (D4): the 48-px
    NAME budget is per part for composed lines (two names in 224 px); the VS box has 96 px for surname + given
    name, so a measured per-use budget, a smaller font or a wider field likely fixes most. Then move `long` to `en`.
  - EXE strings over their in-place room (`lint --warn` "bytes, room"): insert keeps Japanese (build prints the
    count, `insert.SKIPPED`); relocate them through their `refs` (lui/addiu, $gp, words).
  - EXE/80BCC 面 = "St" follows a number on the save list ("3St"): needs the number/label order changed or a
    wider label ("Stage 3"). EXE/80BD0/80BD4 月/日 -> "/" and "." (birthday "3/15.") likewise.
  - Names: VS/status box line 1 prints surname then given name (NAME rows); Western order (D1) needs a code swap
    or the slots' text swapped.
  - Check in game (phase 8): choice rows translators laid out by hand (MAP14/193/0026 route choice, MAP21/199,
    MAP23/215/0002 Yes/No, MAP81/189/01BE..01E8), the composed item-use / club-change / level-up fragments
    (b020), description tag columns (/1 /All /Front /Back /Phys /Mind), 14 dialogue lines that page (lint --warn).
  - Budgets marked "window"/"guess" (item/magic lists, item use, club change, level up, field save, memory-card
    errors) get checked in phase 8 QA; adjust FIELDS if a shot disagrees.
  - Current build/ = English build from script/ (sha1 2c1610f2…, smoke ok; 44 EXE strings and the `long` rows
    still Japanese); `build.py --markers` restores the marker build (sha1 102a2225…, regen 83/83 ok).
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
  Phase 5 fields: Git Bash rewrites an argument that is or starts with `/` into a Windows path (`--qa ID=/` became
  `C:/Program Files/Git/`): `export MSYS_NO_PATHCONV=1` first. Menus that end items by auto-wrap (Japanese padded
  to the window width) need a `\n` per English item. PCSX-Redux exec hooks read args as
  `PCSX.getRegisters().GPR.n.a0`.
  Phase 6 (translation.md): a portrait/face op that persists (op 16) is not the speaker: a second op (2B face,
  expression) swaps faces mid-scene; speaker columns from op 16 alone mislabelled most lines. Translator agents
  report that Write/Edit strip trailing spaces from TSV rows: give the output format an escape (`\s`) and a
  keep-original value (`=JP`). Field rows wider than a guessed budget need a "deferred" state (here `long`) so the
  check can reach 0 errors without abbreviating (D4). Glossary checks must skip a kanji term inside a longer
  compound (魔物 in 邪魔物) and accept the honorific after the full name (Kaoru Kanzaki-san).
- **Waiting on the user:** GUI keyboard input in `tools/pcsx/` is not proven (synthetic keystrokes did not reach the
  pad); owner asked for headless-only runs, so left; check by hand when playtesting. Non-blocking.
