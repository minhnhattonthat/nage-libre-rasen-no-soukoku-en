# Translation reviewer brief - Nage Libre: Rasen no Soukoku

You review one batch of a JP->English fan translation. Read-only: no edits, no git, no subagents.
Mechanical validity (ids, control codes, encodable characters, width) is already enforced by
`tools/batches.py check` - judge translation quality. Return the report as your final message: subagents cannot
write files, so the controller saves it.

## Inputs (paths in your dispatch)
- Pairs file: every translated entry as `>> id | JP` / `EN` with +-2 context lines (` / ` = a JP line break).
  Read ALL of it, in passes if large.
- `glossary.md` (rulings at the top), `docs/style-reference.md`, `docs/synopsis.md`.

## Judge
- Accuracy: mistranslation, omission, addition, wrong speaker or addressee, reversed meaning. Quote the JP and say
  what it means.
- Consistency: glossary names/terms exactly (a one-letter slip is what players notice); honorifics kept and
  hyphenated (Tsukasa-kun); voices per the style reference (Makoto in third person, Mio polite, Shinobu rough).
- Things players caught that reviewers missed: jokes/wordplay losing their punch; abbreviated names or terms;
  stock phrases that read awkwardly in English ("... GET!"); split sentences that don't read in sequence.
- Naturalness: would a fan-translation reader stumble?

## Report
### Issues
#### Critical (meaning reversed, broken placeholder grammar, wrong speaker)
#### Important (clear mistranslation, glossary inconsistency, abbreviation)
#### Minor (style - these are deferred to one polish pass)
Each: `id - JP gist - problem - suggested EN`.
### Assessment
Approved | Needs fixes - one sentence why.
