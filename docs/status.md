# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 7 done 2026-10-30 (lint 0 errors, no `long` rows, every row English or in `script/keep_jp.txt`,
  romdiff + write log clean, no Japanese left in EXE text/records). Next: phase 8 (QA in the emulator).
  `build.py --markers` = marker build; plain `build.py` = VWF engine + names.asm + `en` rows.
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
  - Phase 7 (insert, fit, check; docs/re/vwf.md §Names, §EXE strings over their room): `tools/asm/names.asm`
    (Western name order + space via `NameSp` at all 7 two-part name prints, VS/status boxes 96 -> 112 px at x 8 /
    136, unconditional status newline, birthday name pen x 16 -> 8, save list `StageNum` = "Stage <n>");
    `insert.place_strings` relocates EXE strings over their room (49 rows; same lui half: tails, own slots,
    STRPOOL 0x8008A500..); every text write logged (`insert.WRITES`); `font.balanced_wrap` for dialogue (211 one-word
    last lines gone; lint fails a stub); `batches.py refit` moved all 65 `long` rows to `en` after the budgets
    changed (VS_PX 112, NAME rows 64, per-use battle-bar budgets); keep list `script/keep_jp.txt` (4 rows, lint
    fails any other jp row with no en); `tools/romdiff.py` + tests/test_build.py (romdiff with write log + asm
    .org sites, every English row written, refs land on the English, no kana/kanji in EXE text regions/records;
    record names zero the old string's tail). D11: "Council President", "'s Randoma Card, birthstone bonus!".
    Seen in game: VS boxes "Ann Akagi" (work/qa/vs), 105-px QA pair (work/qa/vs2), battle bar messages
    (work/qa/go2), birthday "Ann Akagi" + "3/15" (work/qa/p7/bz.png).
- **Phase 8 in progress (2026-10-30):** codex phase-6 review fixed (honorifics on nouns Pig-kun/Pig-san/Snowman-san,
  conquest/uniform gag, Great Tree route, glossary voice; `tests/test_terms.py` runs the term/honorific checks over all
  of script/). `tools/gfx.py` redraws TIM text (ops: clear by row-copy / row mode / colour with `keep` classes, text in
  the game font (`game`, bold/outline/shadow/scale) or Tiny5 (`tiny`)); `insert.build_files` writes every
  byte-identical copy. Done (graphics.md #): 6 loading board, 7 birthday, 8 birthstones, 9/10 load/save, 11 save
  titles (Tiny5: 128-px strips), 12 menu, 14 area cards (seen in game: wm06/13/31), 20 news ticker, 28 poster,
  1 title subtitle "Spiral Conflict", 15 "The End" (16bpp), 18/19 boss-intro 参上 "Here!" + name (rotated Tiny5,
  80 copies), 26 blackboard, 27 shrine board. Seen in game (work/qa/p8b): title, birthday, load, poster, battle.
  `python -X utf8 tools/gfx.py [--only NAME]` writes original|English previews to work/qa/gfx/out/; clear modes
  None (row copy from x-1), "mode", "lerp" (horizontal blend), int index, RGB; `keep` classes in gfx.KEEP.
  Packed entries: the loaders always call decomp, so `tools/asm/rle.asm` hooks decomp's entry: a block whose 2nd
  byte is 'R' goes to the game's own RLE decoder (0x80031388); `gfx.rle()` encodes (tested against the routine in
  unicorn), `gfx.join()` rebuilds the offset table, files stay within the 0x86800 RAM area (`gfx.AREA`, area table
  0x80089794). Done that way: #2-5 title (press start seen in game, work/qa/p8d), #16 cast plates (Tiny5).
  Also done: #13 dress-up labels (101), #21-24 town signs (PARK, FI|SH, Maiasa News, Grocer, Kiyoshi Drug,
  JA Nanju, Nanju Shops arch, Kobiro Race), #25 desk plate "Pres." (seen in game, work/qa/p8f). #17 kept as art
  (graphics.md §Phase 8). Every survey row is now handled.
- **Next (phase 8, QA in the emulator):**
  - Visual QA: `tools/debug/tour.py` (83 scenes, ~116 sheets) + `qa_gate.py`, brief `docs/visual-qa-brief.md`
    (standing non-bugs listed there). Round 1 fixed wm19 card, clear-condition wording, ellipses; a 1-px glyph
    bearing (for text flush at plate frames) was reverted in round 2. Round 3 found stale digit pixels on the
    club-select stats (numbers redraw in place; VWF moved them): digits are tabular (7 px) and the number printer
    (0x8003B7A0, mode 2) pads with '`', a blank digit-wide glyph (font.FIGURE; lint bans '`'). Birthstone plates
    clear their top row. Round 4 (build 109093b): 116/116 ok bar one orphan page (MAP08/189/022C, fixed 5fde8eb).
    Round 4 also showed the tour probe pressed circle mid-typing and skipped pages unshot (wm08 lost ~6); tourshot.lua
    now presses only once the text is stable. Round 5 = full re-tour (EN + JP) + review with the fixed probe; gate
    state in work/qa/manifest.tsv + verdicts/ (round 4 kept in work/qa/round4/). Town signs seen in the map01 tour.
    Open note: wm42 replays wm17 with slightly different wording (consistency, not a bug).
  - Memory-card title is English full-width (BIOS manager); Japanese-version saves load in the English build.
  - Release: `tools/release.py VERSION` (check, build, smoke, jp_left on NAGE.EXE/SYSDATA, qa_gate, xdelta3,
    re-apply, README from docs/README.template.txt, zip). Never `gh release create` (D9).
  - Seen: save to a blank formatted card and the load list "File 1 Stage 2 000:00" (work/qa/card; card images
    `work/saves/blank.mcd` = formatted empty (`python tools/debug/mkcard.py OUT.mcd`), `saved1.mcd` = one save; with a save on the card the title boots to
    LOAD, so warp.lua's New Game path doesn't fire: use them with plain routes, not warps).
  - VS plates seen (tour map02: "Flapper / Ann Akagi"). Not seen in game yet: field status box name order (0x80056B94,
    0x80057DFC), battle status box (0x80051804).
  - Check in game: choice rows translators laid out by hand (MAP14/193/0026 route choice, MAP21/199,
    MAP23/215/0002 Yes/No, MAP81/189/01BE..01E8), the composed item-use / club-change / level-up fragments
    (b020), description tag columns (/1 /All /Front /Back /Phys /Mind), 14 dialogue lines that page (lint --warn).
  - Budgets marked "window"/"guess" (item/magic lists, item use, club change, level up, field save, memory-card
    errors) get checked in phase 8 QA; adjust FIELDS if a shot disagrees.
  - Birthday screen: the full name now starts 8 px left of the portrait frame (cosmetic; needed for "Makoto
    Matsunaga" 98 px).
  - Current build/ = English build (sha1 f452e917…, 5fde8eb; regen 83/83 ok on the round-4 build); `build.py --markers` restores the marker
    build.
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
  Phase 7 (platform-ps1.md): armips `li`/`la` with a 32-bit value is lui + ori; in a branch/jal delay slot only
  the lui runs before the call (a1 = 0x80090000 printed garbage): load first, nop in the slot. Relocating MIPS
  strings without touching the lui: keep the new home in the same high half (`(addr + 0x8000) >> 16`) and rewrite
  only the addiu low half; a shared lui then stays right for every other use. Window frames may be drawn from the
  window rect (VS boxes widened fine) or be fixed art (battle bar: widening put text over the cap): compare a shot
  before trusting a wider create. PS1 engines that count 8-px cells (`s3` return of a print) for layout decisions
  break under VWF: grep the callers' use of the return value.
  Phase 8 (fonts/VWF): screens that redraw numbers in place without clearing (stat panels switching character)
  keep stale pixels once a VWF moves digits: give digits one advance and make the number printer's pad glyph that
  wide. A 1-px left bearing (to keep letters off a frame) did the same damage. Tours that mash one button land
  in sub-views the game leaves only with another (card view: cross); the shot-per-new-text probe keyed on the
  text texture's VRAM hash (tools/debug/tourshot.lua) kept 116 sheets for 83 scenes.
- **Waiting on the user:** The MAP01R boss-intro art names the boss レイプマン (a parody of the manga title); drawn
  literally as "Rapeman" (tools/gfx.py `sanjo_map`). Say if you'd rather have another name. Non-blocking.
  The TIME GAUGE art spells Jin's name "Zin" (Latin in the original art; glossary and script say Jin). Left as
  drawn; say if the art should be redrawn as "Jin" or the script should follow the art. Non-blocking.
  GUI keyboard input in `tools/pcsx/` is not proven (synthetic keystrokes did not reach the
  pad); owner asked for headless-only runs, so left; check by hand when playtesting. Non-blocking.
