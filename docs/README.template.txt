Nage Libre: Rasen no Soukoku - English translation v{VERSION}
=============================================================

Unofficial English fan translation of Nage Libre: Rasen no Soukoku (PlayStation, Varie, 1997).
This package holds a patch only. You need your own dump of the Japanese disc; no game data is included, and
pre-patched images are not provided.

What is translated
------------------
All dialogue, menus, battle messages, items, magic and effects, character and enemy names, and the text drawn
as pictures: title screen, birthday entry, load/save screens and chapter titles, area cards, boss intros, the
news ticker, the recruitment poster, signs, the dress-up item labels and the credits cast plates. The memory
card save title is in English too.

Base disc (must match)
----------------------
{HASHES}

Patching
--------
1. Use xdelta3 (command line) or Delta Patcher (GUI).
   xdelta3 -d -s "Nage Libre - Rasen no Soukoku (Japan).bin" {PATCH} "Nage Libre (English).bin"
2. Copy your original .cue next to the patched .bin and change the file name inside it to the new .bin name.
   The patched image keeps the original single-track layout.
3. Start a new game (cold boot). Saves from the Japanese version load.

Tested on PCSX-Redux. Report problems (untranslated text, overflow, crashes) on the project's GitHub issues page,
with a memory card file if you can.

Notes
-----
- Honorifics are kept (-san, -kun, -sama); names are in Western order (given name first).
- A few details in painted artwork stay as drawn (a seal on the poster, background signs half hidden in two
  ending illustrations). The TIME GAUGE art spells Jin's name "Zin": the original's own English, kept.
- Translation and tooling were produced with AI assistance (Claude) and checked in the emulator.
- English text uses the game's own letters; picture text adds Tiny5 (SIL Open Font License 1.1).
- Nage Libre: Rasen no Soukoku (c) Varie. This is a non-commercial fan work, not affiliated with Varie.
