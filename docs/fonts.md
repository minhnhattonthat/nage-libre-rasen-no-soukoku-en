# Fonts

Every font or glyph sheet the build reads ends up inside the released patch, so its licence must allow that. One row
per file; a font with no known licence doesn't go into a release.

| File | Source (URL, version) | Licence | Redistributable in a patch | Used for | Changes made |
|---|---|---|---|---|---|
| (none: NAGE.EXE 0x80089B5C) | the game's own half-width ASCII glyphs, read from the user's disc at build time | the game's | the patch carries the re-encoded bitmaps (as any fan translation patching a game font) | dialogue and menu VWF (tools/font.py) | trimmed to ink, rows bit-reversed, advances added; slot 95 a drawn box glyph |
