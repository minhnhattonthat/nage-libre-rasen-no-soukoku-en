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
| D9 | 2026-10-29 | Release scope | publish, build only | Never `gh release create`, never change repo visibility; the run ends at a built and verified release zip. |
