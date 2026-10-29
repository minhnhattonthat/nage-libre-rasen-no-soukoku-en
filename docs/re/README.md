# Reverse-engineering notes

One file per subsystem (text engine, pointers, compression, font, graphics). Mark every finding with how far it is
proven, so a later session doesn't build on a guess:

- **verified** - and how: a decoded known string, a corrupt-and-boot test, a breakpoint hit on the drawing path, a
  passing roundtrip test. Name the test or savestate.
- **guess** - and why it seems likely (byte pattern, another game, an earlier patch's notes). Promote it to verified
  before code depends on it.

Addresses are for the dump in `rom.sha1` unless a note says otherwise.

| File | Covers | State |
|---|---|---|
| [files.md](files.md) | disc layout, offset-table container, load addresses, packed-block codec, MAPDAT RAM ceiling | layout/codec verified; CD_SYS no-LBA and RAM ceiling guessed |
| [text.md](text.md) | Shift-JIS, SYSDATA font (16x13, 1,386 cells), control codes, text sources, MAPDAT script bytecode and 16-bit jump targets, EXE records | encoding/font/script base verified; opcode lengths and `%c` open |
| [graphics.md](graphics.md) | graphics-text survey: 28 Japanese image elements with sources and copy counts | static sweep done; tour half in phase 5 |

Recon tools (in `tools/`): `textscan.py` (charset-filtered text finder), `tim.py` (TIM scan/render), `decomp.py`
(runs the game's decompressor in unicorn), `sweep_packed.py` (decompress + render every packed TIM), `re.py`
(capstone disassembly, lui/addiu xref), `vram.py` (render a VRAM dump).
