-- Probe: log every string the text engine prints (typewriter runs and instant print 0x8003B288(window, string)),
-- with its window geometry and pen position, for measuring menu/label budgets (tools/debug/fieldscan.py).
-- emu.py ... --debugger --script tools/debug/warp.lua --script tools/debug/fieldlog.lua
-- Window i at 0x800AD89C + 0x1C*i: +0 x, +2 y, +4 width px, +6 height px, +8 W, +A lines, +C pen x, +E pen y.
-- Log line: "STR f<frame> <run|put> ptr <addr> win i x y wpx hpx W lines penx peny hex <bytes up to the 0>". Each distinct
-- (source, window, geometry, pen, text) is logged once.
local ffi = require("ffi")
local mem = PCSX.getMemPtr()
local function u8(a) return ffi.cast("uint8_t*", mem + a % 0x200000)[0] end
local function u32(a) return ffi.cast("uint32_t*", mem + a % 0x200000)[0] end
local function s16(a) return ffi.cast("int16_t*", mem + a % 0x200000)[0] end
local seen = {}
local function dump(kind, w, p)
  if w < 0 or w > 7 or p < 0x80000000 or p >= 0x80200000 then return end
  local b = 0x800AD89C + 0x1C * w
  local hex = {}
  for i = 0, 199 do
    local c = u8(p + i)
    if c == 0 then break end
    hex[#hex + 1] = string.format("%02X", c)
  end
  local s = string.format("%s ptr %08X win %d x %d y %d wpx %d hpx %d W %d lines %d penx %d peny %d hex %s", kind, p, w,
    s16(b), s16(b + 2), s16(b + 4), s16(b + 6), s16(b + 8), s16(b + 10), s16(b + 12), s16(b + 14),
    table.concat(hex))
  if not seen[s] then
    seen[s] = true
    L.log(string.format("STR f%d %s", L.frame, s))
  end
end
L.on_exec(0x8003B288, function()
  local r = PCSX.getRegisters().GPR.n
  dump("put", r.a0, r.a1)
end)
local last = {}
L.on_frame(function()
  for j = 0, 7 do
    local p = u32(0x800AD934 + 16 * j)
    if p ~= last[j] then
      last[j] = p
      if p ~= 0 then dump("run", u32(0x800AD92C + 16 * j), p) end
    end
  end
end)
