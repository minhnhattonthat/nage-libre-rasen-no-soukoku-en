; Variable-width font for half-width (single-byte) text. docs/re/vwf.md
; armips tools/asm/vwf.asm -strequ EXE <path to NAGE.EXE copy>
; The glyph draw 0x8003C778(glyph a0, x a1, y a2, colour a3) returned 0 for a half-width glyph and its two callers
; added 8 to the pen. Now half-width glyphs are drawn at any pixel x and return -advance; the callers subtract it.
; Font rows and the advance table are written by tools/font.py (FONT / WIDTH there).

.psx
.open EXE, 0x80010000 - 0x800

FONT      equ (0x80089B5C)
WIDTH     equ (0x8008A03C)
PREV      equ (0x8008A09C)       ; +0 x, +4 y of the last half glyph, +8 its 13 rows x 3 VRAM units (78 bytes)
LOADIMAGE equ (0x800750C4)
SLOTS     equ (0x8009E86C)       ; upload ring: slot = SLOTS + counter*240 + frame*120
EPILOGUE  equ (0x8003C930)

; callers: half glyphs return -advance (full-width glyphs still return 1 and advance 16)
.org 0x8003C49C
  bltz  v0, 0x8003C4FC
.org 0x8003C50C
  subu  v1, v1, v0
.org 0x8003B650
  bltz  v0, 0x8003B670
.org 0x8003B680
  subu  v1, v1, v0

; half-width branch of the draw: s0 = x, s1 = y, a2 = colour, a0 = glyph (< 500); frame of 0x28 saves s0-s2, ra
.org 0x8003C868
  j     VwfHalf
  addiu s0, s0, 1               ; ink 1 px right of the pen: the trimmed glyphs have no left bearing, so a line's
                                ; first letter touched the window frame (wrap leaves 1 px at the right, so lines
                                ; still fit). EPILOGUE restores s0.

.org 0x8008A0F4
VwfHalf:
  ; glyph slot: 277 (space) -> 93, anything past the 96 VWF slots -> 95 (box)
  li    t0, 277
  bne   a0, t0, @@notspace
  sltiu t0, a0, 96
  b     @@slot
  li    a0, 93
@@notspace:
  bnez  t0, @@slot
  nop
  li    a0, 95
@@slot:
  la    t1, WIDTH
  addu  t1, t1, a0
  lbu   s2, 0(t1)               ; s2 = advance
  sll   t0, a0, 3
  sll   t2, a0, 2
  addu  t0, t0, t2
  addu  t0, t0, a0              ; 13 * glyph
  la    t1, FONT
  addu  t1, t1, t0              ; t1 = glyph rows
  andi  a2, a2, 0xF
  ; upload slot (as the original): t3 = SLOTS + counter*240 + frame*120
  lw    v1, 0xBD4(gp)
  lui   t2, 0x8009
  lw    t2, 0x858(t2)
  sll   t4, v1, 4
  subu  t4, t4, v1
  sll   t4, t4, 4
  sll   t5, t2, 4
  subu  t5, t5, t2
  sll   t5, t5, 3
  la    t3, SLOTS
  addu  t3, t3, t4
  addu  t3, t3, t5
  sra   t4, s0, 2               ; t4 = VRAM unit of x (4 px each)
  andi  t5, s0, 3               ; t5 = pixel shift in that unit
  ; units written: ceil((shift + advance - 1) / 4), so the rect never passes the last inked unit
  addu  a0, t5, s2
  addiu a0, a0, 2
  srl   a0, a0, 2               ; a0 = units (the glyph index is no longer needed)
  ; carry: when this glyph follows the last one on the same row to its right, OR in the last glyph's units
  li    t6, 3                   ; t6 = unit offset into PREV rows (3 = no overlap)
  la    t7, PREV
  lw    t8, 0(t7)
  lw    t9, 4(t7)
  nop                           ; load delay
  bne   t9, s1, @@nocarry
  slt   v0, t8, s0
  beqz  v0, @@nocarry
  sra   t8, t8, 2
  subu  v0, t4, t8
  sltiu v1, v0, 3
  bnez  v1, @@nocarry
  move  t6, v0                  ; delay slot: overlap 0..2 units
  li    t6, 3
@@nocarry:
  sw    s0, 0(t7)
  sw    s1, 4(t7)
  addiu t7, t7, 8
  li    t8, 13
@@row:
  lbu   t9, 0(t1)
  addiu t1, t1, 1
  sllv  t9, t9, t5              ; 12 pixels, bit p = pixel p
  move  v0, zero                ; pixels 0-7 (units 0, 1)
  move  v1, zero                ; pixels 8-11 (unit 2)
  move  a1, zero
@@px:
  srlv  a3, t9, a1
  andi  a3, a3, 1
  beqz  a3, @@nextpx
  sltiu a3, a1, 8
  beqz  a3, @@hi
  sll   a3, a1, 2
  sllv  a3, a2, a3
  b     @@nextpx
  or    v0, v0, a3
@@hi:
  addiu a3, a3, -32
  sllv  a3, a2, a3
  or    v1, v1, a3
@@nextpx:
  addiu a1, a1, 1
  sltiu a3, a1, 12
  bnez  a3, @@px
  nop
  ; previous glyph's units shifted left by t6: p0 p1 p2 -> units 0 1 2
  lhu   a1, 0(t7)
  lhu   a3, 2(t7)
  lhu   t0, 4(t7)
  move  t2, t6
@@shift:
  beqz  t2, @@merge
  addiu t2, t2, -1
  move  a1, a3
  move  a3, t0
  b     @@shift
  move  t0, zero
@@merge:
  sll   a3, a3, 16
  or    a1, a1, a3
  or    v0, v0, a1
  or    v1, v1, t0
  ; remember all 3 units, upload the first a0
  sh    v0, 0(t7)
  srl   a1, v0, 16
  sh    a1, 2(t7)
  sh    v1, 4(t7)
  addiu t7, t7, 6
  sh    v0, 0(t3)
  sltiu a3, a0, 2
  bnez  a3, @@stored
  addiu t3, t3, 2
  sh    a1, 0(t3)
  sltiu a3, a0, 3
  bnez  a3, @@stored
  addiu t3, t3, 2
  sh    v1, 0(t3)
  addiu t3, t3, 2
@@stored:
  addiu t8, t8, -1
  bnez  t8, @@row
  nop
  ; LoadImage({0x280 + unit, 0x100 + y, a0, 13}, slot)
  sll   a1, a0, 1
  sll   a3, a0, 3
  sll   t0, a0, 4
  addu  a3, a3, t0
  addu  a1, a1, a3              ; 26 * units = bytes uploaded
  subu  a1, t3, a1              ; slot start
  sh    a0, 0x14(sp)
  addiu a0, t4, 0x280
  sh    a0, 0x10(sp)
  addiu a0, s1, 0x100
  sh    a0, 0x12(sp)
  li    a0, 13
  sh    a0, 0x16(sp)
  jal   LOADIMAGE
  addiu a0, sp, 0x10
  lw    v0, 0xBD4(gp)
  nop
  addiu v1, v0, 1
  slti  v0, v0, 0x64
  sw    v1, 0xBD4(gp)
  bnez  v0, @@ret
  li    v0, 0x63
  sw    v0, 0xBD4(gp)
@@ret:
  j     EPILOGUE
  subu  v0, zero, s2
.if . > 0x8008A314
  .error "VWF code runs into names.asm (0x8008A314)"
.endif

.close
