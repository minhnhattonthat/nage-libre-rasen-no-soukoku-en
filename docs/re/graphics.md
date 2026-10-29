# Graphics text survey

Japanese drawn as images (TIM textures), not by the text renderer. Built in phase 1 from a **static sweep** of the
whole disc:

- raw TIMs: `python tools/tim.py render work/disc/tree work/gfx/tim` (598 TIMs, 378 unique; `index.tsv` lists every
  copy as `dup`);
- packed TIMs: `cd tools && python sweep_packed.py ../work/disc/tree ../work/gfx/packed` (228 unique; prints every
  skipped file/entry with the reason: scripts/sound/map data files, palette-only `0x11` blocks, 4116-byte tables, face
  pixel blocks);
- sheets: `sheet.py "work/gfx/tim/*.png" --cols 6 --max 24 --div 1`, all 16 + 8 pages read.

Not yet covered: images not stored as TIMs (raw pixel blocks such as faces, map tile blocks in MAPDAT) and text drawn
from the font into screens. The phase-5 marker tour (every screen whose Japanese doesn't turn into markers) closes that
gap; add rows here then.

**Copies:** shared textures are duplicated in many files (e.g. the battle "参上" sheet sits in 34 BTLTIM files, the
TIME GAUGE/"参上" sheet in 46 MAPTIM files). Every edit must be written to every copy listed as `dup` in
`work/gfx/tim/index.tsv`.

| # | Element | Source (first copy) | Format | Copies | Notes |
|---|---|---|---|---|---|
| 1 | Title subtitle 螺旋の相剋 under the "Nage Libre" logo | OP_TMP2.BIN 0x7034C (#10) | raw 8bpp 128x88 | 1 | logo itself is Latin |
| 2 | "スタートボタンではじまるよ！" (press start) | OP_TMP2.BIN #11 | packed 8bpp 128x256 | 1 | also © VARIE 1997 |
| 3 | "ちょっとまっててね♥" (please wait) | OP_TMP2.BIN #12 | packed | 1 | |
| 4 | Title menu: "メモリーカードチェック中" row (NEW GAME/LOAD/... are English) | OP_TMP2.BIN #13 | packed 128x128 | 1 | |
| 5 | Memory card missing notice (5 lines) | OP_TMP2.BIN #14 | packed | 1 | |
| 6 | Loading chalkboard "ロードちゅうです・・・", "月 日" | VARIE.BIN 0x10228 (#1) | raw 8bpp | 1 | shown during every load |
| 7 | New game: "誕生日をきめてね", "これでいいですか？" (YES/NO are English) | OPTION1.BIN 0x10298 | raw 8bpp | 1 | birthday entry |
| 8 | Birthstone names (ガーネット ... ラピスラズリ, 12) | OPTION1.BIN 0x204B8 | raw 8bpp | 1 | |
| 9 | "どのデータではじめる？" (load) | OPTION3.BIN 0x10298 | raw 8bpp | 1 | |
| 10 | "保存する場所をおしえて？" (save) | OPTION3.BIN 0x206CC | raw 8bpp | 1 | |
| 11 | Save-slot chapter titles (~33 lines, e.g. "営業停止寸前！南寿町商店街！！") | OPTION3.BIN 0x308EC, 0x38B0C, 0x4052C | raw 8bpp 64x256, 64x240, 128x256 | 1 each | small pixel font |
| 12 | Between-stage menu "これから なにする？", 部活セレクト / 着せかえ / セーブ / スタート | OPTION4.BIN 0x10298 | raw 8bpp | 1 | |
| 13 | Dress-up item name lists (clothes, shoes, accessories, ~150 names) | OPTION2.BIN #1-#4 | packed 8bpp 128x256 | 1 each | half-width katakana pixel font |
| 14 | Area name cards (25): 密林, 南の海, 遺跡の孤島, 地底洞窟, 城塞内部, 城塞司令室, 二叉岬, 戦艦の眠る砂丘, 霧に包まれた森, カスケードの滝, 古代遺跡, 溶岩洞窟, 紅葉の谷, 飛行戦艦内部, 飛行戦艦ドック, 桜花高校指令塔, ナージュの祭壇, 指令塔屋上, 氷雪山, 温泉郷, 城壁, 巨木の森, 一寸岳, 火山洞窟, 連絡橋 | OPTION7.BIN 0x3D6A0 ... 0x57B00 | raw 8bpp 64x40 each | 1 each | world map; text over party sprites |
| 15 | Ending "おわり" | OPTION6.BIN 0x329C8 | raw 16bpp 256x201 | 1 | over artwork |
| 16 | Cast name plates (10): 赤木 杏, 森野 樹, 松永 真, 筑紫 澪, 風間 忍, 神崎 薫, 桐生 迅, 輪島 大, 相田 司, 黒沢 亮 | OPTION6.BIN #2-#11 | packed 8bpp 40x96 | 1 each | credits; "CAST" is English |
| 17 | Credit artwork sign (生徒会室-style plate in the picture) | OPTION6.BIN #15 (p0219) | packed 92x128 | 1 | background detail; decide in phase 8 |
| 18 | Battle boss intro "参上" (vertical, with VS) | MAP01R/BTLTIM.BIN 0x18A78 | raw 8bpp | 34 | |
| 19 | Boss intro "レイプマン 参上" + TIME GAUGE (English) | MAP01R/MAPTIM.BIN 0x33AE8 | raw 8bpp | 46 | name reads レイプマン in the art |
| 20 | News ticker, 7 lines "※南寿町を中心に..." | MAP01R/MAPTIM.BIN 0x10244 | raw 8bpp | 2 | |
| 21 | Town sign 駐車場 (parking) | MAP01R/MAPFIRST.BIN 0x1FC | raw 8bpp | 2 | small map sign |
| 22 | Town sign 魚政 (fish shop) | MAP01R/MAPFIRST.BIN 0x1041C | raw 8bpp | 2 | |
| 23 | Town shop signs 毎朝新聞社, 八百屋, くすりキヨシ, 南寿町商店街 arch, JA南寿 | MAP01R/MAPFIRST.BIN 0x2063C | raw 8bpp | 2 | several signs on one sheet |
| 24 | Amusement park sign コビーロレース | MAP03R/MAPFIRST.BIN 0x2046C | raw 8bpp | 2 | "BEAT CATS" is English |
| 25 | Student council desk plate 会長 | MAP80/MAPFIRST.BIN 0x44 | raw 8bpp | 1 | |
| 26 | Classroom blackboard "今月の目標 めざせ町の平和" | MAP81/MAPFIRST.BIN 0x10298 | raw 8bpp | 1 | |
| 27 | Shrine notice board 南寿神社のゆらい | MAP82/MAPFIRST.BIN 0xC8 | raw 8bpp | 1 | |
| 28 | Recruitment poster "ナージュ像捜索団員 大募集" (11 lines) | MAP86/MAPFIRST.BIN 0xF8 | raw 8bpp 128x224 | 1 | full-screen readable poster |

Checked and English already (no work): "game over", NEW GAME/LOAD/CONTINUE/SOUND menu, Ann/Ituki/Makoto/Sinobu/Mio
name buttons, TOPS/BOTTOMS/SHOES/ACCESSORY, EXP, TIME GAUGE, "DATE SPOT", "BEAT CATS", "presented by VARIE".
