-- Scene list for tools/debug/warp.lua (RAM map: docs/re/state.md). regen.py reads the names after `return {`
-- with a regex (`name = {` or `name = wm(`), so keep that form. Fields:
--   map      0x80090276, the map number (MAPnn = nn)
--   entry    0x80090277, which CD_SYS file set of the map loads (MAP01: 0 = MAP01R, 1 = MAP01), default 0
--   dir      expected MAPnn folder: warp.lua checks MAPDAT in RAM against it
--   loader   "field" (0x80022780, default) or "mode" (0x800673CC: screen picked by `mode`)
--   mode     0x80090B28 for the mode loader: 1 birthday entry (new game), 2 load, 3 between-stage menu,
--            4 ending + credits, 5 cutscene after MAP24, 6 save
--   after    route steps {{frames, "buttons"}, ...} pressed once the warp is applied (load time included)
--   mash_until  after the warp, press circle every 40 frames until the fade callback equals this value, then
--            press `then_after` and run on_seen(G)
--   settle   frames from ready to the shot (default 900; 300 for the title)
--   map_check  false: skip the map-byte check (screens that rewrite it)
--   pre / every / check  fn(G): writes before the load / every frame after it / extra check (true or a message)
--   title    true: no warp, stop on the title screen
local BATTLE = 0x80059948   -- fade callback that starts a battle (two units engage)
local DOWN = { 6, "down" }
local W = { 20, "-" }
local OK = { 6, "circle" }
local function menu(...)    -- between-stage menu, wait for it, then the given steps
  local t = { { 700, "-" } }
  for _, s in ipairs({ ... }) do t[#t + 1] = s end
  return t
end
local START = menu(DOWN, W, DOWN, W, DOWN, W, OK, { 60, "-" })   -- 4th item スタート: world map, then the stage
local function wm(n) return { map = n, loader = "mode", mode = 3, after = START, settle = 200 } end

return {
  title = { title = true },
  birthday = { map = 86, loader = "mode", mode = 1 },
  load = { map = 86, loader = "mode", mode = 2 },
  menu = { map = 2, loader = "mode", mode = 3 },
  club_select = { map = 2, loader = "mode", mode = 3, after = menu(OK, { 300, "-" }) },
  dressup = { map = 2, loader = "mode", mode = 3, after = menu(DOWN, W, OK, { 300, "-" }) },
  save = { map = 2, loader = "mode", mode = 3, after = menu(DOWN, W, DOWN, W, OK, { 300, "-" }) },
  save_after_m80 = { map = 82, loader = "mode", mode = 6, map_check = false },   -- the save screen rewrites the map byte
  cutscene_m24 = { map = 80, loader = "mode", mode = 5, settle = 1500 },
  credits = { map = 82, loader = "mode", mode = 4, settle = 1800 },
  battle = { map = 2, mash_until = BATTLE, settle = 1500 },   -- no dir: battle data loads over MAPDAT
  gameover = { map = 2, dir = "MAP02", mash_until = BATTLE, settle = 300,
               on_seen = function(G) G.wr16(G.UNITS + 8, 1) end,   -- Ann (unit 0) to 1 HP; the enemy attacks first
               then_after = { { 1500, "-" }, { 8, "right" }, { 60, "-" }, OK, { 1300, "-" }, OK, { 100, "-" }, OK,
                              { 100, "-" }, OK, { 100, "-" }, OK, { 300, "-" } } },
  -- world map with each area card: Start from the menu on a map listed at 0x8008D178
  wm06 = wm(6), wm07 = wm(7), wm08 = wm(8), wm09 = wm(9), wm10 = wm(10), wm11 = wm(11), wm12 = wm(12),
  wm13 = wm(13), wm14 = wm(14), wm15 = wm(15), wm16 = wm(16), wm17 = wm(17), wm18 = wm(18), wm19 = wm(19),
  wm21 = wm(21), wm22 = wm(22), wm23 = wm(23), wm24 = wm(24), wm30 = wm(30), wm31 = wm(31), wm32 = wm(32),
  wm40 = wm(40), wm41 = wm(41), wm42 = wm(42), wm50 = wm(50),
  -- every MAPnn folder, loaded as a field map (its first event plays)
  map01r = { map = 1, entry = 0, dir = "MAP01R" },
  map01 = { map = 1, entry = 1, dir = "MAP01" },
  map02 = { map = 2, dir = "MAP02" },
  map03 = { map = 3, dir = "MAP03" },
  map03r = { map = 3, entry = 1, dir = "MAP03R" },
  map04 = { map = 4, dir = "MAP04" },
  map05 = { map = 5, dir = "MAP05" },
  map06 = { map = 6, dir = "MAP06" },
  map07 = { map = 7, dir = "MAP07" },
  map08 = { map = 8, dir = "MAP08" },
  map09 = { map = 9, dir = "MAP09" },
  map10 = { map = 10, dir = "MAP10" },
  map11 = { map = 11, dir = "MAP11" },
  map12 = { map = 12, dir = "MAP12" },
  map12r = { map = 12, entry = 1, dir = "MAP12R" },
  map13 = { map = 13, dir = "MAP13" },
  map13r = { map = 13, entry = 1, dir = "MAP13R" },
  map14r = { map = 14, entry = 0, dir = "MAP14R" },
  map14 = { map = 14, entry = 1, dir = "MAP14" },
  map15 = { map = 15, dir = "MAP15" },
  map16 = { map = 16, dir = "MAP16" },
  map17 = { map = 17, dir = "MAP17" },
  map17r = { map = 17, entry = 1, dir = "MAP17R" },
  map18 = { map = 18, dir = "MAP18" },
  map19 = { map = 19, dir = "MAP19" },
  map20 = { map = 20, dir = "MAP20" },
  map21 = { map = 21, dir = "MAP21" },
  map22 = { map = 22, dir = "MAP22" },
  map23 = { map = 23, dir = "MAP23" },
  map24 = { map = 24, dir = "MAP24" },
  map30 = { map = 30, dir = "MAP30" },
  map31 = { map = 31, dir = "MAP31" },
  map31r = { map = 31, entry = 1, dir = "MAP31R" },
  map32 = { map = 32, dir = "MAP32" },
  map40 = { map = 40, dir = "MAP40" },
  map41 = { map = 41, dir = "MAP41" },
  map42 = { map = 42, dir = "MAP42" },
  map42r = { map = 42, entry = 1, dir = "MAP42R" },
  map50 = { map = 50, dir = "MAP50" },
  map80 = { map = 80, dir = "MAP80" },
  map81 = { map = 81, dir = "MAP81" },
  map82 = { map = 82, dir = "MAP82" },
  map83 = { map = 83, dir = "MAP83" },
  map84 = { map = 84, dir = "MAP84" },
  map85 = { map = 85, dir = "MAP85" },
  map86 = { map = 86, dir = "MAP86" },
}
