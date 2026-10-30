# Decisions

The user's rulings on scope, style and trade-offs, newest last. Read before asking the user anything; if a later
decision replaces one, mark the old one "replaced by D<n>" instead of deleting it. Binding term spellings live in
`glossary.md`; this file holds the why.

| # | Date | Question | Options offered | Decision and reason |
|---|---|---|---|---|
| D1 | 2026-10-29 | Honorifics and name order | keep (-san), drop; JP or Western order | Keep honorifics; Western order (given name first). Owner's standing answer for one-shot runs. |
| D2 | 2026-10-29 | Romanization source for names | official art, earlier patch, Hepburn | Official English names where they exist, else an earlier fan patch, else Hepburn without macrons. |
| D3 | 2026-10-29 | Credits | stay Japanese, translate | English. |
| D4 | 2026-10-29 | Abbreviations | engine work first (default), abbreviate | Skill default: full names and terms; engine work (wider box, VWF, small font) before abbreviating; abbreviation only as a flagged last resort. |
| D5 | 2026-10-29 | Graphics text left in Japanese | none (default), list | Translate all of it (titles, menus, banners, cards); keep the Japanese logo only if no official English version exists. |
| D6 | 2026-10-29 | Specs and plans | need approval, pre-approved | Pre-approved: keep going through checkpoints, report at the end. One phase per run, then commit, push to main and report. |
| D7 | 2026-10-29 | Existing saves / memory cards | user supplies, none | None provided; build the debug tool (phase 2) as usual. |
| D8 | 2026-10-29 | Emulator runs | GUI, headless | Run PCSX-Redux headless only (owner, mid-session): no GUI windows during agent work. |
| D9 | 2026-10-29 | Release scope | publish, build only | Never `gh release create`, never change repo visibility; the run ends at a built and verified release zip. Replaced by D14 for v1.0. |
| D10 | 2026-10-30 | Register, sound effects, 杏 spelling (controller defaults under D6, pre-approved run) | literal/adapted register; keep JP onomatopoeia or English; An / Ann | Casual natural English per character voice (docs/style-reference.md); English onomatopoeia, monster noise + meaning in (); 杏 = Ann (Hepburn "An" reads as the article). Owner can overrule. |
| D11 | 2026-10-30 | Text that no engine change fits (controller default under D4/D6, pre-approved run) | abbreviate; shorter wording; leave Japanese | Shorter natural wording, never an abbreviation, flagged here: 生徒会長 in the VS/status club line = "Council President" (the box is 112 px at most, both boxes fill the screen width; "Student Council President" is 136 px); battle bar 誕生石効果 card line = "'s Randoma Card, birthstone bonus!" (bar frame is fixed art, 224 px). Owner can overrule. |
| D12 | 2026-10-30 | MAP01R boss-intro name レイプマン (manga-title parody) | literal "Rapeman", another name | "Reipuman" (owner): romanised, keeps the parody without the English word. |
| D13 | 2026-10-30 | TIME GAUGE art spells Jin "Zin" | redraw as Jin, script follows art, keep | Keep the art as drawn (owner); script and glossary stay "Jin". |
| D14 | 2026-10-30 | Publish v1.0 | publish, keep local | Publish (owner): repo public with the template's README (Translation status table), GitHub release v1.0 with the verified zip. |
