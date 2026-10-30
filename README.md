# Nage Libre: Rasen no Soukoku English translation

Unofficial English fan translation of **Nage Libre: Rasen no Soukoku** (PlayStation, Varie, 1997): the source text and
tools that build the patch.

**Just want to play?** Download the patch from [Releases](../../releases) and follow its README. This repository holds
no game data you can play; you need your own dump of the Japanese game.

**Found a bug?** [Report it](../../issues/new/choose): untranslated text, typos, overflow, crashes. Attaching a savestate
helps most.

## Translation status

| Part | Status |
|---|---|
| Dialogue / story (all 46 maps) | Translated |
| Menus, items, magic, battle and system messages | Translated |
| Title screen, area cards, signs, posters, other graphics with text | Translated (a seal on the recruitment poster and background signs half hidden in two credits illustrations stay as drawn) |
| Names, birthday entry, save/load screens, memory card title | Translated |
| Credits roll | Cast plates translated |

The TIME GAUGE art spells Jin's name "Zin": that is the original's own English, kept as drawn.

Known issues: none known; see [Issues](../../issues).

## What's here

| Path | What it is |
|---|---|
| `script/` | Every text block: original Japanese and English. Translation fixes go here. |
| `glossary.md` | Binding names, terms and style rules. |
| `tools/` | Python build chain: extract, insert, lint, release. |
| `tests/` | pytest suite (ROM-dependent tests skip when the ROM is absent). |
| `docs/re/` | Reverse-engineering notes. |
| `docs/decisions.md`, `docs/status.md` | Rulings with their reasons; current progress and open bugs. |
| `docs/fonts.md` | Fonts used and their licences. |
| `AGENTS.md` | Instructions for coding agents (`CLAUDE.md` points to it). |
| `.claude/agents/` | Subagent types (translator, reviewer, visual QA, playtester) with only the tools each needs. |

## Build your own patched ROM

Needs Python 3.12+ and your own dump of the Japanese game.

```sh
git clone https://github.com/minhnhattonthat/nage-libre-rasen-no-soukoku-en
cd nage-libre-rasen-no-soukoku-en
# copy your Redump dump to: rom/Nage Libre - Rasen no Soukoku (Japan).bin (+ its .cue)
#   (113952048 bytes, SHA-1 7ccae6f0837c58e2d628c524baffe6a040cb8d02; the build refuses any other dump, see rom.sha1)
python -X utf8 tools/build.py                          # -> build/nage_libre_en.bin + .cue
python -X utf8 tools/check.py                          # tests + text lint
```

## Support

If you enjoy this translation, you can support my work on Ko-fi:

[![Support me on Ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/minhnhattonthat)

## Licence

Tools and English translation: MIT. The original Japanese text in `script/` is Varie's and is included only so
the translation can be checked against it. Nage Libre: Rasen no Soukoku is (c) Varie; this project is not affiliated
with them.
Do not share patched ROMs.

The translation was made with extensive AI assistance (Claude by Anthropic). Corrections are very welcome.
