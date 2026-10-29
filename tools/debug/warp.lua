-- Warp from a cold boot to a scene in tools/debug/scenes.lua (RAM map: docs/re/state.md).
--   emu.py CUE --out work/qa/warp --script tools/debug/warp.lua --var "SCENE='map13r'" --frames 20000 --sheet
--   [--state-out work/states/map13r.sstate] [--var GOD=1] [--var "DISC_TREE=[[H:/.../tree]]"]
--   [--var "EDIT_TREE=[[H:/.../work/build/files]]"] (a build: its changed files, checked before DISC_TREE)
-- No debugger needed: it polls RAM once a frame. It boots, picks NEW GAME, and when New Game queues its fade-out
-- callback (the next-map function) it sets the map / entry / mode bytes and swaps the callback for the scene's
-- loader, so the game loads the scene the way a map change does. When the scene is ready it waits `settle`
-- frames, shoots <SCENE>.png, checks the scene (map byte; MAPDAT in RAM = the expected file), saves STATE_OUT
-- and quits: exit 0 ok, 2 check failed (message in log.txt and on stderr). --frames is only a cap.
-- GOD=1 pins every player unit's HP to its max every frame. STAY=1 keeps running after the check (to --frames);
-- STAY=N runs N frames after it, then quits (tools/debug/tour.py).
local ffi = require("ffi")
local mem = PCSX.getMemPtr()
local function rd8(a) return mem[a % 0x200000] end
local function wr8(a, v) mem[a % 0x200000] = v end
local function rd16(a) return ffi.cast("uint16_t*", mem + a % 0x200000)[0] end
local function wr16(a, v) ffi.cast("uint16_t*", mem + a % 0x200000)[0] = v end
local function rd32(a) return ffi.cast("uint32_t*", mem + a % 0x200000)[0] end
local function wr32(a, v) ffi.cast("uint32_t*", mem + a % 0x200000)[0] = v end
local G = { rd8 = rd8, wr8 = wr8, rd16 = rd16, wr16 = wr16, rd32 = rd32, wr32 = wr32 }

local MAP, ENTRY, MODE = 0x80090276, 0x80090277, 0x80090B28
local FADE_CB = 0x80090C60          -- $gp+0xB74: called when the fade-out ends
local NEXT_MAP_FN = 0x8003F5B0      -- story progression: current map -> next map, then a loader
local LOADERS = { field = 0x80022780, mode = 0x800673CC }
local MAPDAT_RAM = 0x80170000
local UNITS, UNIT_SIZE = 0x800B3778, 0x50   -- unit records: +8 HP, +0xA max HP; player units 0-6
G.UNITS, G.UNIT_SIZE = UNITS, UNIT_SIZE

-- shortcut: finds the repo from an --out under <repo>/work/; pass SCENES_FILE / DISC_TREE for other --out dirs
local REPO = OUT:match("^(.-)/work/") or "."
local scenes = dofile(SCENES_FILE or (REPO .. "/tools/debug/scenes.lua"))
local sc = scenes[SCENE or ""] or error("unknown SCENE '" .. tostring(SCENE) .. "' (see tools/debug/scenes.lua)")
local TREE = DISC_TREE or (REPO .. "/work/disc/tree")
sc.settle = SETTLE or sc.settle   -- --var SETTLE=N: watch longer with --shot-every
L.log("warp scene " .. SCENE)

-- Boot: skip the logos and intro with Start; then circle through NEW GAME, the name check and the poster (all
-- defaults) until the game queues the next map.
L.press("-", 2400); L.press("start", 6); L.press("-", 600); L.press("start", 6); L.press("-", 300)

local function check()
  if sc.title then return (rd8(MAP) == 86 and rd8(MODE) == 0) or "map/mode bytes are not the title's (86, 0)" end
  if sc.map_check ~= false and rd8(MAP) ~= sc.map then return string.format("map byte %d, want %d", rd8(MAP), sc.map) end
  if sc.dir then
    -- a build's edited files (EDIT_TREE, work/build/files) shadow the unpacked tree
    local f = EDIT_TREE and io.open(EDIT_TREE .. "/MAP01_06/" .. sc.dir .. "/MAPDAT.BIN", "rb")
    f = f or io.open(TREE .. "/MAP01_06/" .. sc.dir .. "/MAPDAT.BIN", "rb")
    if not f then return "cannot open " .. TREE .. "/MAP01_06/" .. sc.dir .. "/MAPDAT.BIN" end
    local want = f:read(0x800); f:close()
    if ffi.string(mem + MAPDAT_RAM % 0x200000, #want) ~= want then return "MAPDAT in RAM is not " .. sc.dir end
  end
  if sc.check then return sc.check(G) end
  return true
end

local warped, ready_at, stay_until = false, nil, nil
local function finish(n)
  L.shot(SCENE .. ".png")
  local ok = check()
  if ok ~= true then L.fail("CHECK FAIL " .. SCENE .. ": " .. tostring(ok)); return end
  L.log(string.format("f%d CHECK ok %s", n, SCENE))
  WARP_DONE = n   -- for probes that start once the scene is reached (tourshot.lua)
  if STATE_OUT then L.save_state(STATE_OUT) end
  if STAY then ready_at = math.huge else L.finish(0) end   -- STAY=1: keep running (mash, probes) to --frames
  if STAY and STAY > 1 then stay_until = n + STAY end      -- STAY=N: N more frames, then quit
end

L.on_frame(function(n)
  if stay_until and n >= stay_until then L.finish(0); return end
  if GOD and warped then
    for i = 0, 6 do
      local u = UNITS + i * UNIT_SIZE
      if rd16(u + 10) > 0 then wr16(u + 8, rd16(u + 10)) end
    end
  end
  if sc.every and warped then sc.every(G) end
  if ready_at then
    if n >= ready_at then finish(n) end
    return
  end
  if sc.title then   -- the boot presses end on the title menu (NEW GAME sets the mode byte to 1)
    if L.route_done() then ready_at = n + (sc.settle or 300) end
    return
  end
  if not warped then
    if L.route_done() and n % 40 == 0 then L.press("circle", 6) end
    if rd32(FADE_CB) == NEXT_MAP_FN then
      if sc.pre then sc.pre(G) end
      wr8(MAP, sc.map)
      wr8(ENTRY, sc.entry or 0)
      if sc.mode then wr8(MODE, sc.mode) end
      wr32(FADE_CB, LOADERS[sc.loader or "field"])
      warped = true
      L.log(string.format("f%d warped: map %d entry %d", n, sc.map, sc.entry or 0))
      for _, s in ipairs(sc.after or {}) do L.press(s[2], s[1]) end
    end
    return
  end
  -- warped: wait for the scene's own ready condition
  if sc.mash_until then
    if rd32(FADE_CB) == sc.mash_until then
      sc.mash_until = nil
      L.log(string.format("f%d callback %08X seen", n, rd32(FADE_CB)))
      for _, s in ipairs(sc.then_after or {}) do L.press(s[2], s[1]) end
      if sc.on_seen then sc.on_seen(G) end
    elseif L.route_done() and n % 40 == 0 then L.press("circle", 6) end
    return
  end
  if L.route_done() then ready_at = n + (sc.settle or 900) end
end)
