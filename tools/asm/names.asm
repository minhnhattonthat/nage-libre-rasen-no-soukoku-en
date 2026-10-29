; Full names in Western order (D1) and room for them. docs/re/vwf.md §Names
; armips tools/asm/names.asm -strequ EXE <path to NAGE.EXE copy> (after vwf.asm: NameSp sits after its code)
; Unit records (0x800B3778 + 0x50*n) hold the surname at +6 and the given name at +4 (NAME rows). Every place that
; prints both printed surname then given name with no space: the loads are swapped and the second print goes
; through NameSp, which puts a space first. The VS boxes (two 96x48 at x 16 / 144) become 112 px wide at x 8 / 136,
; since given + space + surname runs past 96 px for many pairs; the status box's "newline only if the name was
; under 12 cells" test becomes an unconditional newline (a \n right after an auto-wrap is skipped anyway).

.psx
.open EXE, 0x80010000 - 0x800

NAMEREAD  equ (0x8003B9EC)       ; (window, name index): prints SYSDATA name n, nothing for 0
PRINT     equ (0x8003B288)       ; instant print (window, string)
PENX      equ (0x800AD8A8)       ; window table 0x800AD89C + 0x1C*window, +0xC pen x
SPACE     equ (0x80090344)       ; " " (EXE_DATA, unchanged)

; VS box (battle engage): window 2 then window 1
.org 0x8004C56C
  ori   a0, zero, 8              ; x 16 -> 8
.org 0x8004C574
  ori   a2, zero, 112            ; w 96 -> 112
.org 0x8004C590
  ori   a0, zero, 136            ; x 144 -> 136
.org 0x8004C598
  ori   a2, zero, 112
.org 0x8004C5AC
  lh    a1, 0xBF4(gp)            ; given name first
.org 0x8004C5C4
  lh    a1, 0xBD8(gp)
.org 0x8004C5C8
  jal   NameSp
.org 0x8004C620
  lh    a1, 0xA38(gp)
.org 0x8004C630
  lh    a1, 0xA18(gp)
.org 0x8004C634
  jal   NameSp

; status pair (same boxes, 0x80059B74)
.org 0x80059B74
  ori   a0, zero, 8
.org 0x80059B7C
  ori   a2, zero, 112
.org 0x80059B9C
  ori   a0, zero, 136
.org 0x80059BA4
  ori   a2, zero, 112
.org 0x80059BB8
  lh    a1, 0xBF4(gp)
.org 0x80059BD0
  lh    a1, 0xBD8(gp)
.org 0x80059BD4
  jal   NameSp
.org 0x80059BE4
  nop                            ; newline always
.org 0x80059C44
  lh    a1, 0xA38(gp)
.org 0x80059C54
  lh    a1, 0xA18(gp)
.org 0x80059C58
  jal   NameSp
.org 0x80059C68
  nop

; battle status box (224x64)
.org 0x80051804
  lh    a1, 0x377C(at)
.org 0x8005181C
  lh    a1, 0x377E(at)
.org 0x80051820
  jal   NameSp

; field status pair
.org 0x80056B94
  lh    a1, 0x377C(at)
.org 0x80056BB0
  lh    a1, 0x377E(at)
.org 0x80056BB4
  jal   NameSp

; field status box: already prints surname, " ", given name
.org 0x80057DFC
  lh    a1, 0x377C(at)
.org 0x80057E48
  lh    a1, 0x377E(at)

; birthday screen: the heroine's full name starts one 8-px cell further left (x 16 -> 8): "Makoto Matsunaga" is
; 98 px and the stone plate starts 96 px after x 16
.org 0x800689F4
  ori   a1, zero, 2

; (the battle message bar 224x16 at 16,27 can't widen: its frame is fixed art, x 16 text sits right after the cap)

; save list: "<n>面" -> "Stage <n>": the label prints before the number (the 面 print becomes a nop)
.org 0x8006B60C
  jal   StageNum
.org 0x8006B61C
  nop
.org 0x8006BD44
  jal   StageNum
.org 0x8006BD58
  nop

.org 0x8008A314                  ; after vwf.asm's VwfHalf (insert.STRPOOL starts after this code)
; NameSp(window a0, name a1): a space when there is a name and the pen is not at the line start, then the name.
NameSp:
  addiu sp, sp, -0x20
  sw    ra, 0x10(sp)
  sw    a0, 0x14(sp)
  beqz  a1, @@name
  sw    a1, 0x18(sp)
  sll   t0, a0, 3
  subu  t0, t0, a0
  sll   t0, t0, 2                ; 0x1C * window
  la    t1, PENX
  addu  t1, t1, t0
  lh    t0, 0(t1)
  nop
  beqz  t0, @@name
  nop
  li    a1, SPACE                ; lui + ori: never in a delay slot
  jal   PRINT
  nop
  lw    a0, 0x14(sp)
  lw    a1, 0x18(sp)
@@name:
  jal   NAMEREAD
  nop
  lw    ra, 0x10(sp)
  nop
  jr    ra
  addiu sp, sp, 0x20

; StageNum(window a0, a1, digits a2, value a3): "Stage " then the number routine 0x8003B7A0 with the same args.
StageNum:
  addiu sp, sp, -0x28
  sw    ra, 0x10(sp)
  sw    a0, 0x14(sp)
  sw    a1, 0x18(sp)
  sw    a2, 0x1C(sp)
  sw    a3, 0x20(sp)
  la    a1, StageLabel
  jal   PRINT
  nop
  lw    a0, 0x14(sp)
  lw    a1, 0x18(sp)
  lw    a2, 0x1C(sp)
  jal   0x8003B7A0
  lw    a3, 0x20(sp)
  lw    ra, 0x10(sp)
  nop
  jr    ra
  addiu sp, sp, 0x28
StageLabel:
  .asciiz "Stage "
  .align 4
CodeEnd:
.if CodeEnd > 0x8008A500
  .error "names.asm code runs into insert.STRPOOL"
.endif

.close
