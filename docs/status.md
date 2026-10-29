# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** Step 0 (repo setup) done 2026-10-29. Next: phase 1 (research and recon). No build yet.
- **Done:**
  - Dump pinned in `rom.sha1` (bin only; Redump, 113952048 bytes, MODE2/2352 single track).
  - Tools in `tools/` (gitignored, versions/URLs in AGENTS.md): PCSX-Redux nightly 29942, SCPH-5500 BIOS, mkpsxiso/dumpsxiso 2.30, armips 0.11.0. xdelta3 and capstone 5.0.7 already on the machine.
  - Original disc boots headless: `emu.py ... --route tools/routes/boot.txt --smoke` exits 0; route reaches the title menu (NEW GAME / SOUND STEREO), so scripted Start works; `tools/lua/hello.lua` logs to log.txt.
  - Pre-commit hook runs `tools/check.py` (pytest `tests/`); a failing test was rejected. Plugin guard hook blocks `sed -i` (canary checked).
- **Next (phase 1):** dumpsxiso the disc into `work/disc/`, list files (EXE, *.DAT/archives), find the text encoding (Shift-JIS expected) and pointer tables, compression, font, control codes; survey graphics text (title logo, menus, chapter cards). Record in `docs/re/`.
- **Open bugs:** none.
- **Waiting on the user:** GUI keyboard input in `tools/pcsx/` is not proven: synthetic keystrokes (keybd_event, with scancodes) did not reach the pad, though `pcsx.json` has default keyboard bindings (Enter=Start, X=Cross, arrows). Owner asked to run PCSX-Redux headless only, so this was left; check by hand when playtesting.
