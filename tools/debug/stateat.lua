-- Save a state (and a shot) the first time instant print 0x8003B288 draws the string at AT (RAM address), then end
-- the run: a start point for menu routes (emu.py --state-in).
--   emu.py CUE --out D --debugger --script tools/debug/warp.lua --var "SCENE='battle'" --script tools/debug/stateat.lua
--          --var AT=0x800103E8 --var "STATE=[[C:/.../work/states/cmd.sstate]]" [--var DELAY=30]
-- EXE row id -> address: 0x80010000 + offset - 0x800 (EXE/00BE8 = 0x800103E8). DELAY frames after the print.
local at, state, delay = assert(AT, "set --var AT=0x8001...."), assert(STATE, "set --var STATE=[[path]]"), DELAY or 30
local hit
L.on_exec(0x8003B288, function()
  if not hit and PCSX.getRegisters().GPR.n.a1 == at then hit = L.frame end
end)
L.on_frame(function(n)
  if hit and n == hit + delay then
    L.save_state(state)
    L.shot("stateat.png")
    L.log(string.format("f%d state saved at print of %08X (f%d)", n, at, hit))
    L.finish(0)
  end
end)
