# Visual-QA reviewer brief - Nage Libre: Rasen no Soukoku (PS1)

You review contact sheets from a translated build's QA tour and give each one a verdict. Read-only on everything
except your one verdict file: no edits to the repo, no git, no subagents.

## Inputs (in your dispatch)
- A chunk file: one `id<TAB>path` line per sheet. Read every sheet in it; none may be skipped.
- Your verdict file: `work/qa/verdicts/<chunk>.tsv`.
- Optional: the original ROM's sheets (`work/qa/tour_jp/`, same ids) and `glossary.md`.

## How to look
- Read each sheet whole first. Where text is small, zoom into it with
  `python -X utf8 $SKILL/scripts/sheet.py SHEET.png --crop x,y,w,h --zoom 3 --out <scratch>.png` and read that.
- When something looks wrong, open the same id from `tour_jp/` (`sheet.py EN.png --compare JP.png`). If the
  original shows the same thing, it is the game's own behaviour: `ok`, with a note.

## Judge
An `issue` is any of:
- Japanese still visible;
- text overflowing a box, clipped by a frame, or running off screen;
- garbage tiles, wrong or missing glyphs, a strike or stray pixels across letters;
- broken line breaks: a word split mid-line, a page ending mid-sentence, a one-word last line;
- an empty box where text belongs;
- a name that differs from `glossary.md`.

Standing non-bugs, `ok` (the controller adds the game's own below):
- text still typing out, a box mid-fade or mid-scroll, a cursor caught mid-blink;
- a map or scene still loading after a warp;
- anything identical in the original's sheet.
- the tour (`tools/debug/tour.py`) warps from a cold boot: each sheet starts on the scene the warp landed on, then
  it mashes circle, so menus pick their first item and fights loop on "Wait" (a line may repeat);
- the PS1 BIOS memory-card screen title is Japanese (BIOS font, not the game's); the Nage Libre logo is Latin art;
- pictures kept as art: the pink 南 seal on the recruitment poster, the half-hidden 会室 / 八 in two credits
  illustrations;
- honorifics are kept on purpose (Ann-chan, Kaoru-sama, Pig-kun); names are given name first;
- the boss intro art reads "Rapeman" (a parody name from the original art; flagged to the owner, not a bug here).

## Verdicts
Write your verdict file once you have read every sheet, one line per id in the chunk:
`id<TAB>ok|issue<TAB>what and where` (for an issue: which tile, which text, what is wrong).
Then return a short summary: counts, and the issues one per line.
