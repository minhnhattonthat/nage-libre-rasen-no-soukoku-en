# Nage Libre: Rasen no Soukoku (PS1) English translation

Skill: translate-retro-game (Claude Code: plugin, enabled in .claude/settings.json; other agents: its SKILL.md). `python tools/skill.py` prints its folder; `"$(python tools/skill.py)"` works in bash and PowerShell; never paste a `plugins/cache/<hash>` path. Read SKILL.md before ROM, text or QA work.

## Commands (run from repo root)
- Build:    `python -X utf8 tools/build.py` -> build/nage_libre_en.bin + .cue (checks the dump against `rom.sha1` first; unpacks to `work/disc/` on first run)
- Check:    `python -X utf8 tools/check.py` (tests + lint; the pre-commit hook runs this)
- Smoke:    `python -X utf8 "$(python tools/skill.py)/scripts/emu.py" build/nage_libre_en.cue --out work/qa/smoke --route tools/routes/boot.txt --smoke` (original: `"rom/Nage Libre - Rasen no Soukoku (Japan).cue"`)
- Warp:     `python -X utf8 "$(python tools/skill.py)/scripts/emu.py" build/nage_libre_en.cue --out work/qa/warp --script tools/debug/warp.lua --var "SCENE='<name>'" --frames 30000` (scenes: `tools/debug/scenes.lua`; ends itself on the scene with `<name>.png`; `--state-out` saves it; never ask the user to play to a scene)
- All scenes: `python -X utf8 tools/debug/regen.py [--cue build/nage_libre_en.cue --tree <build tree>]` (83 cold-boot warps, checks, `work/states/*.sstate`, sheet `work/qa/warp/all.png`; rerun after code/font/graphics changes)
- Release:  `python -X utf8 tools/release.py` (xdelta3 against the .bin + verify, phase 9; never publish without the user)
- Clean:    `python -X utf8 tools/clean.py` (published projects: lists rebuildable/downloadable files; `--yes` deletes)

## Paths
- Original disc: `rom/Nage Libre - Rasen no Soukoku (Japan).bin/.cue` (gitignored; bin SHA-1 in `rom.sha1`, checked by `tools/check_rom.py`).
- Emulator: PCSX-Redux nightly 29942.20261029.6 x64 in `tools/pcsx/` (`fetch_emu.py pcsx`, distrib.app dev-win-x64 channel; gitignored; settings copy in `tools/emu-config/pcsx.json`). Always run it headless through `emu.py` (no GUI windows). BIOS: `tools/bios/scph5500.bin` (`fetch_emu.py psx-bios`, picked up automatically). Savestates: `work/states/`.
- Disc tools: `tools/mkpsxiso/mkpsxiso-2.30-win64/{dumpsxiso,mkpsxiso}.exe` (v2.30, github.com/Lameguy64/mkpsxiso), `tools/armips/armips.exe` (v0.11.0, github.com/Kingcom/armips), xdelta3 on PATH. All gitignored; re-download from those releases.
- Text: `script/` (format set in phase 4). Tables: `tbl/`. Glossary: `glossary.md`. RE notes index: `docs/re/README.md`. Fonts and their licences: `docs/fonts.md`.

## Rulings
- Edit source files (.py .lua .asm .tbl .json) only with the file-edit tool; scripts here read and analyse, never `.replace()` and write back.
- Subagents: dispatch the `.claude/agents/` types (translator, reviewer, visual-qa, playtester), never general-purpose: their short tool list cuts each agent's start-up context from ~43k to ~9k tokens.
- The user's decisions, with the options and reasons: `docs/decisions.md`. Read it before asking the user anything; add each new ruling there the same session.
- Player bug reports: GitHub issues (`gh issue list --label bug`). Copy the attached save into `work/states/`, reproduce in the emulator, fix, commit with `Fixes #N`, and update `docs/status.md`.
- Japanese game: confirm is circle (`--mash-key circle`). Shift-JIS text: `jp_left.py --sjis`. Release patches the .bin only; no .cue in the zip.

## Status
`docs/status.md`: done, next, open bugs. Update it at the end of every session.
