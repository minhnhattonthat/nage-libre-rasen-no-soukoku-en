# Disc layout, file formats, compression, load addresses

Dump: `rom.sha1`. Unpack: `dumpsxiso -x work/disc/tree -s work/disc/layout.xml <cue>` (run in `work/disc/`).

## Boot and files

- `SYSTEM.CNF` boots `SLPS_006.92` (small loader: shows `VARIE.BIN`, then runs `cdrom:\NAGE.EXE;1`). **verified** (strings).
- `NAGE.EXE`: PS-X EXE, text loaded at 0x80010000, size 0x80800 (file offset = addr - 0x80010000 + 0x800), entry
  0x80071E60, `$gp` = 0x800900EC (set at 0x80071EE0). RAM matches the file at runtime. **verified** (RAM dump).
- Files are opened by name through libcd `CdSearchFile` (directory cached at boot, "CD_cachefile"). Root files are
  named in NAGE.EXE (`\SOUND.BIN;1` ... `\KIG_AC.BIN;1`, file offset 0xFC4-0x10C4); per-map files are listed by name
  in `MAP01_06/MAPnn/CD_SYS.BIN` (format string `%s\MAP%2.2d\CD_SYS.BIN;1`). CD_SYS holds only names, no LBAs/sizes,
  so a rebuild that moves or resizes files needs no table fix-up. **guess** (no LBA field seen; prove in phase 3 by
  growing a file and booting).
- `3MIN.BIN` (30,000,001 bytes) is disc padding.
- Odd file sizes (e.g. 16001, 22833): files end in a stray byte (0x1A / 0xFF). Keep it.

## Container format

Almost every data file is a **u32 offset table**: word 0 = table size in bytes = 4 x entry count; each entry is an
absolute file offset; an entry's length runs to the next entry (the last to EOF). Entries hold raw TIMs, packed
blocks (below), script bytecode or game data. `tools/sweep_packed.py` `table()` validates it. **verified** on
SYSDATA, OPENDATA, OP_TMP*, OPTION*, FACE, MAPFIRST, MAPDAT, KIG_*.

| File | Loaded at | Holds |
|---|---|---|
| SYSDATA.BIN (13 entries) | 0x80130000 | #3 font, #4 font charset, #5 half-width map, #7 name list (docs/re/text.md) |
| MAPnn/MAPDAT.BIN (217 entries, always) | 0x80170000 (whole file) | map data; entries 186-216 = event scripts with the dialogue |
| MAPnn/MAPTIM, MAPFIRST, BTLTIM | - | map/battle textures (raw 8bpp TIMs, 128x256) |
| MAPnn/FACE.BIN, FACE/FACE_Snn.BIN | 0x80148000 / 0x80160000 | packed face portraits (pixels, no TIM header) |
| OPENDATA, OP_TMP1/2, OPTION1-7, VARIE | 0x80170000 (OPENDATA) | title, intro, menus, save screens, area cards |
| KIG_AC/BT/SH/TO.BIN | - | 45-ish packed TIMs each (mini-games?) |

RAM ceiling for MAPDAT: it is loaded at 0x80170000 and the stack starts at 0x801FFF00, so a MAPDAT may be up to
~0x8FF00 bytes (589,568). The largest original is MAP24 (486,109), leaving ~100 KB. **guess**: nothing else was
seen between the MAPDAT end and the stack in the MAP81 RAM dump; prove with a grown MAPDAT before relying on it.

## Compression (packed blocks)

Custom nibble-oriented codec with several run/literal modes. Decoder: `NAGE.EXE 0x80030B78 decomp(a0=src, a1=dst)`;
nibble reader 0x80031314, state in `$gp`+0x3D0..0x3F8 (output pointer at `$gp`+0x3F8). Callers: 0x8003E848,
0x8003E874, 0x80041E48, 0x80041F34, 0x80061664.., 0x80065134, 0x800670A4. A second, simple RLE decoder sits at
0x80031388 (byte >= 0x80: repeat previous byte (n & 0x7F) + 1 times; else copy n literal bytes; 0 ends).

- Packed TIMs start `xx 00 10 88 80 98 88 0c 02 00 f0 37 ...` (OPENDATA #0-2, OP_TMP2 #11, SYSDATA #12, KIG_*).
- Face blocks use the same codec (FACE_S01 #1: 4248 -> 8192 bytes of 16-bit pixels).
- `tools/decomp.py` runs the game's own routine in unicorn: **verified** (OPENDATA #0 decodes to a valid 66,080-byte
  128x256 8bpp TIM). No Python port or compressor yet. Before editing a packed image, try first whether the loader also
  takes a raw TIM in the same table slot (OPENDATA mixes packed and raw TIMs), which avoids writing a compressor.
