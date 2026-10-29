# Translator brief - Nage Libre: Rasen no Soukoku (PS1, 1997)

You translate part of the Japanese script of Nage Libre: Rasen no Soukoku into English for a fan patch. A light
comedy RPG: five Nanju High girls (Ann, Itsuki, Makoto, Shinobu, Mio) hunt the stolen Nage Statue through parallel
worlds, fighting monsters and rival student councils.
Work only on the batches named in your dispatch, one at a time in the order given, each to a passing check before
the next. Do all translation yourself; do not dispatch subagents. Never edit anything but your own output files.

## Read first
1. `docs/style-reference.md` - character voices and approved example pairs. Match this voice.
2. `work/tl/terms_<batch>.txt` - binding glossary rows for this batch (full table and rulings in `glossary.md`).
3. `docs/synopsis.md` - who is who. Don't give a reveal away early.

## Input: `work/tl/<batch>.tsv`
`id<TAB>speaker<TAB>form<TAB>limit<TAB>Japanese`
- speaker: Ann / Itsuki / Makoto / Shinobu / Mio (from the portrait), `NPC face N` (a townsperson or monster; the
  same N = the same NPC), `(no face)` (narration, system messages, or an NPC talking in a plain box), `Jin?`/`Dai?`
  (guessed). The portrait can lag one line: if the text clearly belongs to someone else, voice it for them.
- form: dlg | narration | menu | label | name. limit: the box (`face 143px x4` = 143 px wide, 4 lines before it
  pages; `plain 223px x4`; fields `Npx xL` = hard width per line and line count).
- ` / ` separates the JP's forced line breaks; `(unused: cut content)` marks lines no path reaches (translate them).
- Lines are in story order. Many scripts have the same line once per girl (L1/R1 picks who talks): translate each
  in that girl's voice (Mio polite, Shinobu rough, Makoto in third person), identical if the JP and voice allow.
- Some lines are pieces of one sentence split over several boxes: make the pieces read in sequence.

## Output: `work/tl/<batch>.out.tsv`, written with your file-write tool (never a shell heredoc)
`id<TAB>English`, every input id exactly once, same order. Plain ASCII: straight quotes, `...`, `--`, `~`; no tabs
inside the English, no Japanese or fullwidth characters, no `\uXXXX`, no `\`, no bare `%`. Dialogue: no line
breaks (the build wraps by pixels and pages long text). Write `\n` (backslash-n) only where a break must fall:
Clear Condition boxes, lists, signs, and multi-line menu/label fields.

## Validate
Run `python -X utf8 tools/batches.py check <batch>` from the repo root and fix every reported id until it prints OK.
`python -X utf8 -c "import sys; sys.path.insert(0,'tools'); import font; print(font.advance('text'))"` gives a
string's width in px.

## Style
- Faithful: keep the information and order of ideas; adapt idiom, not meaning. Don't add details the Japanese
  doesn't state; don't summarise or skip. Adapt wordplay so the joke still lands (no translator notes).
- Names and terms exactly as in the glossary. Never abbreviate to fit; dialogue pages automatically. A field that
  can't fit without losing meaning: keep the meaning and report `LONG: id`.
- Honorifics kept, hyphenated: 司クン -> Tsukasa-kun, 真さん -> Makoto-san, 黒沢様 -> Lord Kurosawa or
  Kurosawa-sama (pick per tone, report it). Western name order: 神崎　薫 -> Kaoru Kanzaki.
- Drop furigana: 樹%h（いつき）%z -> Itsuki; drop every %h and %z. Copy `%c02` (colour) and `%p`/`%d` exactly.
- Punctuation: 「」 and ”” -> "...", ・・・ -> ..., ！？ -> ?!, ～ -> ~, ♪ -> "La la" or drop if it's a tune mark.
  Kaomoji -> ASCII ("(-_-) zzZ").
- Monster speech: keep the noise, then the meaning in parentheses: "Oink oink! (Not a chance!)".
- Item get: "Got the "Baby Tee".", "Got an S Candy." Stage cards: "Stage 1 Start", "Clear Condition\n%c02...".
- System text (form menu/label): many EXE strings are fragments printed right after a name or item
  (`は防御した` = "[name] defended", `を手に入れた` = "got [item]"); write the English so it reads after/before
  that piece, starting with a space when it follows a name ("[Ann]" + " defended."). Keep a field's fixed
  leading spaces only if the layout needs them. Rows with `max` bytes: in-place room; over it is a warning only.

## Consistency
Never edit `glossary.md`. For a recurring name or term not in it, pick a form, use it consistently, and report it.

## Report (reply with only this)
Files written and entry count; then any lines: `NEW TERM: jp -> en`, `UNSURE: id - note`, `LONG: id - note`.
