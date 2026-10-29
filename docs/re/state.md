# Game state: map, mode, fade callback, story flags, units

RAM addresses (NAGE.EXE, `$gp` = 0x800900EC). Used by the debug warp (`tools/debug/warp.lua`, scene list
`tools/debug/scenes.lua`, all scenes: `python -X utf8 tools/debug/regen.py`).

## Map and screen selection

| Address | Size | Meaning | State |
|---|---|---|---|
| 0x80090276 | u8 | current map number (MAPnn = nn; 0x56 = 86 at boot/title) | **verified**: `%s\MAP%2.2d\CD_SYS.BIN` sprintf at 0x80035BDC reads it; warps to every MAPnn load that folder's MAPDAT (regen.py check) |
| 0x80090277 | u8 | entry: which file set of the map's CD_SYS.BIN loads (set 0 at CD_SYS+0x8C, set 1 at +0x1700). MAP01 and MAP14: 0 = MAPnnR, 1 = MAPnn; MAP03/12/13/17/31/42: 0 = MAPnn, 1 = MAPnnR | **verified** (MAPDAT check per scene) |
| 0x80090B28 | u8 | screen for the mode loader 0x800673CC (table 0x80012358): 1 birthday entry (OPTION1), 2 load (OPTION3), 3 between-stage menu (OPTION4), 4 ending + credits (OPTION6), 5 cutscene after MAP24, 6 save (OPTION3); other values = 1 | **verified** (shots: birthday, load, menu, credits, cutscene_m24, save_after_m80) |
| 0x80090C60 (`$gp`+0xB74) | u32 | fade-out callback: when the fade counter `$gp`+0x9D8 reaches 0x1D the main loop calls it (0x80043C8C). Setters 0x80043CD4 / 0x80043CE8 (a0 = function); `tools/fadecb.py` lists every queued function | **verified** (warp swaps it) |
| 0x80089874 | 13-byte records | map number + folder (`\MAP01_06` for every map); 83 and 86 missing (fall back to the first record) | verified (static) |
| 0x8008D178 | u8 list, 0-terminated | maps that show the world map + area card when the menu's スタート is chosen: 6-19, 21-24, 30-32, 40-42, 50 (25 = the 25 OPTION7 cards) | **verified** (wm06 shot shows 密林) |

Fade callbacks seen (from `tools/fadecb.py` and runs):

| Function | What it does |
|---|---|
| 0x8003F5B0 | story progression: `switch (map)` (jump table 0x80010E0C, maps 1-86) sets the next map / entry / flags, then calls the field loader (default) or the mode loader with mode 3 (a0), 5 (a2) or 6 (a1); map 82 with 0x80105B62 = 1 goes to mode 4 (ending). Queued by script code at 0x8005FC24 and by New Game |
| 0x8003F494 | after a stage's battle phase: maps 1, 4, 13, 24, 83, 84 bump the entry byte or jump (queued at 0x8005FBDC) |
| 0x80022780 | field loader: loads map (0x276, 0x277) and runs its event script |
| 0x800673CC | mode loader (0x80090B28) |
| 0x80059948 | start a battle between the units at 0x80090960 and 0x80090974 |
| 0x80022F08 | battle over, back to the field |
| 0x8006C790 / 0x80068C78 / 0x8006B730 / 0x8006F048 | menu items: 部活セレクト (OPTION5) / 着せかえ (OPTION2) / セーブ / スタート with world map (OPTION7) |
| 0x8006DB10 | back to the between-stage menu |
| 0x800614B8 | after loading a save |

Next-map table (0x8003F5B0, from the disassembly; m = mode-3 menu first, f = field directly):
86→81f; 81→ by 0x80105B54: 0→1f, 1→6m, 2→15m (0x80105B5E = 0) / 40m, 3→18m, 4→80f; 1→82f; 82→80f (0x80105B62 = 0) or
ending; 80→2m (0x80105B60 = 0) or save (mode 6) → 82; 2,3,4,7-13,16,20,22,23,30,31,41→n+1 m; 5→81f (B54=1);
6→7m (0x80105B5C = 0) / 30m; 14→81f (B54=2); 15→41m; 17→85m; 18→13f entry 1; 19→84f; 21→50m; 24→80 mode 5;
32→10m; 40→16m; 42→85m; 50→22m; 84→20f (0x80105B56 = 1) / 21m (= 2); 85→81f (B54=3). **guess** in detail (read
from code, only the 86→81→1 start observed).

## Story flags (u16, all guesses from the switch above)

0x80105B54 chapter counter for the classroom (MAP81) visits; 0x80105B56 MAP84 branch; 0x80105B5C MAP06 branch;
0x80105B5E MAP81 chapter-2 branch; 0x80105B60 / 0x80105B62 MAP80 / MAP82 ending steps. Event scripts read
variables by index (opcode-0x04/05 handler 0x8005DE0C); not yet mapped to these addresses.

## Units (battle)

Unit records at 0x800B3778, 0x50 bytes each: +0 x, +1 y, +2 side (1 player, 6 enemy), +8 u16 HP, +0xA u16 max HP.
Units 0-6 are the party (Ann = unit 0), enemies follow. **verified**: HP 80 / 43 match the battle screen; setting
unit 0 HP to 1 before the first MAP02 fight gives the game over (scene `gameover`). warp.lua `GOD=1` pins 0-6.
