# Text format (`script/`)

Made by `python -X utf8 tools/extract.py` from the unpacked disc; checked by `tests/test_extract.py`.

| File | Holds | id |
|---|---|---|
| `script/maps/MAPnn.json` | event dialogue, one file per map folder | `MAPnn/<slot>/<offset hex>` (MAPDAT slot 186-216, offset of the `0D`/`1D` opcode in the script) |
| `script/exe.json` | NAGE.EXE system text (battle, menus, memory card) | `EXE/<file offset hex>` |
| `script/records.json` | club, item and magic tables, memory-card title | `CLUB/nn/name`, `ITEM/nn/name|desc`, `MAGIC/nn/name|desc`, `MEMCARD` |
| `script/names.json` | SYSDATA #7 speaker / NPC / monster names | `NAME/nnn` (line number) |

Each file is a JSON list (`indent=1`, UTF-8, not ASCII-escaped) of rows:

- `id`, `jp` (never edit), `en` (the translation; empty = not done);
- `max`: bytes available without relocation (fixed fields and in-place EXE strings, NUL not counted);
- `same`: this line in a revisit map (`MAPnnR`) equals the line `same` names: translate that one, copy here;
- `dead`: in script code no path reaches (cut content); translate for completeness, low priority;
- `refs`: code sites that point at an EXE string (`lui:ADDR` = the addiu/load of a lui pair, `gp:`, `word:`);
- `long`: the full English of a field row wider than its `boxes.FIELDS` budget (`tools/batches.py merge`); `en`
  stays empty (Japanese in the build) until phase 7 widens the field or changes the engine, then it moves to `en`;
- `notes`, `status`: free for translators and reviewers.

Codec (`tools/text.py`): Shift-JIS as text, newline as `\n`, control codes as their ASCII (`%h` `%z` `%cNN` `%tNN`
`%p` `%k`, docs/re/text.md), any byte that would not roundtrip as `[XX]`. Leading/trailing spaces (`　`) are part of
the text. The English encoder is decided in phase 5 (font).

`extract.py` never overwrites a file; `--force` rewrites `jp` and keeps every other field by id.
