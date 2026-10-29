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
| `%cNN` | 25 63 + 2 ASCII digits | colour, e.g. `%c02` before stage goals | guess (39 uses, all `%c02`) |
| CR LF | 0D 0A | separator in the SYSDATA name list only | verified |

## Text sources

| Source | Where | Count | Format |
|---|---|---|---|
| Event dialogue | `MAP01_06/MAPnn/MAPDAT.BIN` (46 files), entries 186-216 | ~4,160 strings | inline in script bytecode (below) |
| System text | NAGE.EXE file 0xBE8-0xC68 (battle menu), 0x13A0-0x1448, 0x1B6C-0x2B24 (battle messages, memory card, menus, items got) | ~150 | NUL-terminated, referenced by `lui/addiu` pairs (e.g. 0x800116F0 from 0x80057570) — verified for 2 strings |
| Items, magic, skills | NAGE.EXE file 0x7BAE4-0x7D3C7 | ~90 records | fixed **0x47-byte records**: name field (~0x14 bytes) + id/stat bytes + description field (`／単`, `／全` = single/all target) |
| Club names | NAGE.EXE file 0x7BB04-0x7BC04 | 9 | fixed 0x20-byte fields padded with `　` |
| Speaker / NPC / monster names | SYSDATA.BIN entry #7 (file 0xA188, 4,740 bytes) | ~250 | CRLF-separated list |
| Misc | NAGE.EXE file 0x80A2C-0x80BE8 | few | short labels (`セーブ`, `なし`) |

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
- **Consequence for insertion**: changing a string's length shifts every later byte of its script, so the inserter
  must parse each script with an opcode length table, re-encode, and remap every jump target in the same script; the
  MAPDAT offset table entries 186-216 (and only the ones after the script) shift too. No pointer outside the file was
  seen into scripts (guess: `$gp`+0x52C is always set from the offset table). Phase 4 builds the length table from the
  80 handlers and proves it by a roundtrip over all 46 files.

## Free space / limits

- MAPDAT: file may grow up to the RAM ceiling (~589 KB, docs/re/files.md); each script < 32 KB.
- NAGE.EXE: strings in place, or relocated into new space reached through the `lui/addiu` pairs; fixed item records
  (0x47 bytes) cap names/descriptions unless the record readers are patched. No free-space candidate verified yet.
- Glyph budget: 1,386 font cells; Latin glyphs would replace or extend these (phase 5 font decision).
