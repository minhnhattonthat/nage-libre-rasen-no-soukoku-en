# English text engine: VWF, boxes, wrapping (phase 5)

Addresses are RAM (NAGE.EXE file offset = addr - 0x80010000 + 0x800).

## Renderer (original)

- Window table at 0x800AD89C, stride 0x1C, 5 windows (create 0x8003DB60(x, y, wpx, hpx, ...)): +0 x, +2 y, +4 width
  px, +6 height px, +8 W = width/8 (wrap limit, 8-px units), +A lines = (height+3)/16, +C pen x, +E pen y,
  +10 line gap (3), +12 `%t` value, +13 `%c` colour, +16 half-width flag (`%h`), +17 "just auto-wrapped" (a `\n`
  right after an auto-wrap is skipped), +1A active. Text runs at 0x800AD92C + 16*j: window index, +8 string
  pointer (0 = idle), +-0xC position. **verified** (tools/debug/winlog.lua on the marker build).
- Each window's text is drawn into its own 4bpp VRAM texture at (0x280 + x/4, 0x100 + y) (cleared at create).
  Typewriter loop 0x8003BF80.., instant print 0x8003B288 (used by op 19 for the speaker line, menus).
- Glyph lookup 0x8003F26C(ptr, half flag): SJIS -> charset index (+500 = full width, 16x13 from SYSDATA #3); in `%h`
  mode an index < 0x120 stays < 500 (half width). A single byte (ASCII, half-width kana) -> its position in
  SYSDATA #5, < 500. **verified** (ASCII markers draw half width with no `%h`).
- Draw 0x8003C778(glyph, x, y, colour): >= 500 -> 0x8003C94C (16 px), returns 1, callers add 16; < 500 ->
  0x8003CBE0: half-width font in NAGE.EXE at 0x80089B5C (8x13, 13 bytes per glyph, MSB = left, bit 0 never drawn),
  278 glyphs (ASCII at 0-92/94, space 277, kana 97-276); returns 0, callers add 8. Upload: ring of 100 slots at
  0x8009E86C + counter($gp+0xBD4)*240 + frame(0x80090858)*120, LoadImage 0x800750C4. Callers: 0x8003C494
  (typewriter), 0x8003B648 (instant). Auto wrap after a glyph when pen x >= 8*W.
- 0x8008A97C.. (right after glyph 277's 11th row) is data with code refs: the font area ends there.

## VWF (tools/asm/vwf.asm + tools/font.py)

- Half-width glyphs are now drawn at any pixel x: `VwfHalf` (code at 0x8008A0F4, in the unused half-width kana
  glyphs) shifts the glyph by x & 3 inside 1-3 VRAM units (4 px each), ORs in the units the previous glyph left on
  the same row (kept at 0x8008A09C: last x, y, 13 rows x 3 units) and uploads only the units up to its last inked
  column, so a rect never passes the box's right edge. Carry applies only when y matches and x is right of the
  last glyph (a new message or line resets it). Returns -advance; the callers' `beqz v0` became `bltz` and
  `+8` became `-v0` (0x8003C49C/C50C, 0x8003B650/B680). Full-width glyphs are untouched (return 1, +16).
- Font: the game's own ASCII glyphs trimmed to their ink, advance = ink + 1 (space 4, `i l |` 2, `m w M W` 8;
  table at 0x8008A03C, 96 slots). Index 277 (space) draws slot 93, indices >= 96 draw slot 95 (a box: Japanese
  left in an English line shows as boxes). Mode byte $gp+0x10C (an italic shear in the original) is never written
  and is ignored. **verified**: tests/test_vwf.py runs the hook in unicorn (pixels at all 4 shifts, carry,
  full-width path); marker build in-game (work/qa/mk/map81v).
- Encoding: English is plain ASCII (1 byte per glyph). `\` shows as a yen sign (Japanese font): don't use it.

## Boxes (tools/boxes.py)

| Box | Text area | Lines | When | Measured |
|---|---|---|---|---|
| face | 144 px (W 18) at x 96 | 4 | after op 16 (speaker + face) | winlog, work/qa/wintour |
| face3 | 144 px | 3 | MAP86 (New Game intro, mode 3) | winlog |
| plain | 224 px (W 28) at x 16 | 4 | after op 17 (open box, no face) | winlog, MAP14R/187/01DA |

The rule (last op 16/17 before the line in script order) matched every line the tour showed
(`boxes.py --check work/qa/boxes_seen.json`). build/insert wraps every dialogue line to `width - MARGIN` px.
Tour: `tools/debug/regen.py --cue build/nage_libre_en.cue --no-states --out work/qa/wintour --extra "--script
tools/debug/winlog.lua --var SETTLE=3000 --mash 40 --mash-key circle"`, then `tools/debug/winscan.py --json
work/qa/boxes_seen.json` (maps each logged pointer back to its row id).

## Fields (menus, labels, system messages: tools/boxes.py FIELDS)

Every EXE / record / name row has a budget (px per line, lines) in `boxes.FIELDS`; lint checks `en` against it
(error over px or lines, warning for a row with none; `tests/test_insert.py` asserts every row has one). How:

- Windows: `tools/wincreate.py` lists the 38 create calls 0x8003DB60(x, y, w, h). Shapes: command menu 40x80 at
  24,48 and sub-menu 40x80 at 56,72 (W 5, one item per line); field message box 224x64 at 16,152, header 224x16 at
  16,24, label 80x16 at 152,24, face box 144x64 at 96,152; battle message line 224x16 at 16,27, result box 144x64,
  VS boxes 96x48 at 16,168 / 144,168, status 224x64 at 16,154; level-up 224x64 / 256x48; dress-up 224x64; save/load
  224x160 at 16,56 + header 224x16; club-select stats 104x80 at 128,18; menu 224x64 at 16,96. **verified** for the
  ones the tour reached (fieldlog geometry = create args).
- Tour: `tools/debug/fieldlog.lua` (emu.py `--debugger`) logs every instant print 0x8003B288(window, string) and
  typewriter run with window geometry + pen; `tools/debug/fieldscan.py` maps them to rows (pointer, or marker text
  in composed buffers) and prints each row's start x and room to the next placed field / wrap edge. Runs:
  work/qa/ft (marker build, 11 scenes + command menus from `tools/debug/stateat.lua` state work/states/mk_cmd),
  work/qa/fo (original), work/qa/fq (QA build with English in the measured fields).
- Menus end items by auto-wrap: the Japanese pads each item to exactly 40 px (the `%h` half flag persists across
  prints in a window). English items get a trailing `\n` from `insert.fit_field` (a `\n` right after an
  auto-wrap is skipped, so a 40-px item is safe too).
- Composed lines (battle messages, result box, item use, level up): the code prints a name (0x8003B9EC) then the
  row on the same line; their px leave `boxes.NAME_PX` (48) per name. VS / status box line 1 is surname + given
  name printed in that order (NAME rows), 96 px for both: Western order (D1) needs the given name in the first
  print or a code swap (phase 7).
- Multi-line windows that a row starts (field box, dress-up, save/load) are word-wrapped by `insert.fit_field`.
- Not reached in a tour yet (budgets from the window only, marked "window"/"guess" in FIELDS): item/magic lists,
  item use, club change, level up, field save messages, memory-card errors. Phase 8 QA reaches them.

## Size limits found

- **SYSDATA.BIN**: buffer 0x80130000 size 0xC000 (memory-area table of {addr, size} words: 0x8008979C = {0x80130000,
  0xC000}, next area 0x8013C000). Original file 47,289 bytes: the names list (#7) may grow by 1,863 bytes in all. 10-byte name markers
  (+3.6 KB) hung New Game on its loading screen. insert.py and lint.py enforce it. Phase 6/7: keep names short, or
  move the list (its reader 0x8003B9EC copies up to 31 bytes of one name; lookup by counting CR LF lines).
- **NAGE.EXE strings in place**: `max` = own bytes + word-alignment zeros (extract.exe_room); in the $gp area exactly
  the original length. Filling the longer zero runs (old `max`) overwrote variables. Longer English: relocate.
- **MAPDAT**: grown to 502 KB (MAP24 markers) and played; ceiling 589 KB still a guess past that.

## Paging

`%k` (0x8003E39C) sets the wait flag $gp+0xAB0 and places the blinking arrow; the typewriter stops until the button
(op 14 ends every message with the same call). `%p` (0x8003E298) clears the window texture and puts the pen at 0,0.
So `page 1%k%ppage 2` pages inside one message with no script change: insert.py splits wrapped lines into
box-sized pages joined by `%k%p`. Translators get the box's lines as a soft limit (lint warns), not a hard one.
