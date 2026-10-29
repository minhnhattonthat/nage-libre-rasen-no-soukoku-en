# Text: encoding, font, control codes, scripts, pointers

Addresses are RAM (NAGE.EXE file offset = addr - 0x80010000 + 0x800) unless marked as a file offset.

## Encoding and font

- **Shift-JIS**, 2-byte codes, NUL-terminated. Decoded known strings match the screen (classroom scene, MAP81
  file 0x48A30 "・・・\nこの人たちのことは気にしないで下さい" = shot `work/qa/r2/f000119.png`). **verified**.
- **Font = SYSDATA.BIN** (loaded at 0x80130000), not the BIOS Kanji ROM (no B0:51h call):
  - entry #3 (file 0x6B8, 36,036 bytes): **1,386 glyphs x 26 bytes = 13 rows of 16 bits, MSB = left pixel**;
  - entry #4 (file 0x937C, 2,780 bytes): the charset, 1,390 SJIS codes in glyph order (starts `！”＃...`).
    Glyph n draws charset[n]. **verified**: "の" is charset[153], glyph 153 at file 0x1642 matches the pixels the game
    drew into VRAM (`tools/textscan.py` uses this charset; `work/qa/r2` VRAM dump).
  - entry #5 (file 0x9E58, 284 bytes): single-byte (ASCII 0x21-0x7E, half-width katakana 0xA1-0xDF) to glyph map,
    used for half-width text (name list has `ﾓﾝｽﾀｰ`). **guess** (layout read by eye, not traced).
  - Only these 1,390 characters exist: any text, Japanese or English, can only use them (full-width Latin Ａ-Ｚ ａ-ｚ
    ０-９ are in the set). English needs a font/renderer change in phase 5 (narrow Latin glyphs or VWF).
- Text is software-rendered: the renderer (reads at 0x8003BFF4, 0x8003C0E4, 0x8003C2B0, 0x8003F288-0x8003F328,
  0x8003C644) draws glyphs as 4bpp pixels into a texture at VRAM (640,256)+ and the box shows that texture.
- **Line wrap is automatic** by box width; scripts use `\n` (0x0A) only for forced breaks. Face box: 9 full-width
  characters x 3 lines; box without face: ~10 per line. **verified** (MAP81 "澪%h（みお）%zやめてよー。樹..." has no
  `\n` and wraps on screen, `work/qa/r3/f000120.png`).

## Control codes (inside strings)

| Code | Bytes | Meaning | State |
|---|---|---|---|
| `\n` | 0A | line break | verified (screen) |
| `%h` ... `%z` | 25 68 / 25 7A | half-width mode on / off: glyphs drawn at half advance (furigana `樹%h（いつき）%z`, item names) | verified (screen) |
| `%cNN` | 25 63 + 2 ASCII digits | colour, e.g. `%c02` before stage goals | handler read (0x8003C0E4: 10*d1+d2 -> colour byte); meaning guess |
| `%tNN` | 25 74 + 2 digits | 2-digit value stored per window (speed/wait?) | handler read 0x8003C148; meaning guess |
| `%p` | 25 70 | calls 0x8003E298 (page/wait for button, guess) | handler read |
| `%k` | 25 6B | calls 0x8003E39C (same call as script op 0x14; clear/close, guess) | handler read |
| CR LF | 0D 0A | separator in the SYSDATA name list only | verified |

Renderer's control parser: 0x8003BFF4 (`\n`, then `%` + one letter at 0x8003C0E4-0x8003C204). The codec in
`tools/text.py` keeps these as literal ASCII in `script/` (`%h`, `%c02`...), so they roundtrip without a table.

## Text sources

| Source | Where | Count | Format |
|---|---|---|---|
| Event dialogue | `MAP01_06/MAPnn/MAPDAT.BIN` (46 files), entries 186-216 | ~4,160 strings | inline in script bytecode (below) |
| System text | NAGE.EXE file 0xBE8-0xC68 (battle menu), 0x13A0-0x1448, 0x1B6C-0x2B24 (battle messages, memory card, menus, items got) | ~150 | NUL-terminated, referenced by `lui/addiu` pairs (e.g. 0x800116F0 from 0x80057570) — verified for 2 strings |
| Items | NAGE.EXE file 0x7BC68 (RAM 0x8008B468) | 25 x **0x47** | name +0 (0x14), stat bytes +0x14..+0x16, description +0x17 (0x30). Field offsets from the code refs to +0/+0x14/+0x15/+0x16/+0x17 (`tools/mips.py` refs). verified (roundtrip; record 0 empty) |
| Magic / skills / item effects | file 0x7C358 (RAM 0x8008BB58) | 56 x **0x4C** | name +0 (0x14), stats +0x14..+0x1A, description +0x1B (0x31); records 38-55 have no name (effects of items, e.g. `%h"コバク"%zを使った`). verified (roundtrip) |
| Club names | file 0x7BAC4 (RAM 0x8008B2C4) | 10 x 0x20 (record 0 empty) | name +0 padded with `　` to the field. verified (roundtrip) |
| Memory-card save title | file 0x7DA1C (RAM 0x8008D21C) | 1 | 64 bytes full-width SJIS `ＮＡＧＥ　ＬＩＢＲＥ　～らせんのそうこく～　…`, shown by the BIOS card manager: keep full-width SJIS |
| Speaker / NPC / monster names | SYSDATA.BIN entry #7 (file 0xA188, 4,740 bytes) | ~250 | CRLF-separated list |
| Misc | NAGE.EXE file 0x809E8-0x80C10 ($gp area) | ~50 | short labels (`セーブ`, `なし`, `LV:`, club short names) between variables |

System strings: `tools/extract.py` takes NAGE.EXE runs in 4 regions (0xBE8-0xC80, 0x13A0-0x1458, 0x1B6C-0x2B58,
0x809E8-0x80C10), split at every address code references (lui pair, $gp, or 32-bit word: `mips.refs()`), so strings
packed right after pointer tables are found. 178 strings, every one with at least one code reference (listed in
`script/exe.json` `refs`, for relocation in phase 7). Non-text runs (pointer tables, variables, `cdrom:\NAGE.EXE;1`,
`bu00:`) are listed in `extract.EXE_DATA`; test_extract fails if the classifier ever disagrees with that list.
**verified** (roundtrip; no other NUL-bounded 3+ font-character run exists in NAGE.EXE).

Totals from `tools/textscan.py` (full-width-kana filter, min 2 chars): 4,399 strings, 151,543 bytes of SJIS in
MAPDAT + NAGE.EXE. Many MAPnnR files repeat their MAPnn text (revisited maps).

## MAPDAT scripts (pointer format)

- MAPDAT is a 217-entry u32 offset table (docs/re/files.md); **entries 186-216 are event scripts**, one per slot,
  placed at the end of the file (MAP81: 186-191 used). Largest script 6,976 bytes; scripts per map <= 10,697 bytes.
- Interpreter: main loop 0x8005DC60; script base pointer `$gp`+0x52C (= 0x80090618) = start of the current script
  slot; script PC `$gp`+0x2A2 (= 0x8009038E) is a **signed 16-bit offset from that base** (`lh`), so a script must
  stay under 32 KB. **verified** (RAM: base 0x801B88DC = MAP81 entry 186, PC 0x182 at the shown line).
- Opcodes are 16-bit words (opcode byte + 00), dispatch table at 0x8008CD74: 80 entries of {u32 opcode, u32 handler}
  for opcodes 0x01-0x51. Known:
  - `01 target` goto; `02 target` gosub; `04`/`05 var count t0..tn` switch with u16 targets (0xFFFF = fall through).
    **Targets are u16 offsets from the script start** (verified from the handlers at 0x8005E49C-0x8005E648).
  - `14 00 <18|19> 00 [args...] 1D 00 <SJIS text> 00 [00 pad to even]` shows a message: `18` = with face/speaker
    args, `19` = plain; `1D` precedes the inline string (verified on MAP01/MAP81 data; argument counts per sub-op not
    yet mapped).
- **Opcode lengths** (read from all 80 handlers; table `OPS` in `tools/script.py`). Each argument is a u16; kinds:
  v value, j jump target, s string offset, d data offset (all offsets from the script start).
  - flow: `01 j` goto, `02 j` gosub, `03` return, `04/05 v n j*n` switch/gosub-switch (0xFFFF = fall through),
    `06/08 v j` jump if true/false, `07/09 v j j` two-way jump, `1F/21 v j` gosub if, `20/22 v j j` gosub then
    two-way jump, ends `0B 35 36` and `3B v` (map change);
  - text: `0D`/`1D` inline SJIS string (then NUL, then one more 0 if the next byte is 0, keeping the PC even),
    `0C s`/`1C s`, `0E/1E v n s*n`, `23 25 27 29 v s`, `24 26 28 2A v s s` (string by offset; none used on this disc);
  - data: `15 d` (8 bytes read), `1B v v d` (move list, 8 bytes x count byte);
  - others: no args `14 17 18 19 33 3C 3D 42 46 4F`; 1 arg `0A 0F 10 11 12 2C 2D 32 34 37 38 39 3A 3F 40 41 44
    47 49 4A 4B 4D 4E`; 2 args `13 16 1A 2B 2E 2F 30 3E 43 45 48 51`; 3 args `31 4C`. Opcode 0x50 does not exist.
  - Unused slots hold `1A 00 00 00`; MAP40 slot 187 is 0 bytes.
- **Verified** by `tools/script.py check` / tests/test_extract.py on all 802 scripts: control flow from offset 0
  covers every byte except a few dead bytes; 69 strings sit in dead code (skipped by a goto) and are decoded
  linearly; rebuilding with every string lengthened gives the same program with every offset remapped.
- **Insertion**: `script.rebuild()` re-encodes a script and remaps j/s/d arguments; `script.rebuild_mapdat()` shifts
  the offset-table entries after it. No pointer outside the file was seen into scripts (guess: `$gp`+0x52C is always
  set from the offset table; prove in phase 5 with a lengthened script that plays).

## Free space / limits

- MAPDAT: file may grow up to the RAM ceiling (~589 KB, docs/re/files.md); each script < 32 KB.
- NAGE.EXE: strings in place, or relocated into new space reached through the `lui/addiu` pairs; fixed item records
  (0x47 bytes) cap names/descriptions unless the record readers are patched. No free-space candidate verified yet.
- Glyph budget: 1,386 font cells; Latin glyphs would replace or extend these (phase 5 font decision).
