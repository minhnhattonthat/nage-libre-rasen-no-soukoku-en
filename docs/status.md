# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 1 (research and recon) done 2026-10-29. Next: phase 2 (debug tool). No build yet.
- **Done:**
  - Step 0: dump pinned (`rom.sha1`), tools in `tools/`, headless smoke on the original, pre-commit check, guard hook.
  - Phase 1 (notes in `docs/re/`): Shift-JIS text; own font in SYSDATA.BIN (1,386 cells, 16x13, charset list);
    control codes `\n`, `%h`/`%z` (half-width), `%c02`; dialogue = inline strings in MAPDAT event scripts
    (entries 186-216, jump targets are u16 offsets from script start, 80-opcode table at 0x8008CD74); system text,
    item/magic records (0x47 bytes) in NAGE.EXE; names in SYSDATA #7; offset-table containers; packed-block codec
    run via `tools/decomp.py` (unicorn); graphics survey of 28 Japanese image elements (`docs/re/graphics.md`).
  - Text total ~4,400 strings / ~150 KB SJIS (`python -X utf8 tools/textscan.py work/disc/tree --summary`).
- **Next (phase 2, debug tool):** a Lua warp in `tools/debug/` that reaches any map/event/scene from cold boot.
  Leads: MAP number is the `%2.2d` in `%s\MAP%2.2d\CD_SYS.BIN`; find the RAM variable holding it (watch the sprintf
  caller, or ramsearch across map changes), the script base/PC at `$gp`+0x52C/0x2A2 (`$gp` = 0x800900EC), and story
  flags the opcode-0x04/05 switches read (handler 0x8005DE0C reads a variable by index). Scenes needed: every map
  (46 MAPDAT), battle, between-stage menu (OPTION4), dress-up (OPTION2), save/load (OPTION3), world map + area cards
  (OPTION7), ending/credits (OPTION6), game over, title/name entry (OPTION1).
- **Then:** phase 3 identity build (`dumpsxiso`/`mkpsxiso` layout in `work/disc/layout.xml`); phase 4 needs an opcode
  length table from the 80 handlers (0x8005E49C..0x80060854) to re-encode scripts.
- **Open bugs:** none.
- **Gotchas found (for the skill):** PCSX-Redux nightly 29942 `PCSX.GPU.getVRAM()` returns 2 MB, not 1 MB (first 1 MB
  is VRAM; pcsx_lib.lua comment says 1 MB). Unicorn MIPS translates kseg0 0x80000000 to physical for fetch and data:
  map RAM at 0 and stop on a code hook (the `until` address is missed after jr + delay slot).
- **Waiting on the user:** GUI keyboard input in `tools/pcsx/` is not proven (synthetic keystrokes did not reach the
  pad); owner asked for headless-only runs, so left; check by hand when playtesting. Non-blocking.
