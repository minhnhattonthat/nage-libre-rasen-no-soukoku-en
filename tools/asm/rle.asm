; Graphics entries re-encoded by tools/gfx.py (docs/re/graphics.md): the game's packed-block decoder decomp(src, dst)
; (0x80030B78) gets a front door. A block whose second byte is 'R' (packed blocks have 00 there) is the game's own
; simple RLE (0x80031388: n < 0x80 copies n bytes, n >= 0x80 repeats the last byte (n & 0x7F) + 1 times, 0 ends;
; same src/dst state at $gp+0x3F4/0x3F8, so callers find the end where decomp leaves it). Two marker bytes lead.
; armips tools/asm/rle.asm -strequ EXE <path to NAGE.EXE copy>

.psx
.open EXE, 0x80010000 - 0x800

DECOMP    equ (0x80030B78)
RLE       equ (0x80031388)

.org 0x80030B78                  ; DECOMP (a literal: tests/test_build.py reads the .org sites)
  j     RleHook
  nop

.org 0x8008A950                  ; end of the unused kana glyph rows (insert.STRPOOL stops here)
RleHook:
  lbu   t0, 1(a0)
  ori   t1, zero, 0x52           ; (load delay slot)
  bne   t0, t1, @@packed
  nop
  j     RLE
  addiu a0, a0, 2
@@packed:                        ; the two instructions the jump replaced
  addiu sp, sp, -0x28
  j     DECOMP + 8
  sw    s0, 0x10(sp)
.if . > 0x8008A97C
  .error "rle.asm runs into the data at 0x8008A97C"
.endif

.close
