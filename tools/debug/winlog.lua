-- Probe: log each message the text engine starts, with its window's geometry (docs/re/vwf.md §Windows).
-- emu.py ... --script tools/debug/warp.lua --script tools/debug/winlog.lua
-- Text runs: 0x800AD934 + 16*j = string pointer (0 = idle), 0x800AD92C + 16*j = window index.
-- Window i at 0x800AD89C + 0x1C*i: +0 x, +2 y, +4 width px, +6 height px, +8 width in 8-px units (wrap limit),
-- +A lines, +1A active. Log line: "MSG f<frame> run j ptr <addr> win i x y wpx hpx W lines".
local ffi = require("ffi")
local mem = PCSX.getMemPtr()
local function u32(a) return ffi.cast("uint32_t*", mem + a % 0x200000)[0] end
local function s16(a) return ffi.cast("int16_t*", mem + a % 0x200000)[0] end
local last = {}
L.on_frame(function(n)
  for j = 0, 7 do
    local p = u32(0x800AD934 + 16 * j)
    if p ~= last[j] then
      last[j] = p
      if p ~= 0 then
        local w = u32(0x800AD92C + 16 * j)
        local b = 0x800AD89C + 0x1C * (w % 16)
        L.log(string.format("MSG f%d run %d ptr %08X win %d x %d y %d wpx %d hpx %d W %d lines %d", n, j, p, w,
          s16(b), s16(b + 2), s16(b + 4), s16(b + 6), s16(b + 8), s16(b + 10)))
      end
    end
  end
end)
